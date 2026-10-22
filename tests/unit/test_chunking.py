import itertools

import pytest

from app.ingestion.chunking import approx_tokens, chunk, chunk_document


def test_empty_text_has_no_chunks() -> None:
    assert chunk("") == []
    assert chunk("   \n\n  ") == []


def test_short_paragraphs_are_merged_into_one_chunk() -> None:
    assert chunk("first\n\nsecond", size=100, overlap=0) == ["first\n\nsecond"]


@pytest.mark.parametrize(("size", "overlap"), [(50, 0), (120, 30), (300, 80)])
def test_no_chunk_exceeds_the_size_limit(size: int, overlap: int) -> None:
    text = "\n\n".join(f"Paragraph {i} " + "word " * (i * 7) for i in range(1, 30))
    chunks = chunk(text, size=size, overlap=overlap)
    assert chunks
    assert all(len(c) <= size for c in chunks)


def test_every_word_survives_chunking() -> None:
    words = [f"w{i}" for i in range(500)]
    chunks = chunk(" ".join(words), size=80, overlap=20)
    joined = " ".join(chunks)
    assert all(w in joined for w in words)


def test_consecutive_chunks_overlap() -> None:
    paragraphs = [f"sentence number {i} " * 3 for i in range(20)]
    chunks = chunk("\n\n".join(paragraphs), size=200, overlap=40)
    assert len(chunks) > 1
    for previous, current in itertools.pairwise(chunks):
        assert previous[-20:] in current


def test_words_longer_than_the_limit_are_split() -> None:
    chunks = chunk("x" * 250, size=100, overlap=0)
    assert [len(c) for c in chunks] == [100, 100, 50]


def test_approx_tokens_is_never_zero() -> None:
    assert approx_tokens("") == 1
    assert approx_tokens("a" * 400) == 100


def test_window_strategy_keeps_the_old_chunks_without_sections() -> None:
    text = "# Title\n\n" + "word " * 300
    chunks = chunk_document(text, size=200, overlap=40, strategy="window")
    assert [c.text for c in chunks] == chunk(text, size=200, overlap=40)
    assert {c.section for c in chunks} == {None}


def test_section_strategy_never_spans_two_sections() -> None:
    text = "intro words\n\n# Install\n\n" + "pip " * 60 + "\n\n# Usage\n\n" + "run " * 60
    chunks = chunk_document(text, size=120, overlap=30, strategy="sections")

    assert chunks[0].section is None
    assert {c.section for c in chunks} == {None, "Install", "Usage"}
    for c in chunks:
        assert not ("pip" in c.text and "run" in c.text)
        assert len(c.text) <= 120
