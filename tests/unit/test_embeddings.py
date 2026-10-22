import json

import httpx
import pytest
import respx

from app.core.config import Settings
from app.core.errors import ProviderNotConfiguredError, UpstreamError
from app.providers.embeddings import (
    COHERE_EMBED_URL,
    CohereEmbeddings,
    LocalEmbeddings,
    build_embedding_provider,
)


def _ok(request: httpx.Request) -> httpx.Response:
    texts = json.loads(request.content)["texts"]
    return httpx.Response(200, json={"embeddings": {"float": [[0.1, 0.2, 0.3]] * len(texts)}})


@pytest.fixture
def sleeps() -> list[float]:
    return []


@pytest.fixture
def cohere(sleeps: list[float]) -> CohereEmbeddings:
    return CohereEmbeddings("test-key", client=httpx.Client(), sleep=sleeps.append)


@respx.mock
def test_documents_and_queries_use_their_own_input_type(cohere: CohereEmbeddings) -> None:
    route = respx.post(COHERE_EMBED_URL).mock(side_effect=_ok)

    cohere.embed_documents(["a passage"])
    cohere.embed_query("a question")

    sent = [json.loads(call.request.content)["input_type"] for call in route.calls]
    assert sent == ["search_document", "search_query"]


@respx.mock
def test_documents_are_sent_in_batches_of_96(cohere: CohereEmbeddings) -> None:
    route = respx.post(COHERE_EMBED_URL).mock(side_effect=_ok)

    vectors = cohere.embed_documents([f"text {i}" for i in range(200)])

    assert len(vectors) == 200
    assert [len(json.loads(c.request.content)["texts"]) for c in route.calls] == [96, 96, 8]


@respx.mock
def test_rate_limits_are_retried_honoring_retry_after(
    cohere: CohereEmbeddings, sleeps: list[float]
) -> None:
    respx.post(COHERE_EMBED_URL).mock(
        side_effect=[httpx.Response(429, headers={"Retry-After": "2"}), _ok]
    )

    assert cohere.embed_query("q") == [0.1, 0.2, 0.3]
    assert sleeps == [2.0]


@respx.mock
def test_network_errors_are_retried_with_backoff(
    cohere: CohereEmbeddings, sleeps: list[float]
) -> None:
    respx.post(COHERE_EMBED_URL).mock(
        side_effect=[httpx.ConnectError("down"), httpx.ConnectError("down"), _ok]
    )

    cohere.embed_query("q")
    assert sleeps == [0.5, 1.0]


@respx.mock
def test_client_errors_fail_fast_without_leaking_the_body(
    cohere: CohereEmbeddings, sleeps: list[float]
) -> None:
    respx.post(COHERE_EMBED_URL).mock(
        return_value=httpx.Response(400, json={"message": "invalid api token sk-123"})
    )

    with pytest.raises(UpstreamError) as raised:
        cohere.embed_query("q")

    assert "sk-123" not in str(raised.value)
    assert sleeps == []


@respx.mock
def test_persistent_server_errors_give_up_after_four_attempts(
    cohere: CohereEmbeddings, sleeps: list[float]
) -> None:
    route = respx.post(COHERE_EMBED_URL).mock(return_value=httpx.Response(503))

    with pytest.raises(UpstreamError):
        cohere.embed_query("q")
    assert route.call_count == 4
    assert sleeps == [0.5, 1.0, 2.0]


def test_cohere_without_a_key_is_not_configured() -> None:
    with pytest.raises(ProviderNotConfiguredError):
        build_embedding_provider(Settings(embedding_provider="cohere", cohere_api_key="changeme"))


def test_local_embeddings_are_the_default() -> None:
    assert Settings.model_fields["embedding_provider"].default == "local"


def test_local_provider_needs_no_key() -> None:
    provider = build_embedding_provider(Settings(embedding_provider="local", cohere_api_key=""))
    assert isinstance(provider, LocalEmbeddings)
    assert provider.dim == 384


@pytest.mark.model
def test_local_model_is_multilingual() -> None:
    """Downloads the ONNX model once (about 220 MB); cached by CI."""
    import numpy as np  # noqa: PLC0415

    provider = LocalEmbeddings()
    docs = provider.embed_documents(
        [
            "Coroutines are declared with async def and awaited with await.",
            "The recipe needs two cups of flour and an egg.",
        ]
    )
    query = provider.embed_query("¿Cómo se declara una corrutina en Python?")

    def cos(a: list[float], b: list[float]) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    assert len(query) == provider.dim
    assert cos(query, docs[0]) > cos(query, docs[1]) + 0.05
