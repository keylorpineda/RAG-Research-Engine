"""Store embeddings in pgvector with an HNSW index.

Moves vectors from the ``embeddings`` JSONB table into ``doc_chunks.embedding vector(N)``, where
N is the dimension of the configured embedding model. Vectors with another dimension cannot be
compared with new queries, so their documents go back to PENDING and are embedded again.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.config import settings

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dim = settings.embedding_dim
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE documents ADD COLUMN embedding_model VARCHAR(200)")
    op.execute(f"ALTER TABLE doc_chunks ADD COLUMN embedding vector({dim})")

    # Copy the vectors whose size matches the configured model.
    op.execute(
        f"""
        UPDATE doc_chunks c
           SET embedding = (e.vector::text)::vector({dim})
          FROM embeddings e
         WHERE e.chunk_id = c.id AND jsonb_array_length(e.vector) = {dim}
        """
    )
    # Documents with any chunk left without a vector are embedded again from scratch.
    op.execute(
        """
        WITH incomplete AS (
          SELECT DISTINCT document_id FROM doc_chunks WHERE embedding IS NULL
        ), deleted AS (
          DELETE FROM doc_chunks WHERE document_id IN (SELECT document_id FROM incomplete)
        )
        UPDATE documents SET status = 'PENDING'
         WHERE id IN (SELECT document_id FROM incomplete)
        """
    )
    op.execute(
        sa.text("UPDATE documents SET embedding_model = :model WHERE status = 'READY'").bindparams(
            model=settings.embedding_model
        )
    )
    op.execute("DROP TABLE embeddings")

    op.execute("DROP INDEX IF EXISTS idx_doc_chunks_doc")
    op.execute("DROP INDEX IF EXISTS idx_doc_chunks_idx")
    op.execute("CREATE INDEX ix_doc_chunks_document_id ON doc_chunks(document_id)")
    op.execute(
        "CREATE INDEX ix_doc_chunks_embedding_hnsw ON doc_chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
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
        INSERT INTO embeddings (chunk_id, vector)
        SELECT id, (embedding::text)::jsonb FROM doc_chunks WHERE embedding IS NOT NULL
        """
    )
    op.execute("DROP INDEX IF EXISTS ix_doc_chunks_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_doc_chunks_document_id")
    op.execute("CREATE INDEX idx_doc_chunks_doc ON doc_chunks(document_id)")
    op.execute("CREATE INDEX idx_doc_chunks_idx ON doc_chunks(chunk_index)")
    op.execute("ALTER TABLE doc_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE documents DROP COLUMN embedding_model")
