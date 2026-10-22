from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.ingestion.queue import queue_depth
from app.models.database import DbSession
from app.schemas import HealthOut

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(db: DbSession) -> HealthOut:
    db.execute(text("SELECT 1"))
    return HealthOut(
        status="ok",
        embedding_model=settings.embedding_model,
        min_similarity=settings.abstain_threshold,
        uploads_enabled=settings.uploads_enabled,
        max_upload_mb=settings.max_upload_mb,
        max_files_per_upload=settings.max_files_per_upload,
        jobs=queue_depth(db),
    )
