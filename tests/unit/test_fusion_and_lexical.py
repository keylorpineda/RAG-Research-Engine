import pytest

from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.lexical import to_tsquery_text


def fuse(*rankings: list[str]) -> list[tuple[str, float]]:
    return reciprocal_rank_fusion(list(rankings), key=lambda x: x)


def test_rrf_scores_follow_the_formula() -> None:
    fused = dict(fuse(["a", "b"], ["b", "c"]))
    assert fused["a"] == pytest.approx(1 / 61)
    assert fused["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert fused["c"] == pytest.approx(1 / 62)


def test_found_by_both_beats_first_place_in_one() -> None:
    order = [item for item, _ in fuse(["a", "x", "y"], ["z", "x", "w"])]
    assert order[0] == "x"


def test_ties_keep_first_appearance_order() -> None:
    order = [item for item, _ in fuse(["a"], ["b"])]
    assert order == ["a", "b"]


def test_empty_lists_fuse_to_nothing() -> None:
    assert fuse([], []) == []


def test_question_words_are_dropped_and_terms_or_ed() -> None:
    assert to_tsquery_text("What does PEP 572 say about the walrus operator?") == (
        "pep | 572 | say | walrus | operator"
    )


def test_spanish_function_words_are_dropped() -> None:
    assert to_tsquery_text("¿Qué es una corrutina en Python?") == "corrutina | python"


def test_operators_and_quotes_cannot_change_the_query() -> None:
    assert to_tsquery_text("foo' | !bar & (baz) <-> :*") == "foo | bar | baz"


def test_identifiers_keep_their_underscores() -> None:
    assert to_tsquery_text("__future__ annotations") == "__future__ | annotations"


def test_only_stopwords_gives_no_query() -> None:
    assert to_tsquery_text("what is the") is None
    assert to_tsquery_text("¿?") is None
