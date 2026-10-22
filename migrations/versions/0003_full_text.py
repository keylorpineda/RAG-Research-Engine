"""Full-text search column for hybrid retrieval.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Generated and stored: Postgres keeps it in sync with `text`, existing rows included.
    op.execute(
        "ALTER TABLE doc_chunks ADD COLUMN tsv tsvector "
        "GENERATED ALWAYS AS (to_tsvector('simple', text)) STORED"
    )
    op.execute("CREATE INDEX ix_doc_chunks_tsv ON doc_chunks USING gin (tsv)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_doc_chunks_tsv")
    op.execute("ALTER TABLE doc_chunks DROP COLUMN tsv")
