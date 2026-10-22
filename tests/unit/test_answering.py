import json
from typing import Any

import httpx
import pytest
import respx

from app.answering import service
from app.answering.citations import check_citations
from app.answering.prompt import NO_ANSWER, SYSTEM_PROMPT, build_user_prompt
from app.answering.service import AbstainReason, AnswerOptions, answer_question
from app.core.config import Settings
from app.providers.llm import GROQ_URL, GroqLLM
from app.retrieval.dense import Hit
from app.retrieval.retriever import Candidate, Retrieval, RetrievalMode
from tests.fakes import HashEmbeddings

# --- citations -------------------------------------------------------------------------------


def test_valid_citations_are_kept_in_order_of_first_use() -> None:
    checked = check_citations("Uses await [2]. Also async def [1][2].", 3)
    assert checked.text == "Uses await [2]. Also async def [1][2]."
    assert checked.cited == [2, 1]
    assert checked.invalid == []


def test_invented_citations_are_removed_and_reported() -> None:
    checked = check_citations("Fact one [1]. Fact two [7].", 3)
    assert checked.text == "Fact one [1]. Fact two."
    assert checked.cited == [1]
    assert checked.invalid == [7]


def test_grouped_citations_are_normalized() -> None:
    checked = check_citations("Both say so [1, 3; 9].", 3)
    assert checked.text == "Both say so [1][3]."
    assert checked.invalid == [9]


def test_full_width_citations_are_normalized() -> None:
    # U+3010/U+3011 is what gpt-oss writes; U+FF3B, U+FF3D and U+FF0C are full-width [ ] and ,
    lo, lc, fo, fc, comma = chr(0x3010), chr(0x3011), chr(0xFF3B), chr(0xFF3D), chr(0xFF0C)
    answer = f"Up to 99 characters{lo}3{lc}{lo}1{lc} and 72 for comments{fo}2{comma}5{fc}."
    checked = check_citations(answer, 3)
    assert checked.text == "Up to 99 characters[3][1] and 72 for comments[2]."
    assert checked.cited == [3, 1, 2]
    assert checked.invalid == [5]


def test_brackets_that_are_not_citations_are_untouched() -> None:
    text = "Index with items[i] or a list like [a, b]."
    assert check_citations(text, 2).text == text


# --- prompt ----------------------------------------------------------------------------------


def _hit(i: int, text: str = "text", filename: str = "doc.txt") -> Hit:
    return Hit(i, 1, filename, i, text, 10, 0.5)


def test_passages_are_numbered_from_one() -> None:
    prompt = build_user_prompt("Why?", [_hit(4, "first"), _hit(9, "second", "b.md")])
    assert "[1] doc.txt (chunk 4)\nfirst" in prompt
    assert "[2] b.md (chunk 9)\nsecond" in prompt
    assert prompt.endswith("Question: Why?")


def test_system_prompt_defines_the_refusal_token() -> None:
    assert f"reply with exactly {NO_ANSWER}" in SYSTEM_PROMPT


# --- service ---------------------------------------------------------------------------------


class FakeLLM:
    name = "fake:llm"

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.reply


class FakeSession:
    def __init__(self) -> None:
        self.logged: list[Any] = []

    def add(self, obj: Any) -> None:
        self.logged.append(obj)

    def commit(self) -> None:
        pass


def _candidates(*scores: float) -> list[Candidate]:
    return [Candidate(_hit(i, f"passage {i}"), s, s, None) for i, s in enumerate(scores)]


@pytest.fixture
def retrieval(monkeypatch: pytest.MonkeyPatch) -> list[Retrieval]:
    """Set ``retrieval[0]`` to control what ``retrieve`` returns."""
    box = [Retrieval([], None)]
    monkeypatch.setattr(service, "retrieve", lambda *a, **kw: box[0])
    return box


def _ask(llm: FakeLLM, db: FakeSession | None = None, **options: Any) -> service.Answer:
    return answer_question(
        db or FakeSession(),  # type: ignore[arg-type]
        "question",
        AnswerOptions(**options),
        embeddings=HashEmbeddings(),
        llm=llm,
    )


def test_weak_evidence_abstains_without_calling_the_model(retrieval: list[Retrieval]) -> None:
    retrieval[0] = Retrieval(_candidates(0.20, 0.10), best_dense_score=0.20)
    llm = FakeLLM("should not be used")
    db = FakeSession()

    answer = _ask(llm, db, min_similarity=0.35)

    assert not answer.answered
    assert answer.reason == AbstainReason.INSUFFICIENT_EVIDENCE
    assert answer.best_similarity == 0.20
    assert llm.calls == []
    assert db.logged[0].result_refs["reason"] == "insufficient_evidence"


def test_nothing_retrieved_abstains(retrieval: list[Retrieval]) -> None:
    answer = _ask(FakeLLM("x"))
    assert answer.reason == AbstainReason.NO_PASSAGES


def test_model_refusal_is_an_abstention(retrieval: list[Retrieval]) -> None:
    retrieval[0] = Retrieval(_candidates(0.8), best_dense_score=0.8)
    answer = _ask(FakeLLM(f"{NO_ANSWER}."), min_similarity=0.35)
    assert not answer.answered
    assert answer.reason == AbstainReason.MODEL_DECLINED
    assert len(answer.passages) == 1


def test_grounded_answer_maps_citations_to_passages(retrieval: list[Retrieval]) -> None:
    retrieval[0] = Retrieval(_candidates(0.9, 0.7, 0.6), best_dense_score=0.9)
    llm = FakeLLM("It uses await [2]. Invented [5].")

    answer = _ask(llm, k=3, min_similarity=0.35)

    assert answer.answered
    assert answer.text == "It uses await [2]. Invented."
    assert answer.cited == [2]
    assert answer.invalid_citations == [5]
    assert answer.passages[1].hit.text == "passage 1"
    assert "[2] doc.txt (chunk 1)\npassage 1" in llm.calls[0][1]


def test_lexical_only_retrieval_is_gated_on_having_hits(retrieval: list[Retrieval]) -> None:
    lexical = [Candidate(_hit(0), 0.1, None, 0.1)]
    retrieval[0] = Retrieval(lexical, best_dense_score=None)
    answer = _ask(FakeLLM("Yes [1]."), mode=RetrievalMode.LEXICAL, min_similarity=0.99)
    assert answer.answered


def test_threshold_defaults_per_embedding_model() -> None:
    assert Settings(embedding_provider="local").abstain_threshold == 0.55
    assert Settings(embedding_provider="local", min_similarity=0.5).abstain_threshold == 0.5


# --- Groq ------------------------------------------------------------------------------------


@respx.mock
def test_groq_is_called_deterministically_with_system_and_user_messages() -> None:
    route = respx.post(GROQ_URL).mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": " Hi [1] "}}]})
    )
    llm = GroqLLM("key", client=httpx.Client(), sleep=lambda _: None)

    assert llm.complete("system rules", "user text") == "Hi [1]"
    sent = json.loads(route.calls[0].request.content)
    assert sent["temperature"] == 0
    assert [m["role"] for m in sent["messages"]] == ["system", "user"]
    assert "reasoning_effort" not in sent


@respx.mock
def test_groq_sends_the_reasoning_effort_when_set() -> None:
    route = respx.post(GROQ_URL).mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
    )
    llm = GroqLLM("key", reasoning_effort="low", client=httpx.Client(), sleep=lambda _: None)
    llm.complete("s", "u")
    assert json.loads(route.calls[0].request.content)["reasoning_effort"] == "low"
