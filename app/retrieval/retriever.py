"""Retrieval: dense, lexical or both fused with RRF, optionally reranked by a cross-encoder."""

from dataclasses import dataclass, replace
from enum import StrEnum

from sqlalchemy.orm import Session

from app.providers.embeddings import EmbeddingProvider
from app.providers.rerank import Reranker
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
    score: float  # the ordering score: cosine, ts_rank_cd, RRF or rerank relevance
    dense_score: float | None  # cosine similarity, when the dense retriever saw this chunk
    lexical_score: float | None
    rerank_score: float | None = None


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
    reranker: Reranker | None = None,
    rerank_candidates: int = 30,
    lexical_query: str | None = None,
) -> Retrieval:
    """Up to ``k`` candidates, best first.

    ``lexical_query`` replaces the question for full-text search only (a translation); dense
    search and the reranker always see the original question.

    With a ``reranker``, the first stage gathers ``max(k, rerank_candidates)`` chunks and the
    reranker picks and orders the final ``k``.
    """
    first_stage_k = max(k, rerank_candidates) if reranker else k
    dense: list[Hit] = []
    lexical: list[Hit] = []
    if mode in (RetrievalMode.DENSE, RetrievalMode.HYBRID):
        dense = dense_search(
            db, embeddings.embed_query(question), k=first_stage_k, ef_search=ef_search
        )
    if mode in (RetrievalMode.LEXICAL, RetrievalMode.HYBRID):
        lexical = lexical_search(db, lexical_query or question, k=first_stage_k)

    dense_scores = {h.chunk_id: h.score for h in dense}
    lexical_scores = {h.chunk_id: h.score for h in lexical}

    if mode == RetrievalMode.HYBRID:
        ranked = reciprocal_rank_fusion([dense, lexical], key=lambda h: h.chunk_id)[:first_stage_k]
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
    if reranker and candidates:
        order = reranker.rerank(question, [c.hit.text for c in candidates], top_n=k)
        candidates = [
            replace(candidates[r.index], score=r.score, rerank_score=r.score) for r in order
        ]
    return Retrieval(candidates=candidates[:k], best_dense_score=dense[0].score if dense else None)
