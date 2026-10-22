"""First-stage retrieval: dense, lexical or both fused with RRF."""

from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy.orm import Session

from app.providers.embeddings import EmbeddingProvider
from app.retrieval.dense import Hit, dense_search
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.lexical import lexical_search


class RetrievalMode(StrEnum):
    DENSE = "dense"
    LEXICAL = "lexical"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class Candidate:
    hit: Hit
    score: float  # the ordering score of the mode: cosine, ts_rank_cd or RRF
    dense_score: float | None  # cosine similarity, when the dense retriever saw this chunk
    lexical_score: float | None


@dataclass(frozen=True)
class Retrieval:
    candidates: list[Candidate]
    best_dense_score: float | None  # evidence strength, used by the abstention gate


def retrieve(
    db: Session,
    question: str,
    *,
    mode: RetrievalMode,
    k: int,
    embeddings: EmbeddingProvider,
    ef_search: int = 100,
) -> Retrieval:
    dense: list[Hit] = []
    lexical: list[Hit] = []
    if mode in (RetrievalMode.DENSE, RetrievalMode.HYBRID):
        dense = dense_search(db, embeddings.embed_query(question), k=k, ef_search=ef_search)
    if mode in (RetrievalMode.LEXICAL, RetrievalMode.HYBRID):
        lexical = lexical_search(db, question, k=k)

    dense_scores = {h.chunk_id: h.score for h in dense}
    lexical_scores = {h.chunk_id: h.score for h in lexical}

    if mode == RetrievalMode.HYBRID:
        ranked = reciprocal_rank_fusion([dense, lexical], key=lambda h: h.chunk_id)[:k]
    else:
        ranked = [(h, h.score) for h in (dense or lexical)]

    candidates = [
        Candidate(
            hit=hit,
            score=score,
            dense_score=dense_scores.get(hit.chunk_id),
            lexical_score=lexical_scores.get(hit.chunk_id),
        )
        for hit, score in ranked
    ]
    return Retrieval(candidates=candidates, best_dense_score=dense[0].score if dense else None)
