"""Text embedding providers.

Asymmetric models embed documents and questions differently, so every provider exposes two
methods instead of one. Mixing them up does not fail: it silently lowers retrieval quality.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from functools import lru_cache
from typing import TYPE_CHECKING, Protocol

import httpx

from app.core.config import COHERE_EMBEDDING_DIMS, LOCAL_EMBEDDING_DIMS, Settings, settings
from app.core.errors import ProviderNotConfiguredError, UpstreamError
from app.providers.http import post_with_retries
from app.providers.ratelimit import TokenBudget, estimate_tokens

if TYPE_CHECKING:
    from fastembed import TextEmbedding

logger = logging.getLogger(__name__)

Vector = list[float]


class EmbeddingProvider(Protocol):
    name: str
    dim: int

    def embed_documents(self, texts: Sequence[str]) -> list[Vector]: ...

    def embed_query(self, text: str) -> Vector: ...


COHERE_EMBED_URL = "https://api.cohere.com/v1/embed"
COHERE_DIMS = COHERE_EMBEDDING_DIMS


class CohereEmbeddings:
    """Cohere v3: ``search_document`` for passages, ``search_query`` for questions."""

    batch_size = 96  # API limit per request

    def __init__(
        self,
        api_key: str,
        model: str = "embed-multilingual-v3.0",
        *,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] | None = None,
        budget: TokenBudget | None = None,
        call_budget: TokenBudget | None = None,
    ) -> None:
        if model not in COHERE_DIMS:
            raise ValueError(f"Unknown Cohere embedding model: {model}")
        self.name = f"cohere:{model}"
        self.dim = COHERE_DIMS[model]
        self._model = model
        self._client = client or httpx.Client(
            timeout=60.0, headers={"Authorization": f"Bearer {api_key}"}
        )
        self._sleep = sleep
        self._budget = budget
        self._call_budget = call_budget  # counts requests, not tokens

    def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        vectors: list[Vector] = []
        for start in range(0, len(texts), self.batch_size):
            vectors.extend(self._embed(texts[start : start + self.batch_size], "search_document"))
        return vectors

    def embed_query(self, text: str) -> Vector:
        return self._embed([text], "search_query")[0]

    def _embed(self, texts: Sequence[str], input_type: str) -> list[Vector]:
        if self._budget is not None:
            waited = self._budget.acquire(sum(estimate_tokens(t) for t in texts))
            if waited:
                logger.info("Waited %.1f s for the Cohere token budget", waited)
        if self._call_budget is not None:
            self._call_budget.acquire(1)
        payload = {
            "model": self._model,
            "texts": list(texts),
            "input_type": input_type,
            "embedding_types": ["float"],
            "truncate": "END",
        }
        response = post_with_retries(
            self._client, COHERE_EMBED_URL, payload, provider="Cohere embed", sleep=self._sleep
        )
        data = response.json()["embeddings"]
        vectors = data["float"] if isinstance(data, dict) else data
        if len(vectors) != len(texts):
            raise UpstreamError("The embedding provider returned an unexpected response.")
        return [[float(v) for v in vector] for vector in vectors]


LOCAL_DIMS = LOCAL_EMBEDDING_DIMS


class LocalEmbeddings:
    """ONNX models on the CPU through fastembed: no API key, reproducible results."""

    def __init__(
        self,
        model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        *,
        cache_dir: str | None = None,
    ) -> None:
        if model not in LOCAL_DIMS:
            raise ValueError(f"Unsupported local embedding model: {model}")
        self.name = f"local:{model}"
        self.dim = LOCAL_DIMS[model]
        self._model_name = model
        self._cache_dir = cache_dir
        self._model: TextEmbedding | None = None

    def _load(self) -> TextEmbedding:
        if self._model is None:
            try:
                from fastembed import TextEmbedding  # noqa: PLC0415 (optional dependency)
            except ImportError as exc:
                raise ProviderNotConfiguredError(
                    "Local embeddings need the 'local' extra: uv sync --extra local"
                ) from exc
            self._model = TextEmbedding(self._model_name, cache_dir=self._cache_dir)
        return self._model

    def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        return [v.tolist() for v in self._load().passage_embed(list(texts), batch_size=64)]

    def embed_query(self, text: str) -> Vector:
        return next(iter(self._load().query_embed(text))).tolist()  # type: ignore[no-any-return]


def build_embedding_provider(config: Settings) -> EmbeddingProvider:
    if config.embedding_provider == "local":
        return LocalEmbeddings(config.local_embedding_model, cache_dir=config.model_cache_dir)
    if not config.cohere_api_key or config.cohere_api_key.strip().lower() == "changeme":
        raise ProviderNotConfiguredError("The embedding provider is not configured.")
    budget = (
        TokenBudget(config.cohere_tokens_per_minute) if config.cohere_tokens_per_minute else None
    )
    calls = config.cohere_embed_requests_per_minute
    return CohereEmbeddings(
        config.cohere_api_key,
        config.cohere_embedding_model,
        budget=budget,
        call_budget=TokenBudget(calls) if calls else None,
    )


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    provider = build_embedding_provider(settings)
    logger.info("Embedding provider: %s (%d dims)", provider.name, provider.dim)
    return provider
