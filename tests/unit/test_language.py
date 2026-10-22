import json
from pathlib import Path

import pytest

from app.retrieval.language import detect_language

QUESTIONS = Path(__file__).parents[2] / "eval" / "questions.jsonl"


@pytest.mark.parametrize(
    ("question", "lang"),
    [
        ("What does PEP 8 recommend about line length?", "en"),
        ("How are coroutines declared?", "en"),
        ("¿Qué problema resuelve el operador morsa?", "es"),
        ("Cuando se llama a __post_init__ en una dataclass", "es"),
        ("PEP 572", "unknown"),
    ],
)
def test_detects_english_and_spanish_questions(question: str, lang: str) -> None:
    assert detect_language(question) == lang


def test_agrees_with_every_labelled_benchmark_question() -> None:
    rows = [json.loads(line) for line in QUESTIONS.read_text("utf-8").splitlines() if line]
    wrong = [r["question"] for r in rows if detect_language(r["question"]) != r["lang"]]
    assert wrong == []
