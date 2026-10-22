import json

import httpx
import pytest
import respx

from app.core.config import Settings
from app.core.errors import ProviderNotConfiguredError
from app.providers.llm import ChatCompletionsLLM, GroqLLM, build_llm

OLLAMA = "http://localhost:11434/v1/chat/completions"


@respx.mock
def test_local_server_needs_no_key() -> None:
    route = respx.post(OLLAMA).mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Yes [1]"}}]})
    )
    llm = build_llm(Settings(llm_provider="openai_compatible", groq_api_key="changeme"))

    assert isinstance(llm, ChatCompletionsLLM)
    assert llm.name == "local:qwen2.5:7b-instruct"
    assert llm.complete("system", "user") == "Yes [1]"
    request = route.calls[0].request
    assert "authorization" not in request.headers
    sent = json.loads(request.content)
    assert sent["model"] == "qwen2.5:7b-instruct"
    assert sent["temperature"] == 0
    assert "reasoning_effort" not in sent


@respx.mock
def test_base_url_model_and_key_are_configurable() -> None:
    route = respx.post("http://gpu-box:8080/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
    )
    llm = build_llm(
        Settings(
            llm_provider="openai_compatible",
            llm_base_url="http://gpu-box:8080/v1/",
            llm_model="llama-3.2-3b",
            llm_api_key="secret",
        )
    )
    llm.complete("s", "u")

    assert route.calls[0].request.headers["authorization"] == "Bearer secret"
    assert json.loads(route.calls[0].request.content)["model"] == "llama-3.2-3b"


def test_groq_stays_the_default_and_needs_its_key() -> None:
    assert isinstance(build_llm(Settings(llm_provider="groq", groq_api_key="key")), GroqLLM)
    with pytest.raises(ProviderNotConfiguredError):
        build_llm(Settings(llm_provider="groq", groq_api_key="changeme"))
