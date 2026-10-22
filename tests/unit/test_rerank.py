import json
from collections.abc import Sequence

import httpx
import pytest
import respx

from app.core.config import Settings
from app.core.errors import ProviderNotConfiguredError, UpstreamError
from app.providers.rerank import COHERE_RERANK_URL, CohereReranker, Reranked, build_reranker
from app.retrieval import retriever
from app.retrieval.dense import Hit
from app.retrieval.retriever import RetrievalMode, retrieve
from tests.fakes import HashEmbeddings


def _hit(i: int, score: float) -> Hit:
    return Hit(i, 1, "doc.txt", i, f"chunk {i}", 10, score)


@pytest.fixture
def cohere() -> CohereReranker:
    return CohereReranker("test-key", client=httpx.Client(), sleep=lambda _: None)


@respx.mock
def test_cohere_rerank_request_and_order(cohere: CohereReranker) -> None:
    route = respx.post(COHERE_RERANK_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": 2, "relevance_score": 0.91},
                    {"index": 0, "relevance_score": 0.40},
                ]
            },
        )
    )

    result = cohere.rerank("question", ["a", "b", "c"], top_n=2)

    sent = json.loads(route.calls[0].request.content)
    assert sent == {
        "model": "rerank-v3.5",
        "query": "question",
        "documents": ["a", "b", "c"],
        "top_n": 2,
    }
    assert result == [Reranked(2, 0.91), Reranked(0, 0.40)]


@respx.mock
def test_out_of_range_indexes_are_rejected(cohere: CohereReranker) -> None:
    respx.post(COHERE_RERANK_URL).mock(
        return_value=httpx.Response(200, json={"results": [{"index": 9, "relevance_score": 1}]})
    )
    with pytest.raises(UpstreamError):
        cohere.rerank("q", ["only one"], top_n=1)


def test_no_documents_makes_no_call(cohere: CohereReranker) -> None:
    assert cohere.rerank("q", [], top_n=5) == []


def test_rerank_is_off_by_default_and_needs_a_key() -> None:
    assert build_reranker(Settings()) is None
    with pytest.raises(ProviderNotConfiguredError):
        build_reranker(Settings(rerank_provider="cohere", cohere_api_key="changeme"))


class ReverseReranker:
    name = "fake:reverse"

    def __init__(self) -> None:
        self.seen: list[str] = []

    def rerank(self, query: str, documents: Sequence[str], top_n: int) -> list[Reranked]:
        self.seen = list(documents)
        n = len(documents)
        return [Reranked(n - 1 - i, 1.0 - i / 10) for i in range(min(top_n, n))]


def test_retrieve_widens_the_first_stage_and_lets_the_reranker_choose(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asked: list[int] = []

    def fake_dense(_db: object, _vector: object, *, k: int, ef_search: int) -> list[Hit]:
        asked.append(k)
        return [_hit(i, 1.0 - i / 100) for i in range(k)]

    monkeypatch.setattr(retriever, "dense_search", fake_dense)
    reranker = ReverseReranker()

    result = retrieve(
        None,  # type: ignore[arg-type]
        "q",
        mode=RetrievalMode.DENSE,
        k=3,
        embeddings=HashEmbeddings(),
        reranker=reranker,
        rerank_candidates=10,
    )

    assert asked == [10]
    assert len(reranker.seen) == 10
    assert [c.hit.chunk_id for c in result.candidates] == [9, 8, 7]
    assert [c.rerank_score for c in result.candidates] == [1.0, 0.9, 0.8]
    assert result.candidates[0].dense_score == pytest.approx(0.91)
    assert result.best_dense_score == 1.0
