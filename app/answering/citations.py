"""Checks the ``[n]`` citations in a generated answer against the passages that were sent."""

import re
from dataclasses import dataclass

_CITATION = re.compile(r"\[(\d+(?:\s*[,;]\s*\d+)*)\]")
_SPACE_BEFORE_PUNCT = re.compile(r"[ \t]+([.,;:!?])")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")


@dataclass(frozen=True)
class CheckedAnswer:
    text: str
    cited: list[int]  # valid passage numbers in order of first use
    invalid: list[int]  # numbers that point to no passage; removed from the text


def check_citations(answer: str, passage_count: int) -> CheckedAnswer:
    """Keep citations to passages ``1..passage_count``; strip and report the rest.

    ``[1, 3]`` is normalized to ``[1][3]``. A model citing ``[7]`` when it was given three
    passages is inventing a source, so that marker is removed rather than shown to the reader.
    """
    cited: list[int] = []
    invalid: list[int] = []

    def replace(match: re.Match[str]) -> str:
        kept: list[int] = []
        for raw in re.split(r"\s*[,;]\s*", match.group(1)):
            n = int(raw)
            if 1 <= n <= passage_count:
                kept.append(n)
                if n not in cited:
                    cited.append(n)
            elif n not in invalid:
                invalid.append(n)
        return "".join(f"[{n}]" for n in kept)

    text = _CITATION.sub(replace, answer)
    text = _MULTI_SPACE.sub(" ", _SPACE_BEFORE_PUNCT.sub(r"\1", text)).strip()
    return CheckedAnswer(text=text, cited=cited, invalid=invalid)
