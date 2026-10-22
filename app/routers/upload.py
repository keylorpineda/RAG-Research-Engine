from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.core.config import settings
from app.core.errors import BadRequestError
from app.models.database import DbSession
from app.models.models import Document, DocumentStatus
from app.schemas import UploadOut
from app.services.storage import StoredFile, save_upload

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload(files: Annotated[list[UploadFile], File()], db: DbSession) -> UploadOut:
    if len(files) > settings.max_files_per_upload:
        raise BadRequestError(f"Upload at most {settings.max_files_per_upload} files at a time.")

    stored: list[StoredFile] = []
    try:
        for file in files:
            stored.append(
                await save_upload(file, Path(settings.uploads_dir), settings.max_upload_bytes)
            )
        documents = [
            Document(
                filename=s.display_name,
                mime=s.mime,
                path=str(s.path),
                size=s.size,
                status=DocumentStatus.PENDING,
            )
            for s in stored
        ]
        db.add_all(documents)
        db.commit()
    except BaseException:
        # All or nothing: a rejected file removes the ones already written by this request.
        db.rollback()
        for s in stored:
            s.path.unlink(missing_ok=True)
        raise

    return UploadOut(ids=[d.id for d in documents])
