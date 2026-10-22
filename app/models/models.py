from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Computed, Enum, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.config import settings


class Base(DeclarativeBase):
    pass


class DocumentStatus(enum.StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    ERROR = "ERROR"


class JobStatus(enum.StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    ERROR = "ERROR"


doc_status_type = Enum(
    "PENDING", "PROCESSING", "READY", "ERROR", name="doc_status", create_type=False
)
job_status_type = Enum("PENDING", "RUNNING", "DONE", "ERROR", name="job_status", create_type=False)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str | None] = mapped_column(String(100))
    upload_ts: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("NOW()"))
    path: Mapped[str] = mapped_column(String(500))
    size: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(doc_status_type, default=DocumentStatus.PENDING)
    # Vectors from different models are not comparable: record which one produced them.
    embedding_model: Mapped[str | None] = mapped_column(String(200))

    chunks: Mapped[list[DocChunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocChunk.chunk_index"
    )
    jobs: Mapped[list[Job]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocChunk(Base):
    __tablename__ = "doc_chunks"
    __table_args__ = (
        Index(
            "ix_doc_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_doc_chunks_tsv", "tsv", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int]
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.embedding_dim))
    # Maintained by Postgres; "simple" = no stemming, so English and Spanish behave the same.
    tsv: Mapped[Any] = mapped_column(
        TSVECTOR, Computed("to_tsvector('simple', text)", persisted=True), deferred=True
    )

    document: Mapped[Document] = relationship(back_populates="chunks")


class Job(Base):
    """An ingestion job. The table is the queue: workers claim rows with SKIP LOCKED."""

    __tablename__ = "jobs"
    __table_args__ = (
        Index(
            "ix_jobs_claimable",
            "status",
            "run_after",
            postgresql_where=text("status IN ('PENDING', 'RUNNING')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(50), default="INGEST")
    status: Mapped[str] = mapped_column(job_status_type, default=JobStatus.PENDING)
    attempts: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    run_after: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("NOW()"))
    locked_by: Mapped[str | None] = mapped_column(String(100))
    locked_until: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    finished_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    error: Mapped[str | None] = mapped_column(Text)

    document: Mapped[Document | None] = relationship(back_populates="jobs")


class QueryLog(Base):
    __tablename__ = "queries"

    id: Mapped[int] = mapped_column(primary_key=True)
    query_text: Mapped[str] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("NOW()"))
    result_refs: Mapped[Any] = mapped_column(JSONB, nullable=True)
