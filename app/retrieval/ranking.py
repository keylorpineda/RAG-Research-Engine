"""Turns scored candidates into the passages sent to the language model.

Ranking uses relevance only. Upload time used to add up to 0.2 to the score, which let a weakly
related chunk uploaded today beat a highly relevant chunk uploaded last year, and made the
threshold mix two unrelated scales (#4).
"""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Scored[T]:
    item: T
    score: float
    tokens: int


def select_passages[T](
    candidates: Iterable[Scored[T]], *, top_k: int, max_tokens: int, min_score: float
) -> list[Scored[T]]:
    """Best ``top_k`` candidates scoring at least ``min_score`` that fit in ``max_tokens``.

    A passage that does not fit in the remaining budget is skipped, not treated as the end of
    the list: a shorter, slightly less relevant passage can still be used.
    """
    ranked = sorted((c for c in candidates if c.score >= min_score), key=lambda c: -c.score)
    selected: list[Scored[T]] = []
    budget = max_tokens
    for candidate in ranked:
        if len(selected) == top_k:
            break
        if candidate.tokens <= budget:
            selected.append(candidate)
            budget -= candidate.tokens
    return selected
