import logging
import pathlib
import threading
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import SessionLocal
from app.models.models import DocChunk, Document, Embedding, JobLog
from app.services import chunking, embedding_provider, text_extractor

logger = logging.getLogger(__name__)

_stop_event = threading.Event()
_workers: list[threading.Thread] = []


def start_background_ingestion() -> None:
    _stop_event.clear()
    worker = threading.Thread(target=_loop, daemon=True, name="ingestion-worker")
    worker.start()
    _workers.append(worker)
    logger.info("Ingestion background worker started.")


def stop_background_ingestion() -> None:
    _stop_event.set()
    while _workers:
        _workers.pop().join(timeout=5)


def _loop() -> None:
    interval = settings.ingestion_poll_interval_ms / 1000.0
    while not _stop_event.is_set():
        try:
            _process_pending()
        except Exception as exc:
            logger.error("Ingestion loop error: %s", exc, exc_info=True)
        _stop_event.wait(interval)


def _process_pending() -> None:
    db: Session = SessionLocal()
    try:
        pending = db.query(Document).filter(Document.status == "PENDING").all()
        for doc in pending:
            _ingest_document(db, doc)
    finally:
        db.close()


def _ingest_document(db: Session, doc: Document) -> None:
    job = JobLog(
        document_id=doc.id,
        type="INGEST",
        status="RUNNING",
        started_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        doc.status = "PROCESSING"
        db.commit()
        logger.info("Starting ingestion job %s for document %s (%s)", job.id, doc.id, doc.filename)

        raw_text = text_extractor.extract(doc.path, doc.mime)
        chunks_text = chunking.chunk(raw_text, size=1000, overlap=200)

        uploads_dir = pathlib.Path(settings.uploads_dir)
        uploads_dir.mkdir(parents=True, exist_ok=True)

        chunk_entities: list[DocChunk] = []
        for idx, chunk_text in enumerate(chunks_text):
            c = DocChunk(
                document_id=doc.id,
                chunk_index=idx,
                text=chunk_text,
                token_count=chunking.approx_tokens(chunk_text),
            )
            chunk_entities.append(c)

        db.add_all(chunk_entities)
        db.flush()

        embedding_entities: list[Embedding] = []
        batch_size = 90
        for i in range(0, len(chunk_entities), batch_size):
            batch_objects = chunk_entities[i : i + batch_size]
            batch_texts = [c.text for c in batch_objects]
            vectors = embedding_provider.embed_batch(batch_texts)

            for chunk_obj, vec in zip(batch_objects, vectors, strict=True):
                embedding_entities.append(Embedding(chunk_id=chunk_obj.id, vector=vec))

        db.add_all(embedding_entities)

        doc.status = "READY"
        job.status = "DONE"
        job.finished_at = datetime.utcnow()
        db.commit()
        logger.info(
            "Finished ingestion job %s for document %s. Status set to READY", job.id, doc.id
        )

    except Exception as exc:
        db.rollback()
        doc.status = "ERROR"
        job.status = "ERROR"
        job.error = str(exc)
        job.finished_at = datetime.utcnow()
        db.commit()
        logger.error(
            "Ingestion job %s failed for document %s: %s", job.id, doc.id, exc, exc_info=True
        )
