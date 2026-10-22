"""Chat-completion providers that write the grounded answer."""

from collections.abc import Callable
from functools import lru_cache
from typing import Protocol

import httpx

from app.core.config import Settings, settings
from app.core.errors import ProviderNotConfiguredError, UpstreamError
from app.providers.http import post_with_retries

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMProvider(Protocol):
    name: str

    def complete(self, system: str, user: str) -> str: ...


class GroqLLM:
    """OpenAI-compatible chat completions on Groq. Temperature 0: same passages, same answer."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        *,
        max_tokens: int = 1024,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.name = f"groq:{model}"
        self._model = model
        self._max_tokens = max_tokens
        self._client = client or httpx.Client(
            timeout=60.0, headers={"Authorization": f"Bearer {api_key}"}
        )
        self._sleep = sleep

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "max_tokens": self._max_tokens,
        }
        response = post_with_retries(
            self._client, GROQ_URL, payload, provider="Groq chat", sleep=self._sleep
        )
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise UpstreamError("The language model provider returned no answer.") from exc
        return str(content or "").strip()


def build_llm(config: Settings) -> LLMProvider:
    if not config.groq_api_key or config.groq_api_key.strip().lower() == "changeme":
        raise ProviderNotConfiguredError("The language model provider is not configured.")
    return GroqLLM(config.groq_api_key, config.groq_model, max_tokens=config.groq_max_output_tokens)


@lru_cache(maxsize=1)
def get_llm() -> LLMProvider:
    return build_llm(settings)
