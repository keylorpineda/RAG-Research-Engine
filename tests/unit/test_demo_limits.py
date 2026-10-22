from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.answering.service import Answer
from app.core import demo_limits
from app.core.config import settings
from app.core.demo_limits import SlidingWindowLimiter, TtlCache
from app.main import app
from app.models.database import get_db
from app.routers import query as query_route


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_sliding_window_allows_up_to_the_limit_per_key() -> None:
    clock = Clock()
    limiter = SlidingWindowLimiter(2, window=60, clock=clock)

    assert limiter.allow("a")
    assert limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")  # keys are independent

    clock.now += 61
    assert limiter.allow("a")


def test_cache_expires_and_drops_the_least_recently_used() -> None:
    clock = Clock()
    cache: TtlCache[str, int] = TtlCache(size=2, ttl=10, clock=clock)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1  # "a" is now the most recent
    cache.put("c", 3)

    assert cache.get("b") is None
    assert cache.get("a") == 1
    clock.now += 11
    assert cache.get("a") is None


def test_a_zero_size_cache_stores_nothing() -> None:
    cache: TtlCache[str, int] = TtlCache(size=0, ttl=10)
    cache.put("a", 1)
    assert cache.get("a") is None


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    calls: list[str] = []
    app.dependency_overrides[get_db] = lambda: None
    monkeypatch.setattr(query_route, "get_llm", lambda: None)
    monkeypatch.setattr(query_route, "get_embedding_provider", lambda: None)
    monkeypatch.setattr(query_route, "get_reranker", lambda: None)

    def fake_answer(_db: Any, question: str, *_a: Any, **_kw: Any) -> Answer:
        calls.append(question)
        return Answer(False, None, None, best_similarity=0.2)

    monkeypatch.setattr(query_route, "answer_question", fake_answer)
    monkeypatch.setattr(query_route, "answer_cache", TtlCache(size=0, ttl=60))
    demo_limits._limiter_for.cache_clear()
    test_client = TestClient(app, raise_server_exceptions=False)
    test_client.calls = calls  # type: ignore[attr-defined]
    yield test_client
    app.dependency_overrides.clear()


def test_the_daily_cap_answers_with_a_clear_429(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "daily_question_limit", 15)
    monkeypatch.setattr(demo_limits, "questions_today", lambda _db: 15)

    response = client.post("/api/query", json={"q": "What is PEP 8?"})

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "daily_limit_reached"
    assert client.calls == []  # type: ignore[attr-defined]


def test_one_client_cannot_spend_the_whole_cap(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "questions_per_client_per_hour", 2)
    monkeypatch.setattr(settings, "trust_proxy_headers", True)
    visitor = {"X-Forwarded-For": "203.0.113.7, 10.0.0.1"}

    codes = [
        client.post("/api/query", json={"q": f"q{i}"}, headers=visitor).status_code
        for i in range(3)
    ]
    other = client.post("/api/query", json={"q": "q"}, headers={"X-Forwarded-For": "198.51.100.2"})

    assert codes == [200, 200, 429]
    assert other.status_code == 200


def test_repeated_questions_come_from_the_cache_without_counting(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(query_route, "answer_cache", TtlCache(size=8, ttl=60))
    monkeypatch.setattr(settings, "questions_per_client_per_hour", 1)

    first = client.post("/api/query", json={"q": "What is  PEP 8?"})
    again = client.post("/api/query", json={"q": "what is pep 8?"})

    assert first.status_code == again.status_code == 200
    assert again.json() == first.json()
    assert client.calls == ["What is  PEP 8?"]  # type: ignore[attr-defined]


def test_forwarded_headers_are_ignored_unless_trusted(monkeypatch: pytest.MonkeyPatch) -> None:
    request = SimpleNamespace(
        headers={"x-forwarded-for": "203.0.113.7"}, client=SimpleNamespace(host="10.0.0.1")
    )

    monkeypatch.setattr(settings, "trust_proxy_headers", False)
    assert demo_limits.client_key(request) == "10.0.0.1"  # type: ignore[arg-type]
    monkeypatch.setattr(settings, "trust_proxy_headers", True)
    assert demo_limits.client_key(request) == "203.0.113.7"  # type: ignore[arg-type]
