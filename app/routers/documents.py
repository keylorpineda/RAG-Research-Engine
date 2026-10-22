import logging
import pathlib
from typing import Any

from fastapi import APIRouter, HTTPException

from app.models.database import DbSession
from app.models.models import Document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/documents")
def list_documents(db: DbSession) -> list[dict[str, Any]]:
    docs = db.query(Document).order_by(Document.id).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "mime": d.mime,
            "size": d.size,
            "status": d.status,
            "uploadTs": d.upload_ts.isoformat() if d.upload_ts else None,
        }
        for d in docs
    ]


@router.get("/documents/{doc_id}")
def get_document(doc_id: int, db: DbSession) -> dict[str, Any]:
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id,
        "filename": doc.filename,
        "mime": doc.mime,
        "size": doc.size,
        "status": doc.status,
        "uploadTs": doc.upload_ts.isoformat() if doc.upload_ts else None,
        "chunks": [
            {
                "id": c.id,
                "chunkIndex": c.chunk_index,
                "tokenCount": c.token_count,
                "text": c.text,
            }
            for c in doc.chunks
        ],
    }


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: DbSession) -> dict[str, str]:
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        pathlib.Path(doc.path).unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not delete file for document %s", doc.id, exc_info=True)

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}
