import pathlib
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import get_db
from app.models.models import Document

router = APIRouter(prefix="/api", tags=["upload"])

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}
MAX_FILES = 10
MAX_FILE_SIZE = 20 * 1024 * 1024


@router.post("/upload")
async def upload(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Max {MAX_FILES} files.")

    uploads_dir = pathlib.Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    ids: list[int] = []
    for f in files:
        original_name = f.filename or ""
        fn_lower = original_name.lower()
        if not fn_lower:
            raise HTTPException(status_code=400, detail="Filename is required.")

        ext = pathlib.Path(fn_lower).suffix
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Only TXT/MD/PDF files are supported.")

        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Max 20MB per file.")

        unique_name = f"{uuid.uuid4().hex}_{original_name}"
        dest = uploads_dir / unique_name
        dest.write_bytes(content)

        doc = Document(
            filename=original_name,
            mime=f.content_type,
            path=str(dest.resolve()),
            size=len(content),
            status="PENDING",
        )
        db.add(doc)
        db.flush()
        ids.append(doc.id)

    db.commit()
    return {"ids": ids, "message": "uploaded"}
