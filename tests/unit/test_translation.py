from app.core.errors import UpstreamError
from app.retrieval.translation import QueryTranslator


class FakeLLM:
    name = "fake"

    def __init__(self, reply: str = "What problem does the walrus operator solve?") -> None:
        self.reply = reply
        self.calls: list[str] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append(user)
        return self.reply


class FailingLLM:
    name = "failing"

    def complete(self, system: str, user: str) -> str:
        raise UpstreamError("down")


def test_english_questions_are_not_translated() -> None:
    llm = FakeLLM()
    question = "What does PEP 8 say about tabs?"
    assert QueryTranslator(llm).for_lexical(question) == question
    assert llm.calls == []


def test_spanish_questions_are_translated_once_and_cached() -> None:
    llm = FakeLLM('"What problem does the walrus operator solve?"\n')
    translator = QueryTranslator(llm)

    first = translator.for_lexical("¿Qué problema resuelve el operador morsa?")
    again = translator.for_lexical("¿qué problema  resuelve el operador morsa?")

    assert first == again == "What problem does the walrus operator solve?"
    assert len(llm.calls) == 1


def test_failures_and_odd_replies_fall_back_to_the_question() -> None:
    question = "¿Cómo se declara una corrutina?"
    assert QueryTranslator(FailingLLM()).for_lexical(question) == question
    assert QueryTranslator(FakeLLM("")).for_lexical(question) == question
    assert QueryTranslator(FakeLLM("x" * 500)).for_lexical(question) == question


def test_the_model_is_resolved_only_when_needed() -> None:
    built: list[FakeLLM] = []

    def factory() -> FakeLLM:
        built.append(FakeLLM())
        return built[-1]

    translator = QueryTranslator(factory)
    translator.for_lexical("How are coroutines declared?")
    assert built == []
    translator.for_lexical("¿Cómo se declaran las corrutinas?")
    assert len(built) == 1
