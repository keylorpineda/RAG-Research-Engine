from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.answering.service import AbstainReason, Answer
from app.core.config import settings
from app.main import app
from app.models.database import get_db
from app.models.models import Document
from app.retrieval.dense import Hit
from app.retrieval.retriever import Candidate
from app.routers import query as query_route
from app.routers import upload as upload_route


class FakeSession:
    """Just enough of a SQLAlchemy session for the upload and document routes."""

    def __init__(self) -> None:
        self.added: list[Any] = []
        self.queued: list[Any] = []
        self.rolled_back = False

    def add_all(self, objects: list[Any]) -> None:
        for i, obj in enumerate(objects, start=len(self.added) + 1):
            obj.id = i
        self.added.extend(objects)

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        self.rolled_back = True

    def get(self, _model: type, _id: int) -> None:
        return None


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def uploads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "uploads"
    monkeypatch.setattr(settings, "uploads_dir", str(target))
    return target


@pytest.fixture
def client(session: FakeSession, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: session
    # Queueing is covered by the integration tests; here it only records the documents.
    monkeypatch.setattr(upload_route.queue, "enqueue", lambda _db, doc: session.queued.append(doc))
    # No `with`: the lifespan (ingestion worker) is not started in unit tests.
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def _files(*items: tuple[str, bytes]) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [("files", (name, content, "text/plain")) for name, content in items]


@pytest.mark.parametrize(
    "malicious_name",
    ["x/../../../evil.txt", "..\\..\\evil.txt", "/etc/../evil.txt", "C:\\Windows\\evil.txt"],
)
def test_upload_cannot_escape_the_upload_directory(
    client: TestClient, session: FakeSession, uploads: Path, malicious_name: str
) -> None:
    response = client.post("/api/upload", files=_files((malicious_name, b"hello")))

    assert response.status_code == 201
    doc: Document = session.added[0]
    assert doc.filename == "evil.txt"
    stored = Path(doc.path)
    assert stored.parent == uploads.resolve()
    assert stored.name != "evil.txt"  # server-generated name
    assert stored.read_bytes() == b"hello"
    assert session.queued == [doc]
    assert not (uploads.parent / "evil.txt").exists()


def test_oversized_file_is_rejected_and_removed(
    client: TestClient, session: FakeSession, uploads: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    big = b"a" * (1024 * 1024 + 1)

    response = client.post("/api/upload", files=_files(("big.txt", big)))

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"
    assert list(uploads.iterdir()) == []
    assert session.added == []


def test_a_rejected_file_rolls_back_the_whole_request(
    client: TestClient, session: FakeSession, uploads: Path
) -> None:
    response = client.post(
        "/api/upload", files=_files(("ok.txt", b"fine"), ("fake.pdf", b"MZ\x90\x00 not a pdf"))
    )

    assert response.status_code == 415
    assert list(uploads.iterdir()) == []
    assert session.rolled_back


@pytest.mark.parametrize("name", ["tool.exe", "noext", "archive.tar.gz"])
def test_unsupported_extensions_are_rejected(client: TestClient, uploads: Path, name: str) -> None:
    response = client.post("/api/upload", files=_files((name, b"data")))
    assert response.status_code == 415


def test_binary_content_in_a_text_file_is_rejected(client: TestClient, uploads: Path) -> None:
    response = client.post("/api/upload", files=_files(("notes.txt", b"abc\x00def")))
    assert response.status_code == 415


def test_real_pdf_header_is_accepted(
    client: TestClient, session: FakeSession, uploads: Path
) -> None:
    response = client.post("/api/upload", files=_files(("paper.pdf", b"%PDF-1.7\n...")))
    assert response.status_code == 201
    assert session.added[0].mime == "application/pdf"


def test_unexpected_errors_do_not_leak_details(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("password=hunter2 at /srv/secret/path")

    monkeypatch.setattr(query_route, "get_llm", lambda: None)
    monkeypatch.setattr(query_route, "answer_question", explode)

    response = client.post("/api/query", json={"q": "anything"}, headers={"X-Request-ID": "abc"})

    assert response.status_code == 500
    assert "hunter2" not in response.text
    assert "/srv" not in response.text
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Something went wrong.", "requestId": "abc"}
    }
    assert response.headers["X-Request-ID"] == "abc"


def test_validation_errors_use_the_same_shape(client: TestClient) -> None:
    response = client.post("/api/query", json={"q": "", "k": 500})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert {tuple(d["loc"]) for d in error["details"]} == {("body", "q"), ("body", "k")}


def test_missing_document_is_a_404(client: TestClient) -> None:
    response = client.get("/api/documents/42")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_query_response_shape(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    hit = Hit(
        chunk_id=7,
        document_id=3,
        filename="pep-492.txt",
        chunk_index=2,
        text="t",
        token_count=5,
        score=0.81,
    )
    passage = Candidate(hit, score=0.03, dense_score=0.81, lexical_score=0.2)
    answer = Answer(
        True, "Use await [1].", None, passages=[passage], cited=[1], best_similarity=0.81
    )
    monkeypatch.setattr(query_route, "get_llm", lambda: None)
    monkeypatch.setattr(query_route, "answer_question", lambda *a, **kw: answer)

    body = client.post("/api/query", json={"q": "How?", "minSimilarity": 0.4}).json()

    assert body == {
        "answered": True,
        "answer": "Use await [1].",
        "reason": None,
        "refs": [
            {
                "n": 1,
                "docId": 3,
                "filename": "pep-492.txt",
                "chunkIndex": 2,
                "score": 0.03,
                "denseScore": 0.81,
                "lexicalScore": 0.2,
                "rerankScore": None,
                "cited": True,
                "text": "t",
            }
        ],
        "invalidCitations": [],
        "evidence": {"bestSimilarity": 0.81, "minSimilarity": 0.4},
    }


def test_abstention_has_no_answer_text(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    answer = Answer(False, None, AbstainReason.INSUFFICIENT_EVIDENCE, best_similarity=0.1)
    monkeypatch.setattr(query_route, "get_llm", lambda: None)
    monkeypatch.setattr(query_route, "answer_question", lambda *a, **kw: answer)

    body = client.post("/api/query", json={"q": "Unrelated?"}).json()

    assert body["answered"] is False
    assert body["answer"] is None
    assert body["reason"] == "insufficient_evidence"
    assert body["refs"] == []


def test_uploads_can_be_turned_off(
    client: TestClient, uploads: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "uploads_enabled", False)
    response = client.post("/api/upload", files=_files(("notes.txt", b"hello")))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
    assert not uploads.exists() or list(uploads.iterdir()) == []
