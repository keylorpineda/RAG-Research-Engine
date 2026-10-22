import pathlib

import pdfplumber


def extract(path: str, mime: str | None = None) -> str:
    p = pathlib.Path(path)
    name_lower = p.name.lower()

    if (mime and "pdf" in mime) or name_lower.endswith(".pdf"):
        text_parts = []
        with pdfplumber.open(str(p)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
        return "\n".join(text_parts)

    return p.read_text(encoding="utf-8", errors="replace")
