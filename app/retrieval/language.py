"""Tells English from Spanish questions, without a model.

Only good for short questions in these two languages, which is all the lexical translation
needs: it decides whether a question shares words with an English corpus.
"""

import re

_WORD = re.compile(r"[a-záéíóúüñ]+")
_SPANISH_MARKS = re.compile(r"[¿¡ñáéíóú]")
_SPANISH = frozenset(
    [
        "qué",
        "que",
        "cómo",
        "como",
        "cuál",
        "cual",
        "cuáles",
        "cuándo",
        "cuando",
        "dónde",
        "donde",
        "por",
        "para",
        "porqué",
        "quién",
        "el",
        "la",
        "los",
        "las",
        "un",
        "una",
        "unos",
        "unas",
        "del",
        "al",
        "es",
        "son",
        "se",
        "lo",
        "le",
        "les",
        "su",
        "sus",
        "y",
        "o",
        "pero",
        "con",
        "sin",
        "hay",
        "está",
        "están",
        "ser",
        "puede",
        "pueden",
        "debe",
        "deben",
        "esto",
        "esta",
        "este",
        "estos",
        "estas",
        "sobre",
        "entre",
        "según",
        "cuál",
        "también",
        "más",
        "muy",
    ]
)
_ENGLISH = frozenset(
    [
        "what",
        "how",
        "which",
        "when",
        "where",
        "why",
        "who",
        "the",
        "a",
        "an",
        "of",
        "to",
        "in",
        "on",
        "for",
        "with",
        "without",
        "is",
        "are",
        "be",
        "can",
        "could",
        "should",
        "does",
        "do",
        "did",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "and",
        "or",
        "but",
        "about",
        "between",
        "from",
        "by",
        "as",
        "at",
        "into",
        "more",
        "most",
    ]
)


def detect_language(text: str) -> str:
    """``"es"``, ``"en"``, or ``"unknown"`` when the question gives no clue."""
    lowered = text.lower()
    words = _WORD.findall(lowered)
    spanish = sum(w in _SPANISH for w in words) + 2 * len(_SPANISH_MARKS.findall(lowered))
    english = sum(w in _ENGLISH for w in words)
    if spanish == english:
        return "unknown"
    return "es" if spanish > english else "en"
