"""Checks the ``[n]`` citations in a generated answer against the passages that were sent."""

import re
from dataclasses import dataclass

# Square brackets, plus the full-width forms some models (gpt-oss) write instead: U+3010/U+3011
# (black lenticular brackets), U+FF3B/U+FF3D (full-width square) and U+FF0C (full-width comma).
_LENTICULAR = chr(0x3010), chr(0x3011)
_FULL_WIDTH = chr(0xFF3B), chr(0xFF3D)
_OPEN = rf"[\[{_LENTICULAR[0]}{_FULL_WIDTH[0]}]"
_CLOSE = rf"[\]{_LENTICULAR[1]}{_FULL_WIDTH[1]}]"
_SEP = rf"\s*[,;{chr(0xFF0C)}]\s*"
_CITATION = re.compile(rf"{_OPEN}(\d+(?:{_SEP}\d+)*){_CLOSE}")
_SPACE_BEFORE_PUNCT = re.compile(r"[ \t]+([.,;:!?])")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")


@dataclass(frozen=True)
class CheckedAnswer:
    text: str
    cited: list[int]  # valid passage numbers in order of first use
    invalid: list[int]  # numbers that point to no passage; removed from the text


def check_citations(answer: str, passage_count: int) -> CheckedAnswer:
    """Keep citations to passages ``1..passage_count``; strip and report the rest.

    ``[1, 3]`` is normalized to ``[1][3]``, and full-width brackets to square ones. A model
    citing ``[7]`` when it was given three passages is inventing a source, so that marker is
    removed rather than shown to the reader.
    """
    cited: list[int] = []
    invalid: list[int] = []

    def replace(match: re.Match[str]) -> str:
        kept: list[int] = []
        for raw in re.split(_SEP, match.group(1)):
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
