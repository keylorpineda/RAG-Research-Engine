from fastapi.testclient import TestClient

from app.main import app
from app.models.database import get_db


def test_ping_answers_without_a_database() -> None:
    def no_database() -> None:
        raise AssertionError("ping must not open a database session")

    app.dependency_overrides[get_db] = no_database
    try:
        response = TestClient(app).get("/api/ping")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
