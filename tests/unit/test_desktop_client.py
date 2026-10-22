import json

import httpx
import pytest
import respx

from desktop.api import ApiError, RagClient

BASE = "http://rag.test/api"


@pytest.fixture
def client() -> RagClient:
    return RagClient(BASE, client=httpx.Client())


ANSWER = {
    "answered": True,
    "answer": "Use await [1].",
    "reason": None,
    "refs": [
        {
            "n": 1,
            "docId": 3,
            "filename": "pep-0492.rst",
            "chunkIndex": 2,
            "score": 0.03,
            "denseScore": 0.81,
            "lexicalScore": None,
            "rerankScore": None,
            "cited": True,
            "text": "async def ...",
        }
    ],
    "invalidCitations": [7],
    "evidence": {"bestSimilarity": 0.81, "minSimilarity": 0.55},
}


@respx.mock
def test_query_sends_mode_and_parses_citations(client: RagClient) -> None:
    route = respx.post(f"{BASE}/query").mock(return_value=httpx.Response(200, json=ANSWER))

    result = client.query("How?", k=3, mode="dense")

    assert json.loads(route.calls[0].request.content) == {"q": "How?", "k": 3, "mode": "dense"}
    assert result.answered
    assert result.refs[0].cited
    assert result.refs[0].dense_score == 0.81
    assert result.invalid_citations == [7]
    assert result.explanation == ""


@respx.mock
def test_abstention_is_explained(client: RagClient) -> None:
    body = {
        "answered": False,
        "answer": None,
        "reason": "insufficient_evidence",
        "refs": [],
        "invalidCitations": [],
        "evidence": {"bestSimilarity": 0.31, "minSimilarity": 0.55},
    }
    respx.post(f"{BASE}/query").mock(return_value=httpx.Response(200, json=body))

    result = client.query("Capital of Australia?")

    assert not result.answered
    assert "did not ask the language model" in result.explanation
    assert "0.31" in result.explanation
    assert "0.55" in result.explanation


@respx.mock
def test_api_errors_surface_their_message(client: RagClient) -> None:
    error = {
        "error": {
            "code": "upstream_error",
            "message": "The Groq provider failed.",
            "requestId": "x",
        }
    }
    respx.post(f"{BASE}/query").mock(return_value=httpx.Response(502, json=error))

    with pytest.raises(ApiError, match=r"The Groq provider failed\."):
        client.query("q")


@respx.mock
def test_unreachable_api_is_a_clear_error(client: RagClient) -> None:
    respx.get(f"{BASE}/documents").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(ApiError, match=r"Cannot reach the API"):
        client.documents()


def test_base_url_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_API_URL", "http://example.test/api/")
    assert RagClient().base_url == "http://example.test/api"
