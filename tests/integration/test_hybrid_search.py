import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import DocChunk, Document, DocumentStatus
from app.retrieval.lexical import lexical_search
from app.retrieval.retriever import RetrievalMode, retrieve
from tests.fakes import HashEmbeddings

FILLER = [
    "Generic typing features let functions accept many kinds of values.",
    "Type hints describe the shape of data passed between functions.",
    "Variadic arguments collect any number of positional values.",
    "Annotations are stored on the function and read by type checkers.",
]


class RandomQueryEmbeddings(HashEmbeddings):
    """Queries land on a random vector: dense search cannot find the right chunk."""

    def embed_query(self, text: str) -> list[float]:
        return np.random.default_rng(0).normal(size=self.dim).tolist()


def _seed(db: Session) -> int:
    rng = np.random.default_rng(3)
    doc = Document(filename="pep-646.txt", path="/data/pep-646", status=DocumentStatus.READY)
    db.add(doc)
    db.flush()
    target_id = 0
    for i in range(40):
        text = FILLER[i % len(FILLER)]
        if i == 17:
            text = "PEP 646 introduces TypeVarTuple to parameterize generics with many types."
        chunk = DocChunk(
            document_id=doc.id,
            chunk_index=i,
            text=text,
            token_count=20,
            embedding=rng.normal(size=settings.embedding_dim),
        )
        db.add(chunk)
        db.flush()
        if i == 17:
            target_id = chunk.id
    db.commit()
    return target_id


def test_lexical_search_finds_an_exact_identifier(db: Session) -> None:
    target = _seed(db)
    hits = lexical_search(db, "What is TypeVarTuple?", k=5)
    assert hits[0].chunk_id == target
    assert len(hits) == 1  # no other chunk contains the word


def test_hybrid_recovers_what_dense_search_misses(db: Session) -> None:
    target = _seed(db)
    embeddings = RandomQueryEmbeddings()

    dense = retrieve(db, "TypeVarTuple", mode=RetrievalMode.DENSE, k=5, embeddings=embeddings)
    hybrid = retrieve(db, "TypeVarTuple", mode=RetrievalMode.HYBRID, k=5, embeddings=embeddings)

    assert target not in [c.hit.chunk_id for c in dense.candidates]
    hybrid_ids = [c.hit.chunk_id for c in hybrid.candidates]
    assert target in hybrid_ids[:2]
    found = next(c for c in hybrid.candidates if c.hit.chunk_id == target)
    assert found.lexical_score is not None
    assert hybrid.best_dense_score == dense.best_dense_score


def test_lexical_mode_has_no_dense_evidence(db: Session) -> None:
    _seed(db)
    result = retrieve(
        db, "TypeVarTuple", mode=RetrievalMode.LEXICAL, k=5, embeddings=HashEmbeddings()
    )
    assert result.best_dense_score is None
    assert all(c.dense_score is None for c in result.candidates)


def test_spanish_text_is_searchable(db: Session) -> None:
    doc = Document(filename="notas.txt", path="/data/notas", status=DocumentStatus.READY)
    db.add(doc)
    db.flush()
    db.add(
        DocChunk(
            document_id=doc.id,
            chunk_index=0,
            text="La corrutina se declara con async def y se espera con await.",
            token_count=15,
            embedding=[0.1] * settings.embedding_dim,
        )
    )
    db.commit()
    assert lexical_search(db, "¿Qué es una corrutina?", k=3)[0].filename == "notas.txt"
