"""Reciprocal Rank Fusion (Cormack, Clarke and Büttcher, SIGIR 2009).

Cosine similarities and ``ts_rank_cd`` values live on unrelated scales, so they are not added.
RRF uses only positions: ``score(d) = Σ 1 / (k + rank_i(d))`` over the lists that contain ``d``.
A passage found by both retrievers beats one found by a single retriever at a similar position.
"""

from collections.abc import Callable, Hashable, Sequence

RRF_K = 60


def reciprocal_rank_fusion[T](
    rankings: Sequence[Sequence[T]], *, key: Callable[[T], Hashable], k: int = RRF_K
) -> list[tuple[T, float]]:
    """Fuse ranked lists (best first). Ties keep the order of first appearance."""
    scores: dict[Hashable, float] = {}
    items: dict[Hashable, T] = {}
    for ranking in rankings:
        for position, item in enumerate(ranking, start=1):
            item_key = key(item)
            items.setdefault(item_key, item)
            scores[item_key] = scores.get(item_key, 0.0) + 1.0 / (k + position)
    order = sorted(scores, key=lambda item_key: -scores[item_key])  # stable
    return [(items[item_key], scores[item_key]) for item_key in order]
