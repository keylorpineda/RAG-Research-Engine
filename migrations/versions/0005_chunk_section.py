"""Section title of each chunk.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable: chunks cut by fixed windows, and text before the first heading, have none.
    op.add_column("doc_chunks", sa.Column("section", sa.String(300), nullable=True))


def downgrade() -> None:
    op.drop_column("doc_chunks", "section")
