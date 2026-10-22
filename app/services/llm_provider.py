import logging

import httpx

from app.core.config import settings
from app.core.errors import ProviderNotConfiguredError, UpstreamError

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def chat(prompt: str) -> str:
    if not settings.groq_api_key or settings.groq_api_key.strip().lower() == "changeme":
        raise ProviderNotConfiguredError("The language model provider is not configured.")

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.groq_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": settings.groq_max_output_tokens,
    }

    response = httpx.post(GROQ_URL, json=payload, headers=headers, timeout=300.0)
    if not response.is_success:
        logger.error("Groq chat failed: %s %s", response.status_code, response.text[:500])
        raise UpstreamError("The language model provider failed.")

    data = response.json()
    choices = data.get("choices", [])
    if choices:
        return str(choices[0].get("message", {}).get("content", ""))

    return ""
