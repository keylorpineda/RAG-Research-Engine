"""Translates questions for the lexical retriever.

Full-text search matches words, so a Spanish question finds almost nothing in English text
(lexical Recall@5 0.20 for Spanish against 0.67 for English). Dense search already crosses
languages; only the lexical side gets the translation, and the original question is kept for
everything else (embedding, reranking, the answer).
"""

import logging
from collections import OrderedDict
from collections.abc import Callable
from functools import lru_cache
from threading import Lock

from app.core.config import settings
from app.core.errors import AppError
from app.providers.llm import LLMProvider, get_llm
from app.retrieval.language import detect_language

logger = logging.getLogger(__name__)

TRANSLATE_PROMPT = (
    "Translate the user's question into English. It will be used as a keyword search over "
    "English technical documents. Keep code, identifiers, numbers and names exactly as written. "
    "Reply with the translation only, on one line."
)
MAX_GROWTH = 3  # a "translation" much longer than the question is an answer, not a translation


class QueryTranslator:
    def __init__(
        self,
        llm: LLMProvider | Callable[[], LLMProvider],
        *,
        corpus_language: str = "en",
        cache_size: int = 512,
    ) -> None:
        self._llm = llm
        self._corpus_language = corpus_language
        self._cache_size = cache_size
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._lock = Lock()

    def for_lexical(self, question: str) -> str:
        """The question in the corpus language; unchanged when it already is, or on failure."""
        if detect_language(question) in (self._corpus_language, "unknown"):
            return question
        key = " ".join(question.lower().split())
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
        translated = self._translate(question)
        with self._lock:
            self._cache[key] = translated
            while len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)
        return translated

    def _translate(self, question: str) -> str:
        model = self._llm if isinstance(self._llm, LLMProvider) else self._llm()
        try:
            raw = model.complete(TRANSLATE_PROMPT, question)
        except AppError:
            logger.warning("Translation failed; searching with the original question.")
            return question
        text = raw.strip().strip("\"'").splitlines()[0].strip() if raw.strip() else ""
        if not text or len(text) > MAX_GROWTH * len(question):
            return question
        return text


@lru_cache(maxsize=1)
def get_translator() -> QueryTranslator | None:
    if not settings.lexical_translation:
        return None
    return QueryTranslator(get_llm)
