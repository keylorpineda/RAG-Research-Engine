"""HTTP calls to model providers with bounded retries on transient failures."""

import logging
import time
from collections.abc import Callable
from typing import Any

import httpx

from app.core.errors import UpstreamError

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504}
MAX_ATTEMPTS = 4
BASE_DELAY_S = 0.5


def _delay(attempt: int, response: httpx.Response | None) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            return min(float(retry_after), 30.0)
    return float(BASE_DELAY_S * 2 ** (attempt - 1))


def post_with_retries(
    client: httpx.Client,
    url: str,
    payload: dict[str, Any],
    *,
    provider: str,
    sleep: Callable[[float], None] | None = None,
) -> httpx.Response:
    """POST ``payload``; retry 429/5xx and network errors with exponential backoff.

    Raises ``UpstreamError`` with a generic message. Status codes and response bodies are only
    logged, so provider details never reach API clients.
    """
    wait = sleep or time.sleep
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response: httpx.Response | None = None
        try:
            response = client.post(url, json=payload)
        except httpx.TransportError as exc:
            logger.warning("%s attempt %d failed: %s", provider, attempt, exc)
        else:
            if response.is_success:
                return response
            logger.warning(
                "%s attempt %d returned %d: %s",
                provider,
                attempt,
                response.status_code,
                response.text[:300],
            )
            if response.status_code not in RETRYABLE_STATUS:
                break
        if attempt < MAX_ATTEMPTS:
            wait(_delay(attempt, response))
    raise UpstreamError(f"The {provider.split(maxsplit=1)[0]} provider failed.")
