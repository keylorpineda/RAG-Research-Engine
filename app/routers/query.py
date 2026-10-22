from fastapi import APIRouter, Request

from app.answering.service import Answer, AnswerOptions, answer_question
from app.core import demo_limits
from app.core.config import settings
from app.core.errors import BadRequestError
from app.models.database import DbSession
from app.providers.embeddings import get_embedding_provider
from app.providers.llm import get_llm
from app.providers.rerank import get_reranker
from app.schemas import Evidence, QueryRequest, QueryResponse, Reference

router = APIRouter(prefix="/api", tags=["query"])

type CacheKey = tuple[str, str, int, int, float]
answer_cache: demo_limits.TtlCache[CacheKey, QueryResponse] = demo_limits.TtlCache(
    settings.answer_cache_size, settings.answer_cache_seconds
)


@router.post("/query")
def query(req: QueryRequest, request: Request, db: DbSession) -> QueryResponse:
    question = req.q.strip()
    if not question:
        raise BadRequestError("The question cannot be empty.")
    min_similarity = (
        req.min_similarity if req.min_similarity is not None else settings.abstain_threshold
    )
    key: CacheKey = (
        " ".join(question.lower().split()),
        req.mode,
        req.k,
        req.max_tokens,
        min_similarity,
    )
    cached = answer_cache.get(key)
    if cached is not None:
        return cached  # free: no provider calls, not counted against the limits
    demo_limits.check_question_allowed(db, request)

    options = AnswerOptions(
        mode=req.mode,
        k=req.k,
        max_context_tokens=req.max_tokens,
        min_similarity=min_similarity,
        ef_search=settings.hnsw_ef_search,
        rerank_candidates=settings.rerank_candidates,
    )
    answer = answer_question(
        db,
        question,
        options,
        embeddings=get_embedding_provider(),
        llm=get_llm,
        reranker=get_reranker(),
    )
    response = to_response(answer, min_similarity)
    answer_cache.put(key, response)
    return response


def to_response(answer: Answer, min_similarity: float) -> QueryResponse:
    return QueryResponse(
        answered=answer.answered,
        answer=answer.text,
        reason=answer.reason,
        refs=[
            Reference(
                n=n,
                doc_id=p.hit.document_id,
                filename=p.hit.filename,
                chunk_index=p.hit.chunk_index,
                score=round(p.score, 6),
                dense_score=None if p.dense_score is None else round(p.dense_score, 6),
                lexical_score=None if p.lexical_score is None else round(p.lexical_score, 6),
                rerank_score=None if p.rerank_score is None else round(p.rerank_score, 6),
                cited=n in answer.cited,
                text=p.hit.text,
            )
            for n, p in enumerate(answer.passages, start=1)
        ],
        invalid_citations=answer.invalid_citations,
        evidence=Evidence(best_similarity=answer.best_similarity, min_similarity=min_similarity),
    )
