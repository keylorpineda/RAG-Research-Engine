"""Typed client for the RAG Research Engine HTTP API, used by the desktop app."""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

DEFAULT_URL = "http://localhost:8000/api"

REASONS = {
    "insufficient_evidence": "No passage is similar enough to the question, so the engine "
    "did not ask the language model.",
    "no_passages": "Nothing was retrieved. Upload documents or try other words.",
    "model_declined": "The passages were read, but they do not contain the answer.",
}


class ApiError(Exception):
    """An error response, with the API's message (never a stack trace)."""


@dataclass(frozen=True)
class Reference:
    n: int
    filename: str
    chunk_index: int
    score: float
    dense_score: float | None
    lexical_score: float | None
    cited: bool
    text: str


@dataclass(frozen=True)
class QueryResult:
    answered: bool
    answer: str | None
    reason: str | None
    refs: list[Reference]
    invalid_citations: list[int]
    best_similarity: float | None
    min_similarity: float

    @property
    def explanation(self) -> str:
        """Why the engine did not answer, in plain words."""
        if self.answered or self.reason is None:
            return ""
        text = REASONS.get(self.reason, self.reason)
        if self.reason == "insufficient_evidence" and self.best_similarity is not None:
            text += (
                f" Best similarity {self.best_similarity:.2f}, threshold {self.min_similarity:.2f}."
            )
        return text


def parse_query(body: dict[str, Any]) -> QueryResult:
    evidence = body.get("evidence") or {}
    return QueryResult(
        answered=bool(body["answered"]),
        answer=body.get("answer"),
        reason=body.get("reason"),
        refs=[
            Reference(
                n=r["n"],
                filename=r["filename"],
                chunk_index=r["chunkIndex"],
                score=r["score"],
                dense_score=r.get("denseScore"),
                lexical_score=r.get("lexicalScore"),
                cited=r.get("cited", False),
                text=r.get("text", ""),
            )
            for r in body.get("refs", [])
        ],
        invalid_citations=list(body.get("invalidCitations", [])),
        best_similarity=evidence.get("bestSimilarity"),
        min_similarity=evidence.get("minSimilarity", 0.0),
    )


class RagClient:
    def __init__(self, base_url: str | None = None, client: httpx.Client | None = None) -> None:
        self.base_url = (base_url or os.environ.get("RAG_API_URL") or DEFAULT_URL).rstrip("/")
        self._http = client or httpx.Client(timeout=120.0)

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self._http.request(method, f"{self.base_url}{path}", **kwargs)
        except httpx.TransportError as exc:
            raise ApiError(f"Cannot reach the API at {self.base_url}.") from exc
        if response.is_error:
            try:
                message = response.json()["error"]["message"]
            except (ValueError, KeyError, TypeError):
                message = f"HTTP {response.status_code}"
            raise ApiError(message)
        return response.json()

    def health(self) -> dict[str, Any]:
        return dict(self._request("GET", "/health"))

    def documents(self) -> list[dict[str, Any]]:
        return list(self._request("GET", "/documents"))

    def upload(self, paths: Sequence[Path]) -> list[int]:
        files = [("files", (p.name, p.read_bytes())) for p in paths]
        return list(self._request("POST", "/upload", files=files)["ids"])

    def delete(self, doc_id: int) -> None:
        self._request("DELETE", f"/documents/{doc_id}")

    def reingest(self, doc_id: int) -> None:
        self._request("POST", f"/documents/{doc_id}/reingest")

    def query(self, question: str, *, k: int = 5, mode: str = "hybrid") -> QueryResult:
        body = self._request("POST", "/query", json={"q": question, "k": k, "mode": mode})
        return parse_query(body)
