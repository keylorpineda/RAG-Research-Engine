"""Chat-completion providers that write the grounded answer."""

from collections.abc import Callable
from functools import lru_cache
from typing import Protocol, runtime_checkable

import httpx

from app.core.config import Settings, settings
from app.core.errors import ProviderNotConfiguredError, UpstreamError
from app.providers.http import post_with_retries

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def complete(self, system: str, user: str) -> str: ...


class ChatCompletionsLLM:
    """Any OpenAI-compatible ``/chat/completions`` endpoint. Temperature 0: same passages, same
    answer."""

    def __init__(
        self,
        url: str,
        model: str,
        *,
        api_key: str | None = None,
        label: str = "chat",
        max_tokens: int = 1024,
        reasoning_effort: str | None = None,
        timeout: float = 60.0,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.name = f"{label}:{model}"
        self._url = url
        self._label = label
        self._model = model
        self._max_tokens = max_tokens
        self._reasoning_effort = reasoning_effort
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = client or httpx.Client(timeout=timeout, headers=headers)
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
        if self._reasoning_effort:
            payload["reasoning_effort"] = self._reasoning_effort
        response = post_with_retries(
            self._client, self._url, payload, provider=f"{self._label} chat", sleep=self._sleep
        )
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise UpstreamError("The language model provider returned no answer.") from exc
        return str(content or "").strip()


class GroqLLM(ChatCompletionsLLM):
    """Groq's hosted models."""

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-120b",
        *,
        max_tokens: int = 1024,
        reasoning_effort: str | None = None,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        super().__init__(
            GROQ_URL,
            model,
            api_key=api_key,
            label="Groq",
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            client=client,
            sleep=sleep,
        )
        self.name = f"groq:{model}"


def build_llm(config: Settings) -> LLMProvider:
    if config.llm_provider == "openai_compatible":
        return ChatCompletionsLLM(
            f"{config.llm_base_url.rstrip('/')}/chat/completions",
            config.llm_model,
            api_key=config.llm_api_key,
            label="local",
            max_tokens=config.groq_max_output_tokens,
            timeout=config.llm_timeout_seconds,
        )
    if not config.groq_api_key or config.groq_api_key.strip().lower() == "changeme":
        raise ProviderNotConfiguredError("The language model provider is not configured.")
    return GroqLLM(
        config.groq_api_key,
        config.groq_model,
        max_tokens=config.groq_max_output_tokens,
        reasoning_effort=config.groq_reasoning_effort,
    )


@lru_cache(maxsize=1)
def get_llm() -> LLMProvider:
    return build_llm(settings)
