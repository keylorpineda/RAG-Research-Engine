import re
from typing import List


def chunk(text: str, size: int = 1000, overlap: int = 200) -> List[str]:
    if not text or not text.strip():
        return []

    normalized = text.replace("\r", "")
    paragraphs = re.split(r"\n\n+", normalized)
    current = ""
    out: List[str] = []

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


def _split_paragraph(paragraph: str, size: int) -> List[str]:
    if len(paragraph) <= size:
        return [paragraph]

    words = paragraph.split()
    segments: List[str] = []
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
    out: List[str], current: str, segment: str, size: int, overlap: int
) -> tuple:
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
