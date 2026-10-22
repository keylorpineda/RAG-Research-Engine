from pathlib import Path

import pytest

from app.ingestion.sections import Section, split_sections

CORPUS = Path(__file__).parents[2] / "eval" / "corpus"


def test_text_without_headings_is_one_untitled_section() -> None:
    assert split_sections("just a paragraph\n\nand another") == [
        Section(None, "just a paragraph\n\nand another")
    ]


def test_markdown_headings_start_sections_and_keep_their_line() -> None:
    text = "intro\n\n# Install\n\npip install x\n\n## Usage ##\n\nrun it"
    assert split_sections(text) == [
        Section(None, "intro"),
        Section("Install", "Install\n\npip install x"),
        Section("Usage", "Usage\n\nrun it"),
    ]


def test_restructuredtext_underlined_and_overlined_titles() -> None:
    text = (
        "=======\nPEP 999\n=======\n\nPreamble.\n\n"
        "Abstract\n========\n\nShort.\n\nScope\n-----\n\nWide."
    )
    titles = [s.title for s in split_sections(text)]
    assert titles == ["PEP 999", "Abstract", "Scope"]


def test_an_underline_shorter_than_the_title_is_not_a_heading() -> None:
    assert [s.title for s in split_sections("A long line of text\n===\n\nmore")] == [None]


@pytest.mark.parametrize(
    ("text", "titles"),
    [
        ("Body.\n\n2.1 Hybrid retrieval\n\nRRF fuses lists.", [None, "2.1 Hybrid retrieval"]),
        ("Body.\n\n3. Results\n\nNumbers.", [None, "3. Results"]),
        # A numbered sentence inside a paragraph is not a heading.
        ("Steps:\n1. Install the package.\n2. Run it.", [None]),
        ("Body.\n\n1. Install the package.\n\nMore.", [None]),
    ],
)
def test_numbered_headings_as_pdfs_extract_them(text: str, titles: list[str | None]) -> None:
    assert [s.title for s in split_sections(text)] == titles


def test_no_text_is_lost() -> None:
    text = (CORPUS / "pep-0572.rst").read_text("utf-8") if CORPUS.exists() else "a\n\n# b\n\nc"
    sections = split_sections(text)
    joined = "\n".join(s.text for s in sections)
    for word in set(text.split()):
        if set(word) <= set("=-~^*#+`:'\"._"):
            continue  # adornment lines are dropped on purpose
        assert word in joined


@pytest.mark.skipif(not (CORPUS / "pep-0572.rst").exists(), reason="corpus not downloaded")
def test_a_pep_splits_into_its_sections() -> None:
    titles = [s.title for s in split_sections((CORPUS / "pep-0572.rst").read_text("utf-8"))]
    assert "Abstract" in titles
    assert "Rationale" in titles
    assert len(titles) > 10
