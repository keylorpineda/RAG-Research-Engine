import json

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text

from app.core.config import settings


def _column_type(engine: Engine, table: str, column: str) -> str:
    with engine.connect() as conn:
        return str(
            conn.execute(
                text(
                    "SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
                    "WHERE attrelid = CAST(:t AS regclass) AND attname = :c"
                ),
                {"t": table, "c": column},
            ).scalar_one()
        )


def test_head_creates_the_vector_column_and_hnsw_index(engine: Engine) -> None:
    assert _column_type(engine, "doc_chunks", "embedding") == f"vector({settings.embedding_dim})"
    with engine.connect() as conn:
        indexdef = conn.execute(
            text("SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_doc_chunks_embedding_hnsw'")
        ).scalar_one()
        old_table = conn.execute(text("SELECT to_regclass('embeddings')")).scalar_one()
    assert "USING hnsw (embedding vector_cosine_ops)" in indexdef
    assert old_table is None


def test_upgrade_moves_v1_vectors_and_requeues_incompatible_documents(
    engine: Engine, alembic_config: Config
) -> None:
    dim = settings.embedding_dim
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "0001")
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO documents (id, filename, path, status) VALUES "
                    "(1, 'same-dim.txt', '/x', 'READY'), (2, 'other-dim.txt', '/y', 'READY')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO doc_chunks (id, document_id, chunk_index, text, token_count) "
                    "VALUES (1, 1, 0, 'a', 1), (2, 2, 0, 'b', 1)"
                )
            )
            conn.execute(
                text("INSERT INTO embeddings (chunk_id, vector) VALUES (1, :v1), (2, :v2)"),
                {"v1": json.dumps([0.5] * dim), "v2": json.dumps([0.5] * 1024)},
            )

        command.upgrade(alembic_config, "head")

        with engine.connect() as conn:
            docs = conn.execute(
                text("SELECT id, status, embedding_model FROM documents ORDER BY id")
            ).all()
            chunks = conn.execute(
                text("SELECT document_id, embedding::text FROM doc_chunks ORDER BY id")
            ).all()
        assert docs == [(1, "READY", settings.embedding_model), (2, "PENDING", None)]
        assert len(chunks) == 1
        assert chunks[0][0] == 1
        assert json.loads(chunks[0][1]) == [0.5] * dim
    finally:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE documents, queries, jobs RESTART IDENTITY CASCADE"))
        command.upgrade(alembic_config, "head")


def test_downgrade_keeps_the_vectors(engine: Engine, alembic_config: Config) -> None:
    dim = settings.embedding_dim
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO documents (id, filename, path, status) VALUES (1,'a','/a','READY')")
        )
        conn.execute(
            text(
                "INSERT INTO doc_chunks"
                " (id, document_id, chunk_index, text, token_count, embedding)"
                " VALUES (1, 1, 0, 't', 1, :v)"
            ),
            {"v": str([0.25] * dim)},
        )
    try:
        command.downgrade(alembic_config, "0001")
        with engine.connect() as conn:
            stored = conn.execute(text("SELECT vector FROM embeddings")).scalar_one()
        assert stored == [0.25] * dim
    finally:
        command.upgrade(alembic_config, "head")
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE documents, queries, jobs RESTART IDENTITY CASCADE"))
