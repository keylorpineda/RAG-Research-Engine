"""Stores uploaded files safely.

The client's filename is display metadata only: files are written under a server-generated name,
streamed in chunks with the size limit enforced on the way, and checked by content, not by the
``Content-Type`` header.
"""

import re
import unicodedata
import uuid
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from fastapi import UploadFile

from app.core.errors import BadRequestError, PayloadTooLargeError, UnsupportedMediaError

ALLOWED_TYPES = {".txt": "text/plain", ".md": "text/markdown", ".pdf": "application/pdf"}
PDF_MAGIC = b"%PDF-"
READ_CHUNK = 1024 * 1024
MAX_NAME_LENGTH = 255
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


@dataclass(frozen=True)
class StoredFile:
    path: Path
    display_name: str
    mime: str
    size: int


def display_name(raw: str | None) -> str:
    """Basename of a client filename, for display only. Handles `/` and `\\` separators."""
    name = PureWindowsPath(raw or "").name  # PureWindowsPath splits on both separators
    name = _CONTROL.sub("", unicodedata.normalize("NFC", name)).strip().lstrip(".")
    if not name:
        raise BadRequestError("The file needs a name.")
    return name[-MAX_NAME_LENGTH:]


def _check_content(head: bytes, ext: str) -> None:
    if ext == ".pdf":
        if not head.startswith(PDF_MAGIC):
            raise UnsupportedMediaError("The file has a .pdf extension but is not a PDF.")
    elif b"\x00" in head:
        raise UnsupportedMediaError("Text files cannot contain binary data.")


async def save_upload(file: UploadFile, uploads_dir: Path, max_bytes: int) -> StoredFile:
    name = display_name(file.filename)
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_TYPES:
        raise UnsupportedMediaError("Only TXT, MD and PDF files are supported.")

    root = uploads_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    dest = root / f"{uuid.uuid4().hex}{ext}"
    if not dest.resolve().is_relative_to(root):  # defense in depth: the name is ours
        raise BadRequestError("Invalid destination.")

    size = 0
    try:
        with dest.open("xb") as out:
            while block := await file.read(READ_CHUNK):
                if size == 0:
                    _check_content(block[:1024], ext)
                size += len(block)
                if size > max_bytes:
                    limit_mb = max_bytes // (1024 * 1024)
                    raise PayloadTooLargeError(f"Each file can be at most {limit_mb} MB.")
                out.write(block)
        if size == 0:
            raise BadRequestError("The file is empty.")
    except BaseException:
        dest.unlink(missing_ok=True)
        raise

    return StoredFile(path=dest, display_name=name, mime=ALLOWED_TYPES[ext], size=size)
