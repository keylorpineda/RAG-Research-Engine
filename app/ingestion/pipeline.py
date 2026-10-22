"""Turns a stored file into embedded chunks.

Idempotent: re-ingesting a document replaces its chunks, so a retried or re-claimed job never
leaves duplicates behind.
"""

import logging

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ingestion import chunking, extract
from app.models.models import DocChunk, Document, DocumentStatus
from app.providers.embeddings import EmbeddingProvider

logger = logging.getLogger(__name__)


class EmptyDocumentError(ValueError):
    pass


def ingest_document(db: Session, document: Document, embeddings: EmbeddingProvider) -> int:
    """Extract, chunk and embed ``document``. Returns the number of chunks. Does not commit."""
    chunks = chunking.chunk_document(
        extract.extract(document.path, document.mime),
        size=settings.chunk_size,
        overlap=settings.chunk_overlap,
        strategy=settings.chunking,
    )
    texts = [c.text for c in chunks]
    if not texts:
        raise EmptyDocumentError("No text could be extracted from the document.")

    vectors = embeddings.embed_documents(texts)
    db.execute(delete(DocChunk).where(DocChunk.document_id == document.id))
    db.add_all(
        DocChunk(
            document_id=document.id,
            chunk_index=i,
            section=c.section,
            text=c.text,
            token_count=chunking.approx_tokens(c.text),
            embedding=v,
        )
        for i, (c, v) in enumerate(zip(chunks, vectors, strict=True))
    )
    document.embedding_model = settings.embedding_model
    document.status = DocumentStatus.READY
    logger.info("Ingested document %s (%s): %d chunks", document.id, document.filename, len(texts))
    return len(texts)
