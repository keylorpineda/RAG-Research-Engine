import math

import pytest

from eval.run import percentile, ranking_metrics


def test_first_relevant_at_rank_three() -> None:
    m = ranking_metrics([10, 11, 12, 13], {12}, ["a", "b", "c", "d"], "c")
    assert m["recall@1"] == 0.0
    assert m["recall@5"] == 1.0
    assert m["mrr@10"] == pytest.approx(1 / 3)
    assert m["ndcg@10"] == pytest.approx((1 / math.log2(4)) / 1.0)
    assert m["doc_recall@5"] == 1.0


def test_nothing_relevant_scores_zero() -> None:
    m = ranking_metrics([1, 2, 3], {99}, ["a", "a", "a"], "z")
    assert m == {
        "recall@1": 0.0,
        "recall@5": 0.0,
        "recall@10": 0.0,
        "mrr@10": 0.0,
        "ndcg@10": 0.0,
        "doc_recall@5": 0.0,
    }


def test_ndcg_is_one_when_all_relevant_chunks_lead() -> None:
    m = ranking_metrics([5, 6, 7], {5, 6}, ["d", "d", "x"], "d")
    assert m["ndcg@10"] == pytest.approx(1.0)


def test_percentile_uses_nearest_rank() -> None:
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.0
    assert percentile(list(map(float, range(1, 101))), 0.95) == 95.0
