import threading
from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import Engine, func, select, text
from sqlalchemy.orm import Session, sessionmaker

from app import worker
from app.ingestion import queue
from app.models.models import DocChunk, Document, DocumentStatus, Job, JobStatus
from tests.fakes import HashEmbeddings


def _add_document(db: Session, folder: Path, name: str, paragraphs: int = 3) -> Document:
    path = folder / name
    path.write_text("\n\n".join(f"{name} paragraph {i} " * 20 for i in range(paragraphs)), "utf-8")
    doc = Document(filename=name, path=str(path), status=DocumentStatus.PENDING)
    db.add(doc)
    db.flush()
    queue.enqueue(db, doc)
    db.commit()
    return doc


def _process(db: Session, embeddings: object = None, max_attempts: int = 3) -> bool:
    return worker.process_one(
        db,
        embeddings or HashEmbeddings(),  # type: ignore[arg-type]
        worker="test",
        lease_seconds=60,
        max_attempts=max_attempts,
    )


def test_a_document_is_queued_once(db: Session, tmp_path: Path) -> None:
    doc = _add_document(db, tmp_path, "a.txt")
    assert queue.enqueue(db, doc) is None  # already pending
    assert db.scalar(select(func.count()).select_from(Job)) == 1


def test_worker_ingests_and_completes_the_job(db: Session, tmp_path: Path) -> None:
    doc = _add_document(db, tmp_path, "a.txt")

    assert _process(db) is True
    assert _process(db) is False  # queue drained

    db.expire_all()
    job = db.scalars(select(Job)).one()
    assert (job.status, job.attempts, job.locked_by) == (JobStatus.DONE, 1, None)
    assert db.get(Document, doc.id).status == DocumentStatus.READY  # type: ignore[union-attr]
    assert db.scalar(select(func.count()).select_from(DocChunk)) > 0


def test_two_workers_never_ingest_the_same_document(engine: Engine, tmp_path: Path) -> None:
    make_session = sessionmaker(bind=engine, expire_on_commit=False)
    with make_session() as db:
        docs = [_add_document(db, tmp_path, f"doc{i}.txt") for i in range(20)]
    claimed: list[int] = []
    lock = threading.Lock()

    class CountingEmbeddings(HashEmbeddings):
        def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
            with lock:
                claimed.append(len(texts))
            return super().embed_documents(texts)

    def run_worker() -> None:
        with make_session() as db:
            while worker.process_one(
                db,
                CountingEmbeddings(),
                worker=threading.current_thread().name,
                lease_seconds=60,
                max_attempts=3,
            ):
                pass

    threads = [threading.Thread(target=run_worker, name=f"w{i}") for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    try:
        with make_session() as db:
            assert len(claimed) == len(docs)  # each document embedded exactly once
            jobs = db.scalars(select(Job)).all()
            assert {j.status for j in jobs} == {JobStatus.DONE}
            assert all(j.attempts == 1 for j in jobs)
            per_doc = db.execute(
                select(DocChunk.document_id, func.count()).group_by(DocChunk.document_id)
            ).all()
            assert len(per_doc) == len(docs)
            assert len({count for _, count in per_doc}) == 1  # no duplicated chunks
            assert {j.locked_by for j in jobs} == {None}
    finally:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE documents, queries, jobs RESTART IDENTITY CASCADE"))


def test_an_expired_lease_is_claimed_again(db: Session, tmp_path: Path) -> None:
    _add_document(db, tmp_path, "a.txt")
    first = queue.claim(db, "crashed-worker", lease_seconds=60)
    assert first is not None
    assert queue.claim(db, "other", lease_seconds=60) is None  # still leased

    db.execute(
        text("UPDATE jobs SET locked_until = :t"),
        {"t": queue.utcnow() - timedelta(seconds=1)},
    )
    db.commit()

    second = queue.claim(db, "other", lease_seconds=60)
    assert second is not None
    assert (second.id, second.attempts) == (first.id, 2)


class FlakyEmbeddings(HashEmbeddings):
    def __init__(self, failures: int) -> None:
        super().__init__()
        self.failures = failures

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if self.failures > 0:
            self.failures -= 1
            raise RuntimeError("provider down")
        return super().embed_documents(texts)


def test_failures_are_retried_with_backoff(db: Session, tmp_path: Path) -> None:
    doc = _add_document(db, tmp_path, "a.txt")
    flaky = FlakyEmbeddings(failures=1)

    _process(db, flaky)
    db.expire_all()
    job = db.scalars(select(Job)).one()
    assert job.status == JobStatus.PENDING
    assert job.run_after > queue.utcnow() + timedelta(seconds=20)
    assert job.error == "RuntimeError: provider down"
    assert db.get(Document, doc.id).status == DocumentStatus.PENDING  # type: ignore[union-attr]
    assert _process(db, flaky) is False  # not due yet

    db.execute(text("UPDATE jobs SET run_after = :t"), {"t": queue.utcnow()})
    db.commit()
    assert _process(db, flaky) is True
    db.expire_all()
    assert db.scalars(select(Job)).one().status == JobStatus.DONE
    assert db.get(Document, doc.id).status == DocumentStatus.READY  # type: ignore[union-attr]


def test_the_last_attempt_marks_the_document_as_failed(db: Session, tmp_path: Path) -> None:
    doc = _add_document(db, tmp_path, "a.txt")
    _process(db, FlakyEmbeddings(failures=5), max_attempts=1)
    db.expire_all()
    assert db.scalars(select(Job)).one().status == JobStatus.ERROR
    assert db.get(Document, doc.id).status == DocumentStatus.ERROR  # type: ignore[union-attr]


def test_reingest_replaces_chunks(db: Session, tmp_path: Path) -> None:
    doc = _add_document(db, tmp_path, "a.txt")
    _process(db)
    before = db.scalar(select(func.count()).select_from(DocChunk))

    assert queue.enqueue(db, doc) is not None
    db.commit()
    _process(db)

    assert db.scalar(select(func.count()).select_from(DocChunk)) == before


@pytest.mark.parametrize(("attempt", "expected"), [(1, 30), (2, 60), (3, 120), (20, 3600)])
def test_backoff_doubles_and_is_capped(attempt: int, expected: float) -> None:
    assert queue.backoff_seconds(attempt) == expected
