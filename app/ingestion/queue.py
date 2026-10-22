"""A job queue on the ``jobs`` table.

Workers claim one job at a time with ``FOR UPDATE SKIP LOCKED``: two workers never get the same
row, and a worker never waits for another one's lock. A claimed job holds a lease
(``locked_until``); if its worker dies, the lease expires and the job can be claimed again.
Failures are retried with exponential backoff up to ``max_attempts``.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.models import Document, DocumentStatus, Job, JobStatus

INGEST = "INGEST"


def utcnow() -> datetime:
    """Naive UTC, matching the TIMESTAMP WITHOUT TIME ZONE columns."""
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass(frozen=True)
class ClaimedJob:
    id: int
    document_id: int
    attempts: int  # including this one


def enqueue(db: Session, document: Document) -> Job | None:
    """Queue ``document`` for ingestion unless a job for it is already waiting or running."""
    active = (
        db.query(Job)
        .filter(
            Job.document_id == document.id,
            Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
        )
        .first()
    )
    if active is not None:
        return None
    document.status = DocumentStatus.PENDING
    job = Job(document_id=document.id, type=INGEST, status=JobStatus.PENDING, run_after=utcnow())
    db.add(job)
    return job


_CLAIM = text(
    """
    UPDATE jobs
       SET status = 'RUNNING',
           attempts = attempts + 1,
           locked_by = :worker,
           locked_until = :now + make_interval(secs => :lease),
           started_at = :now,
           error = NULL
     WHERE id = (
            SELECT id FROM jobs
             WHERE type = 'INGEST'
               AND ((status = 'PENDING' AND run_after <= :now)
                    OR (status = 'RUNNING' AND locked_until < :now))
             ORDER BY run_after, id
             FOR UPDATE SKIP LOCKED
             LIMIT 1)
    RETURNING id, document_id, attempts
    """
)


def claim(db: Session, worker: str, lease_seconds: float) -> ClaimedJob | None:
    """Claim the next due job (or one whose lease expired) and commit the claim."""
    row = db.execute(
        _CLAIM, {"worker": worker, "now": utcnow(), "lease": float(lease_seconds)}
    ).first()
    db.commit()
    return None if row is None else ClaimedJob(*row)


def complete(db: Session, job_id: int) -> None:
    job = db.get(Job, job_id)
    if job is None:
        return
    job.status = JobStatus.DONE
    job.finished_at = utcnow()
    job.locked_by = None
    job.locked_until = None


def backoff_seconds(attempt: int, base: float = 30.0, cap: float = 3600.0) -> float:
    """30 s, 60 s, 120 s ... capped at an hour."""
    return float(min(cap, base * 2 ** (attempt - 1)))


def fail(db: Session, job_id: int, error: str, max_attempts: int) -> bool:
    """Record a failure. Returns True if the job will be retried."""
    job = db.get(Job, job_id)
    if job is None:
        return False
    job.error = error[:2000]
    job.locked_by = None
    job.locked_until = None
    if job.attempts < max_attempts:
        job.status = JobStatus.PENDING
        job.run_after = utcnow() + timedelta(seconds=backoff_seconds(job.attempts))
        return True
    job.status = JobStatus.ERROR
    job.finished_at = utcnow()
    return False


def queue_depth(db: Session) -> dict[str, int]:
    rows = db.execute(text("SELECT status::text, count(*) FROM jobs GROUP BY status")).all()
    return {status: int(count) for status, count in rows}
