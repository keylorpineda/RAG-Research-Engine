from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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

    chunks: Mapped[list[DocChunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    jobs: Mapped[list[JobLog]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocChunk(Base):
    __tablename__ = "doc_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int]

    document: Mapped[Document] = relationship(back_populates="chunks")
    embedding: Mapped[Embedding | None] = relationship(
        back_populates="chunk", cascade="all, delete-orphan"
    )


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("doc_chunks.id", ondelete="CASCADE"))
    vector: Mapped[Any] = mapped_column(JSONB)

    chunk: Mapped[DocChunk] = relationship(back_populates="embedding")


class JobLog(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(job_status_type, default=JobStatus.PENDING)
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
