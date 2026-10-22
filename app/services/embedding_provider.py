import logging

import httpx

from app.core.config import settings
from app.core.errors import ProviderNotConfiguredError, UpstreamError

logger = logging.getLogger(__name__)

COHERE_URL = "https://api.cohere.com/v1/embed"


def embed(text: str) -> list[float]:
    return embed_batch([text])[0]


def embed_batch(texts: list[str]) -> list[list[float]]:
    if not settings.cohere_api_key or settings.cohere_api_key.strip().lower() == "changeme":
        raise ProviderNotConfiguredError("The embedding provider is not configured.")

    headers = {
        "Authorization": f"Bearer {settings.cohere_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.cohere_embedding_model,
        "texts": texts,
        "truncate": "NONE",
    }
    if settings.cohere_embedding_input_type:
        payload["input_type"] = settings.cohere_embedding_input_type

    response = httpx.post(COHERE_URL, json=payload, headers=headers, timeout=300.0)
    if not response.is_success:
        logger.error("Cohere embed failed: %s %s", response.status_code, response.text[:500])
        raise UpstreamError("The embedding provider failed.")

    data = response.json()
    return [[float(v) for v in vector] for vector in data["embeddings"]]
