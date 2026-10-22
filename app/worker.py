"""Ingestion worker: ``python -m app.worker``.

Runs apart from the API, so embedding large documents never competes with request handling.
Start as many as you like; they coordinate through the jobs table.
"""

import logging
import os
import signal
import socket
import threading
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.config import settings
from app.ingestion import queue
from app.ingestion.pipeline import ingest_document
from app.models.database import SessionLocal
from app.models.models import Document, DocumentStatus
from app.providers.embeddings import EmbeddingProvider, get_embedding_provider

logger = logging.getLogger("app.worker")


def worker_name() -> str:
    return f"{socket.gethostname()}:{os.getpid()}:{threading.get_ident()}"


def process_one(
    db: Session,
    embeddings: EmbeddingProvider,
    *,
    worker: str,
    lease_seconds: float,
    max_attempts: int,
) -> bool:
    """Claim and process one job. Returns False when there was nothing to do."""
    job = queue.claim(db, worker, lease_seconds)
    if job is None:
        return False
    document = db.get(Document, job.document_id)
    if document is None:  # deleted while queued
        queue.complete(db, job.id)
        db.commit()
        return True

    document.status = DocumentStatus.PROCESSING
    db.commit()
    try:
        ingest_document(db, document, embeddings)
        queue.complete(db, job.id)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Job %s (document %s) failed on attempt %d", job.id, document.id, job.attempts
        )
        document = db.get(Document, job.document_id)
        retrying = queue.fail(db, job.id, f"{type(exc).__name__}: {exc}", max_attempts)
        if document is not None:
            document.status = DocumentStatus.PENDING if retrying else DocumentStatus.ERROR
        db.commit()
    return True


def run(
    stop: threading.Event,
    *,
    session_factory: Callable[[], Session] = SessionLocal,
    embeddings: EmbeddingProvider | None = None,
    poll_seconds: float | None = None,
) -> None:
    """Process jobs until ``stop`` is set, sleeping ``poll_seconds`` when the queue is empty."""
    name = worker_name()
    provider = embeddings or get_embedding_provider()
    interval = poll_seconds if poll_seconds is not None else settings.worker_poll_seconds
    logger.info("Worker %s started (%s)", name, provider.name)
    while not stop.is_set():
        try:
            with session_factory() as db:
                busy = process_one(
                    db,
                    provider,
                    worker=name,
                    lease_seconds=settings.job_lease_seconds,
                    max_attempts=settings.job_max_attempts,
                )
        except Exception:
            logger.exception("Worker loop error")
            busy = False
        if not busy:
            stop.wait(interval)
    logger.info("Worker %s stopped", name)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    run(stop)


if __name__ == "__main__":
    main()
