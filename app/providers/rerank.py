"""Second-stage reranking with a cross-encoder.

First-stage retrievers score the question and each chunk independently. A cross-encoder reads
them together, which usually fixes the order at the top of the list, for one extra API call.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

import httpx

from app.core.config import Settings, settings
from app.core.errors import ProviderNotConfiguredError, UpstreamError
from app.providers.http import post_with_retries
from app.providers.ratelimit import TokenBudget

COHERE_RERANK_URL = "https://api.cohere.com/v2/rerank"


@dataclass(frozen=True)
class Reranked:
    index: int  # position in the list that was sent
    score: float


class Reranker(Protocol):
    name: str

    def rerank(self, query: str, documents: Sequence[str], top_n: int) -> list[Reranked]: ...


class CohereReranker:
    def __init__(
        self,
        api_key: str,
        model: str = "rerank-v3.5",
        *,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] | None = None,
        budget: TokenBudget | None = None,
    ) -> None:
        self.name = f"cohere:{model}"
        self._model = model
        self._client = client or httpx.Client(
            timeout=30.0, headers={"Authorization": f"Bearer {api_key}"}
        )
        self._sleep = sleep
        self._budget = budget  # counts calls, not tokens

    def rerank(self, query: str, documents: Sequence[str], top_n: int) -> list[Reranked]:
        if not documents:
            return []
        if self._budget is not None:
            self._budget.acquire(1)
        payload = {
            "model": self._model,
            "query": query,
            "documents": list(documents),
            "top_n": min(top_n, len(documents)),
        }
        response = post_with_retries(
            self._client, COHERE_RERANK_URL, payload, provider="Cohere rerank", sleep=self._sleep
        )
        results = response.json().get("results", [])
        reranked = [Reranked(int(r["index"]), float(r["relevance_score"])) for r in results]
        if any(not 0 <= r.index < len(documents) for r in reranked):
            raise UpstreamError("The rerank provider returned an unexpected response.")
        return sorted(reranked, key=lambda r: -r.score)


def build_reranker(config: Settings) -> Reranker | None:
    if config.rerank_provider == "none":
        return None
    if not config.cohere_api_key or config.cohere_api_key.strip().lower() == "changeme":
        raise ProviderNotConfiguredError("The rerank provider is not configured.")
    per_minute = config.cohere_rerank_requests_per_minute
    return CohereReranker(
        config.cohere_api_key,
        config.cohere_rerank_model,
        budget=TokenBudget(per_minute) if per_minute else None,
    )


@lru_cache(maxsize=1)
def get_reranker() -> Reranker | None:
    return build_reranker(settings)
