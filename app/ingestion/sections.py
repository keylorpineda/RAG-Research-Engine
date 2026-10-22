"""Splits a document into sections at its headings.

Recognized headings:

- Markdown: ``# Title`` to ``###### Title``.
- reStructuredText: a line underlined (optionally also overlined) with one repeated punctuation
  character, at least as long as the title.
- Numbered headings, as PDFs extract them: ``2.1 Hybrid retrieval`` alone on its line, short,
  and not ending like a sentence.

Text before the first heading becomes a section without a title.
"""

import re
from dataclasses import dataclass

_MARKDOWN = re.compile(r"^#{1,6}\s+(?P<title>.+?)\s*#*\s*$")
_RST_ADORNMENT = re.compile(r"^([=\-~^*#+`:'\"._])\1{2,}\s*$")
_NUMBERED = re.compile(r"^\d+(?:\.\d+)*\.?\s+[A-ZÁÉÍÓÚÑ][^\n]{1,78}$")
MAX_TITLE = 120


@dataclass(frozen=True)
class Section:
    title: str | None
    text: str  # includes the heading line, so the title words stay searchable


def split_sections(text: str) -> list[Section]:
    lines = text.replace("\r", "").split("\n")
    sections: list[Section] = []
    title: str | None = None
    body: list[str] = []

    def close() -> None:
        content = "\n".join(body).strip()
        if content:
            sections.append(Section(title, content))

    i = 0
    while i < len(lines):
        heading, consumed = _heading_at(lines, i)
        if heading is not None:
            close()
            title, body = heading, [heading]
            i += consumed
            continue
        body.append(lines[i])
        i += 1
    close()
    return sections


def _heading_at(lines: list[str], i: int) -> tuple[str | None, int]:
    """The heading starting at line ``i`` and how many lines it spans, or ``(None, 0)``."""
    line = lines[i].strip()
    if not line:
        return None, 0

    if match := _MARKDOWN.match(line):
        return match["title"][:MAX_TITLE], 1

    nxt = lines[i + 1].rstrip() if i + 1 < len(lines) else ""
    # Overlined title: ===== / Title / =====
    if _RST_ADORNMENT.match(line) and i + 2 < len(lines):
        title = nxt.strip()
        under = lines[i + 2].rstrip()
        if title and _RST_ADORNMENT.match(under) and len(under) >= len(title):
            return title[:MAX_TITLE], 3
    # Underlined title: Title / =====
    if (
        not _RST_ADORNMENT.match(line)
        and _RST_ADORNMENT.match(nxt)
        and len(nxt) >= len(line)
        and len(line) <= MAX_TITLE
    ):
        return line, 2

    previous_blank = i == 0 or not lines[i - 1].strip()
    next_blank = i + 1 >= len(lines) or not lines[i + 1].strip()
    if (
        previous_blank
        and next_blank
        and _NUMBERED.match(line)
        and not line.endswith((".", ",", ";", ":"))
    ):
        return line, 1
    return None, 0
