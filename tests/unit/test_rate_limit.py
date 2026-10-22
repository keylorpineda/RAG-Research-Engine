import json

import httpx
import pytest
import respx

from app.core.config import Settings
from app.core.errors import UpstreamError
from app.providers.embeddings import COHERE_EMBED_URL, CohereEmbeddings, build_embedding_provider
from app.providers.ratelimit import TokenBudget, estimate_tokens


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def test_batches_wait_for_the_window_instead_of_exceeding_it() -> None:
    clock = FakeClock()
    budget = TokenBudget(100_000, clock=clock, sleep=clock.sleep)

    budget.acquire(40_000)
    clock.now += 10
    budget.acquire(40_000)
    clock.now += 10
    waited = budget.acquire(40_000)  # 120k in the window: must wait for the first to expire

    assert waited == pytest.approx(40.0)
    assert clock.slept == [pytest.approx(40.0)]


def test_old_usage_leaves_the_window() -> None:
    clock = FakeClock()
    budget = TokenBudget(100_000, clock=clock, sleep=clock.sleep)
    budget.acquire(90_000)
    clock.now += 61
    assert budget.acquire(90_000) == 0.0


def test_a_request_larger_than_the_limit_goes_alone() -> None:
    clock = FakeClock()
    budget = TokenBudget(10, clock=clock, sleep=clock.sleep)
    assert budget.acquire(50) == 0.0  # empty window: allowed rather than blocked forever
    assert budget.acquire(1) == pytest.approx(60.0)


def test_estimate_errs_high() -> None:
    assert estimate_tokens("a" * 400) >= 100
    assert estimate_tokens("") == 1


@respx.mock
def test_cohere_spends_its_budget_per_batch() -> None:
    clock = FakeClock()
    budget = TokenBudget(1_000, clock=clock, sleep=clock.sleep)

    def ok(request: httpx.Request) -> httpx.Response:
        n = len(json.loads(request.content)["texts"])
        return httpx.Response(200, json={"embeddings": {"float": [[0.1]] * n}})

    route = respx.post(COHERE_EMBED_URL).mock(side_effect=ok)
    cohere = CohereEmbeddings("k", client=httpx.Client(), sleep=lambda _: None, budget=budget)
    cohere.batch_size = 2

    cohere.embed_documents(["x" * 900] * 4)  # two batches of ~600 tokens each

    assert route.call_count == 2
    assert clock.slept == [pytest.approx(60.0)]


@respx.mock
def test_rate_limits_back_off_long_enough_for_a_minute_window() -> None:
    sleeps: list[float] = []
    respx.post(COHERE_EMBED_URL).mock(return_value=httpx.Response(429, json={"message": "limit"}))
    cohere = CohereEmbeddings("k", client=httpx.Client(), sleep=sleeps.append)

    with pytest.raises(UpstreamError):
        cohere.embed_query("q")

    assert sleeps == [5.0, 10.0, 20.0, 40.0, 60.0]  # six attempts


def test_rerank_calls_are_paced_per_minute() -> None:
    clock = FakeClock()
    budget = TokenBudget(2, clock=clock, sleep=clock.sleep)
    for _ in range(3):
        budget.acquire(1)
    assert clock.slept == [pytest.approx(60.0)]


def test_budget_is_built_from_settings() -> None:
    provider = build_embedding_provider(
        Settings(embedding_provider="cohere", cohere_api_key="k", cohere_tokens_per_minute=90_000)
    )
    assert isinstance(provider, CohereEmbeddings)
    assert provider._budget is not None
    assert provider._budget.limit == 90_000
    assert provider._call_budget is None


@respx.mock
def test_cohere_paces_its_calls_per_minute() -> None:
    clock = FakeClock()
    respx.post(COHERE_EMBED_URL).mock(
        return_value=httpx.Response(200, json={"embeddings": {"float": [[0.1]]}})
    )
    cohere = CohereEmbeddings(
        "k",
        client=httpx.Client(),
        sleep=lambda _: None,
        call_budget=TokenBudget(2, clock=clock, sleep=clock.sleep),
    )
    for _ in range(3):
        cohere.embed_query("q")
    assert clock.slept == [pytest.approx(60.0)]


def test_cohere_threshold_is_calibrated() -> None:
    settings = Settings(embedding_provider="cohere", cohere_api_key="k")
    assert settings.abstain_threshold == 0.60
