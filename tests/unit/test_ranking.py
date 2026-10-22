from dataclasses import dataclass

from app.retrieval.ranking import Scored, select_passages


@dataclass(frozen=True)
class Chunk:
    name: str
    token_count: int = 100


def scored(chunk: Chunk, score: float) -> Scored[Chunk]:
    return Scored(chunk, score, chunk.token_count)


def names(selected: list[Scored[Chunk]]) -> list[str]:
    return [s.item.name for s in selected]


def test_relevance_alone_decides_the_order() -> None:
    """The two examples from #4: upload time no longer matters."""
    old_but_relevant = scored(Chunk("uploaded a year ago"), score=0.85)
    new_but_weak = scored(Chunk("uploaded today"), score=0.63)

    selected = select_passages(
        [new_but_weak, old_but_relevant], top_k=5, max_tokens=4000, min_score=0.7
    )

    # Before: 0.8*0.85 + 0.2*0 = 0.68 was dropped, 0.8*0.63 + 0.2*1 = 0.704 passed.
    assert names(selected) == ["uploaded a year ago"]


def test_threshold_applies_to_the_raw_similarity() -> None:
    candidates = [scored(Chunk("a"), 0.31), scored(Chunk("b"), 0.29)]
    assert names(select_passages(candidates, top_k=5, max_tokens=4000, min_score=0.3)) == ["a"]


def test_top_k_limits_the_result() -> None:
    candidates = [scored(Chunk(str(i)), score=i / 10) for i in range(10)]
    assert names(select_passages(candidates, top_k=3, max_tokens=4000, min_score=0.0)) == [
        "9",
        "8",
        "7",
    ]


def test_a_passage_that_does_not_fit_is_skipped_not_the_end() -> None:
    candidates = [
        scored(Chunk("big", token_count=900), 0.9),
        scored(Chunk("too big now", token_count=600), 0.8),
        scored(Chunk("small", token_count=50), 0.7),
    ]
    selected = select_passages(candidates, top_k=5, max_tokens=1000, min_score=0.0)
    assert names(selected) == ["big", "small"]


def test_nothing_above_the_threshold_returns_nothing() -> None:
    assert select_passages([scored(Chunk("x"), 0.1)], top_k=5, max_tokens=10, min_score=0.5) == []
