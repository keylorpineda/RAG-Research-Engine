import logging
import pathlib

from fastapi import APIRouter

from app.core.errors import BadRequestError, NotFoundError
from app.ingestion import queue
from app.models.database import DbSession
from app.models.models import Document
from app.schemas import DocumentDetailOut, DocumentOut, MessageOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["documents"])


def _get_or_404(db: DbSession, doc_id: int) -> Document:
    doc = db.get(Document, doc_id)
    if doc is None:
        raise NotFoundError("Document not found.")
    return doc


@router.get("/documents")
def list_documents(db: DbSession) -> list[DocumentOut]:
    docs = db.query(Document).order_by(Document.id).all()
    return [DocumentOut.model_validate(d) for d in docs]


@router.get("/documents/{doc_id}")
def get_document(doc_id: int, db: DbSession) -> DocumentDetailOut:
    return DocumentDetailOut.model_validate(_get_or_404(db, doc_id))


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: DbSession) -> MessageOut:
    doc = _get_or_404(db, doc_id)
    try:
        pathlib.Path(doc.path).unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not delete file for document %s", doc.id, exc_info=True)

    db.delete(doc)
    db.commit()
    return MessageOut(message="Document deleted")


@router.post("/documents/{doc_id}/reingest", status_code=202)
def reingest_document(doc_id: int, db: DbSession) -> MessageOut:
    """Queue the document again, for example after changing the embedding model."""
    doc = _get_or_404(db, doc_id)
    if queue.enqueue(db, doc) is None:
        raise BadRequestError("The document is already queued or being processed.")
    db.commit()
    return MessageOut(message="Document queued for ingestion")
