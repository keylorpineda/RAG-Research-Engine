from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.database import get_db
from app.models.models import DocChunk, Document, DocumentStatus


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_documents_report_their_passage_count(db: Session, client: TestClient) -> None:
    ready = Document(filename="ready.md", path="x", status=DocumentStatus.READY)
    pending = Document(filename="pending.md", path="y", status=DocumentStatus.PENDING)
    db.add_all([ready, pending])
    db.flush()
    db.add_all(
        DocChunk(document_id=ready.id, chunk_index=i, text=f"passage {i}", token_count=2)
        for i in range(3)
    )
    db.commit()

    listed = {d["filename"]: d["chunkCount"] for d in client.get("/api/documents").json()}
    assert listed == {"ready.md": 3, "pending.md": 0}
    assert client.get(f"/api/documents/{ready.id}").json()["chunkCount"] == 3
