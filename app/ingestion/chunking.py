import re
from dataclasses import dataclass
from typing import Literal

from app.ingestion.sections import split_sections

Strategy = Literal["window", "sections"]


@dataclass(frozen=True)
class Chunk:
    text: str
    section: str | None


def chunk_document(
    text: str, *, size: int = 1000, overlap: int = 200, strategy: Strategy = "window"
) -> list[Chunk]:
    """``window``: fixed-size windows over the whole text. ``sections``: the same windows inside
    each section, so no chunk spans two sections and overlap never crosses a heading."""
    if strategy == "window":
        return [Chunk(t, None) for t in chunk(text, size, overlap)]
    return [
        Chunk(t, section.title)
        for section in split_sections(text)
        for t in chunk(section.text, size, overlap)
    ]


def chunk(text: str, size: int = 1000, overlap: int = 200) -> list[str]:
    if not text or not text.strip():
        return []

    normalized = text.replace("\r", "")
    paragraphs = re.split(r"\n\n+", normalized)
    current = ""
    out: list[str] = []

    for raw in paragraphs:
        paragraph = raw.strip()
        if not paragraph:
            continue
        for segment in _split_paragraph(paragraph, size):
            if not segment:
                continue
            current, out = _append_segment(out, current, segment, size, overlap)

    if current:
        out.append(current)

    return out


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _split_paragraph(paragraph: str, size: int) -> list[str]:
    if len(paragraph) <= size:
        return [paragraph]

    words = paragraph.split()
    segments: list[str] = []
    current = ""

    for word in words:
        if not word:
            continue
        if len(word) > size:
            if current:
                segments.append(current)
                current = ""
            start = 0
            while start < len(word):
                end = min(start + size, len(word))
                segments.append(word[start:end])
                start = end
            continue
        if not current:
            current = word
            continue
        candidate = current + " " + word
        if len(candidate) <= size:
            current = candidate
        else:
            segments.append(current)
            current = word

    if current:
        segments.append(current)

    return segments


def _append_segment(
    out: list[str], current: str, segment: str, size: int, overlap: int
) -> tuple[str, list[str]]:
    if len(segment) > size:
        start = 0
        while start < len(segment):
            end = min(start + size, len(segment))
            current, out = _append_segment(out, current, segment[start:end], size, overlap)
            start = end
        return current, out

    if not current:
        return segment, out

    sep = "\n\n"
    if len(current) + len(sep) + len(segment) <= size:
        return current + sep + segment, out

    out.append(current)
    tail = _build_overlap_tail(current, overlap)
    tail = _ensure_tail_fits(tail, len(segment), size, len(sep))

    if tail and len(tail) + len(sep) + len(segment) <= size:
        return tail + sep + segment, out

    return segment, out


def _build_overlap_tail(current: str, overlap: int) -> str:
    if overlap <= 0 or not current:
        return ""
    effective = min(overlap, len(current))
    return current[-effective:]


def _ensure_tail_fits(tail: str, segment_len: int, size: int, sep_len: int) -> str:
    if not tail:
        return tail
    max_tail = size - segment_len - sep_len
    if max_tail <= 0:
        return ""
    if len(tail) > max_tail:
        return tail[-max_tail:]
    return tail
