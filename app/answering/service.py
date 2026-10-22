"""Question answering: retrieve, decide whether there is enough evidence, answer with citations.

The decision to abstain is made from retrieval scores **before** the language model is called.
A prompt instruction ("say you don't know") is a request; a threshold on the evidence is a rule,
and it can be calibrated and measured (see ``eval/``).
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from sqlalchemy.orm import Session

from app.answering.citations import check_citations
from app.answering.prompt import NO_ANSWER, SYSTEM_PROMPT, build_user_prompt
from app.models.models import QueryLog
from app.providers.embeddings import EmbeddingProvider
from app.providers.llm import LLMProvider
from app.providers.rerank import Reranker
from app.retrieval.ranking import Scored, select_passages
from app.retrieval.retriever import Candidate, Retrieval, RetrievalMode, retrieve

# Retrieve more than k so the token budget can skip long passages and still fill k slots.
CANDIDATE_FACTOR = 4


class AbstainReason(StrEnum):
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"  # best similarity below the threshold
    NO_PASSAGES = "no_passages"  # nothing retrieved at all
    MODEL_DECLINED = "model_declined"  # the model read the passages and found no answer


@dataclass(frozen=True)
class AnswerOptions:
    mode: RetrievalMode = RetrievalMode.HYBRID
    k: int = 5
    max_context_tokens: int = 4000
    min_similarity: float = 0.35
    ef_search: int = 100
    rerank_candidates: int = 30


@dataclass
class Answer:
    answered: bool
    text: str | None
    reason: AbstainReason | None
    passages: list[Candidate] = field(default_factory=list)  # passage n is passages[n - 1]
    cited: list[int] = field(default_factory=list)
    invalid_citations: list[int] = field(default_factory=list)
    best_similarity: float | None = None


def has_enough_evidence(retrieval: Retrieval, min_similarity: float) -> bool:
    """The gate. Dense evidence is required when it exists; lexical-only needs at least one hit."""
    if retrieval.best_dense_score is not None:
        return retrieval.best_dense_score >= min_similarity
    return bool(retrieval.candidates)


def answer_question(
    db: Session,
    question: str,
    options: AnswerOptions,
    *,
    embeddings: EmbeddingProvider,
    llm: LLMProvider | Callable[[], LLMProvider],
    reranker: Reranker | None = None,
) -> Answer:
    retrieval = retrieve(
        db,
        question,
        mode=options.mode,
        k=options.k * CANDIDATE_FACTOR,
        embeddings=embeddings,
        ef_search=options.ef_search,
        reranker=reranker,
        rerank_candidates=options.rerank_candidates,
    )
    best = retrieval.best_dense_score
    if not retrieval.candidates:
        return _log(
            db, question, Answer(False, None, AbstainReason.NO_PASSAGES, best_similarity=best)
        )
    if not has_enough_evidence(retrieval, options.min_similarity):
        return _log(
            db,
            question,
            Answer(False, None, AbstainReason.INSUFFICIENT_EVIDENCE, best_similarity=best),
        )

    passages = [
        s.item
        for s in select_passages(
            (Scored(c, c.score, c.hit.token_count) for c in retrieval.candidates),
            top_k=options.k,
            max_tokens=options.max_context_tokens,
            min_score=float("-inf"),
        )
    ]
    # Resolved only here: abstentions need no language model (nor its API key).
    model = llm if isinstance(llm, LLMProvider) else llm()
    raw = model.complete(SYSTEM_PROMPT, build_user_prompt(question, [p.hit for p in passages]))
    if not raw or raw.strip().strip(".").upper() == NO_ANSWER:
        return _log(
            db,
            question,
            Answer(
                False, None, AbstainReason.MODEL_DECLINED, passages=passages, best_similarity=best
            ),
        )

    checked = check_citations(raw, len(passages))
    return _log(
        db,
        question,
        Answer(
            answered=True,
            text=checked.text,
            reason=None,
            passages=passages,
            cited=checked.cited,
            invalid_citations=checked.invalid,
            best_similarity=best,
        ),
    )


def _log(db: Session, question: str, answer: Answer) -> Answer:
    db.add(
        QueryLog(
            query_text=question,
            result_refs={
                "answered": answer.answered,
                "reason": answer.reason,
                "bestSimilarity": answer.best_similarity,
                "passages": [
                    {"chunkId": p.hit.chunk_id, "score": p.score} for p in answer.passages
                ],
                "cited": answer.cited,
                "invalidCitations": answer.invalid_citations,
            },
        )
    )
    db.commit()
    return answer
