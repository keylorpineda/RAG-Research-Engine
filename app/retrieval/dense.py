"""Dense retrieval inside Postgres with pgvector.

The query vector is compared in the database through the HNSW index (cosine distance), so only
the top ``k`` rows leave Postgres. The v1 engine loaded every vector as JSON and scored them in a
Python loop.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.models import DocChunk, Document, DocumentStatus


@dataclass(frozen=True)
class Hit:
    chunk_id: int
    document_id: int
    filename: str
    chunk_index: int
    text: str
    token_count: int
    score: float
    section: str | None = None


def dense_search(
    db: Session, query_vector: Sequence[float], *, k: int, ef_search: int = 100
) -> list[Hit]:
    """Top ``k`` chunks of READY documents by cosine similarity (``1 - cosine distance``).

    ``ef_search`` is the HNSW candidate list size: higher is more accurate and slower. It must be
    at least ``k`` or the index can return fewer rows than asked.
    """
    db.execute(
        text("SELECT set_config('hnsw.ef_search', :ef, true)"), {"ef": str(max(ef_search, k))}
    )
    distance = DocChunk.embedding.cosine_distance(list(query_vector))
    rows = db.execute(
        select(
            DocChunk.id,
            DocChunk.document_id,
            Document.filename,
            DocChunk.chunk_index,
            DocChunk.text,
            DocChunk.token_count,
            (1 - distance).label("score"),
            DocChunk.section,
        )
        .join(Document)
        .where(Document.status == DocumentStatus.READY, DocChunk.embedding.is_not(None))
        .order_by(distance)
        .limit(k)
    ).all()
    return [Hit(*row) for row in rows]
