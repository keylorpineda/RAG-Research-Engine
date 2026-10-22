"""Stable error responses.

Every error leaves the API as ``{"error": {"code", "message", "requestId"}}``. Exception text,
provider responses and file paths are logged server-side and never sent to the client.
"""

import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class PayloadTooLargeError(AppError):
    status_code = 413
    code = "payload_too_large"


class UnsupportedMediaError(AppError):
    status_code = 415
    code = "unsupported_media_type"


class UpstreamError(AppError):
    """A provider (embeddings, LLM, reranker) failed. The detail stays in the logs."""

    status_code = 502
    code = "upstream_error"


class ProviderNotConfiguredError(AppError):
    status_code = 503
    code = "provider_not_configured"


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def error_response(
    request: Request, status_code: int, code: str, message: str, **extra: Any
) -> JSONResponse:
    request_id = _request_id(request)
    body = {"error": {"code": code, "message": message, "requestId": request_id, **extra}}
    # Set here too: unhandled errors are answered outside the request-id middleware.
    return JSONResponse(
        status_code=status_code, content=body, headers={REQUEST_ID_HEADER: request_id}
    )


def install_error_handling(app: FastAPI) -> None:
    @app.middleware("http")
    async def assign_request_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request.state.request_id
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:  # noqa: PLR2004
            logger.error("[%s] %s: %s", _request_id(request), exc.code, exc, exc_info=exc)
        return error_response(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return error_response(request, exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {"loc": list(e["loc"]), "message": e["msg"], "type": e["type"]} for e in exc.errors()
        ]
        return error_response(
            request, 422, "validation_error", "The request is not valid.", details=details
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("[%s] unhandled error", _request_id(request), exc_info=exc)
        return error_response(request, 500, "internal_error", "Something went wrong.")
