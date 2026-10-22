"""Turn the jobs table into a queue that several workers can share.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE jobs ADD COLUMN attempts INT NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE jobs ADD COLUMN run_after TIMESTAMP NOT NULL DEFAULT NOW()")
    op.execute("ALTER TABLE jobs ADD COLUMN locked_by VARCHAR(100)")
    op.execute("ALTER TABLE jobs ADD COLUMN locked_until TIMESTAMP")
    op.execute("ALTER TABLE jobs ALTER COLUMN type SET DEFAULT 'INGEST'")
    op.execute("DROP INDEX IF EXISTS idx_jobs_doc_status")
    op.execute(
        "CREATE INDEX ix_jobs_claimable ON jobs (status, run_after) "
        "WHERE status IN ('PENDING', 'RUNNING')"
    )
    # v1 jobs were a log written after the fact. Close the ones a crash left open and queue
    # every document that is still waiting (or was stuck mid-way) for ingestion.
    op.execute(
        "UPDATE jobs SET status = 'ERROR', error = 'interrupted before v2' "
        "WHERE status IN ('PENDING', 'RUNNING')"
    )
    op.execute("UPDATE documents SET status = 'PENDING' WHERE status = 'PROCESSING'")
    op.execute(
        "INSERT INTO jobs (document_id, type, status) "
        "SELECT id, 'INGEST', 'PENDING' FROM documents WHERE status = 'PENDING'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_jobs_claimable")
    op.execute("CREATE INDEX idx_jobs_doc_status ON jobs(document_id, status)")
    op.execute("ALTER TABLE jobs ALTER COLUMN type DROP DEFAULT")
    for column in ("locked_until", "locked_by", "run_after", "attempts"):
        op.execute(f"ALTER TABLE jobs DROP COLUMN {column}")
