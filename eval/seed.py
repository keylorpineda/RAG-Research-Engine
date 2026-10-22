"""Load the pinned PEP corpus into the database in DATABASE_URL, for a demo instance.

    uv run python -m eval.seed

Applies the migrations, then ingests each PEP with the configured embedding provider (the same
one the API will use). PEPs already in the library are skipped, so it is safe to run again.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import select

from app.core.config import settings
from app.ingestion.pipeline import ingest_document
from app.models.database import SessionLocal
from app.models.models import Document, DocumentStatus
from app.providers.embeddings import get_embedding_provider
from eval.corpus import PEPS_COMMIT, fetch

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = settings.database_url
    command.upgrade(config, "head")

    embeddings = get_embedding_provider()
    start = time.perf_counter()
    added = chunks = 0
    with SessionLocal() as db:
        present = set(db.scalars(select(Document.filename)))
        for path in fetch():
            if path.name in present:
                continue
            doc = Document(
                filename=path.name,
                mime="text/plain",
                path=str(path),
                size=path.stat().st_size,
                status=DocumentStatus.PENDING,
            )
            db.add(doc)
            db.flush()
            chunks += ingest_document(db, doc, embeddings)
            db.commit()  # one PEP at a time: an interrupted run keeps what it finished
            added += 1
            print(f"{path.name}: ready", flush=True)  # alembic owns the logging setup

    seconds = time.perf_counter() - start
    print(
        f"Added {added} PEPs ({chunks} passages) from python/peps@{PEPS_COMMIT[:7]}"
        f" with {settings.embedding_model} in {seconds:.0f} s."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
