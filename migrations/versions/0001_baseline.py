"""Baseline: the v1 schema created by init.sql.

Existing v1 databases already have it: mark them with ``alembic stamp 0001`` and then run
``alembic upgrade head``.

Revision ID: 0001
Revises:
Create Date: 2026-10-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TYPE doc_status AS ENUM ('PENDING','PROCESSING','READY','ERROR')")
    op.execute("CREATE TYPE job_status AS ENUM ('PENDING','RUNNING','DONE','ERROR')")
    op.execute(
        """
        CREATE TABLE documents (
          id SERIAL PRIMARY KEY,
          filename VARCHAR(255) NOT NULL,
          mime VARCHAR(100),
          upload_ts TIMESTAMP NOT NULL DEFAULT NOW(),
          path VARCHAR(500) NOT NULL,
          size BIGINT,
          status doc_status NOT NULL DEFAULT 'PENDING'
        )
        """
    )
    op.execute("CREATE INDEX idx_documents_status ON documents(status)")
    op.execute("CREATE INDEX idx_documents_upload_ts ON documents(upload_ts)")
    op.execute(
        """
        CREATE TABLE doc_chunks (
          id SERIAL PRIMARY KEY,
          document_id INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
          chunk_index INT NOT NULL,
          text TEXT NOT NULL,
          token_count INT NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX idx_doc_chunks_doc ON doc_chunks(document_id)")
    op.execute("CREATE INDEX idx_doc_chunks_idx ON doc_chunks(chunk_index)")
    op.execute(
        """
        CREATE TABLE embeddings (
          id SERIAL PRIMARY KEY,
          chunk_id INT NOT NULL REFERENCES doc_chunks(id) ON DELETE CASCADE,
          vector JSONB NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX idx_embeddings_chunk ON embeddings(chunk_id)")
    op.execute(
        """
        CREATE TABLE queries (
          id SERIAL PRIMARY KEY,
          query_text TEXT NOT NULL,
          ts TIMESTAMP NOT NULL DEFAULT NOW(),
          result_refs JSONB
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_queries_text ON queries USING GIN (to_tsvector('english', query_text))"
    )
    op.execute("CREATE INDEX idx_queries_ts ON queries(ts)")
    op.execute(
        """
        CREATE TABLE jobs (
          id SERIAL PRIMARY KEY,
          document_id INT REFERENCES documents(id) ON DELETE CASCADE,
          type VARCHAR(50) NOT NULL,
          status job_status NOT NULL DEFAULT 'PENDING',
          started_at TIMESTAMP,
          finished_at TIMESTAMP,
          error TEXT
        )
        """
    )
    op.execute("CREATE INDEX idx_jobs_doc_status ON jobs(document_id, status)")


def downgrade() -> None:
    for table in ("jobs", "queries", "embeddings", "doc_chunks", "documents"):
        op.execute(f"DROP TABLE IF EXISTS {table}")
    op.execute("DROP TYPE IF EXISTS job_status")
    op.execute("DROP TYPE IF EXISTS doc_status")
