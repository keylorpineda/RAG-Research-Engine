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
# Rate limits are usually per minute: give the window time to reset.
RATE_LIMIT_ATTEMPTS = 6
RATE_LIMIT_BASE_DELAY_S = 5.0
MAX_DELAY_S = 60.0


def _delay(attempt: int, response: httpx.Response | None) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            return min(float(retry_after), MAX_DELAY_S)
        if response.status_code == 429:  # noqa: PLR2004
            return float(min(MAX_DELAY_S, RATE_LIMIT_BASE_DELAY_S * 2 ** (attempt - 1)))
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

    Server and network errors get 4 attempts (0.5 s, 1 s, 2 s apart). Rate limits get 6, up to
    a minute apart, because provider limits are usually per minute.

    Raises ``UpstreamError`` with a generic message. Status codes and response bodies are only
    logged, so provider details never reach API clients.
    """
    wait = sleep or time.sleep
    attempt = 0
    while True:
        attempt += 1
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
        rate_limited = response is not None and response.status_code == 429  # noqa: PLR2004
        if attempt >= (RATE_LIMIT_ATTEMPTS if rate_limited else MAX_ATTEMPTS):
            break
        wait(_delay(attempt, response))
    raise UpstreamError(f"The {provider.split(maxsplit=1)[0]} provider failed.")
