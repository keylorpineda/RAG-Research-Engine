from pathlib import Path

import numpy as np
import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import DocChunk, Document, DocumentStatus
from app.retrieval.dense import dense_search
from app.services import ingestion
from tests.fakes import HashEmbeddings


def _seed(db: Session, rng: np.random.Generator, n_per_doc: int = 100) -> dict[int, np.ndarray]:
    """Three documents; the third is still PENDING and must never be returned."""
    vectors: dict[int, np.ndarray] = {}
    statuses = [DocumentStatus.READY, DocumentStatus.READY, DocumentStatus.PENDING]
    for d, status in enumerate(statuses):
        doc = Document(filename=f"doc{d}.txt", path=f"/data/doc{d}", status=status)
        db.add(doc)
        db.flush()
        for i in range(n_per_doc):
            v = rng.normal(size=settings.embedding_dim)
            chunk = DocChunk(
                document_id=doc.id, chunk_index=i, text=f"d{d} c{i}", token_count=10, embedding=v
            )
            db.add(chunk)
            db.flush()
            if status == DocumentStatus.READY:
                vectors[chunk.id] = v
    db.commit()
    return vectors


def test_matches_exact_cosine_order(db: Session) -> None:
    rng = np.random.default_rng(7)
    vectors = _seed(db, rng)
    query = rng.normal(size=settings.embedding_dim)

    hits = dense_search(db, query.tolist(), k=10, ef_search=200)

    ids = np.array(list(vectors))
    matrix = np.stack(list(vectors.values()))
    cosine = matrix @ query / (np.linalg.norm(matrix, axis=1) * np.linalg.norm(query))
    expected = ids[np.argsort(-cosine)[:10]].tolist()

    assert [h.chunk_id for h in hits] == expected
    expected_scores = sorted(cosine, reverse=True)[:10]
    assert [h.score for h in hits] == pytest.approx(expected_scores, abs=1e-5)


def test_pending_documents_are_never_returned(db: Session) -> None:
    _seed(db, np.random.default_rng(1))
    hits = dense_search(db, [1.0] * settings.embedding_dim, k=300)
    assert {h.filename for h in hits} == {"doc0.txt", "doc1.txt"}
    assert len(hits) == 200


def test_ingestion_stores_vectors_and_the_model_name(
    db: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ingestion, "get_embedding_provider", HashEmbeddings)
    source = tmp_path / "notes.txt"
    source.write_text("Coroutines use async and await.\n\nThe GIL limits threads.", "utf-8")
    doc = Document(filename="notes.txt", path=str(source), status=DocumentStatus.PENDING)
    db.add(doc)
    db.commit()

    ingestion._ingest_document(db, doc)

    db.refresh(doc)
    assert doc.status == DocumentStatus.READY
    assert doc.embedding_model == settings.embedding_model
    assert len(doc.chunks) == 1
    assert doc.chunks[0].embedding is not None

    query = HashEmbeddings().embed_query("async await coroutines")
    assert dense_search(db, query, k=1)[0].filename == "notes.txt"
