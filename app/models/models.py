import enum

from sqlalchemy import (
    BigInteger, Column, Enum, ForeignKey, Integer,
    String, Text, text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    ERROR = "ERROR"


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    ERROR = "ERROR"


doc_status_type = Enum(
    "PENDING", "PROCESSING", "READY", "ERROR",
    name="doc_status",
    create_type=False,
)
job_status_type = Enum(
    "PENDING", "RUNNING", "DONE", "ERROR",
    name="job_status",
    create_type=False,
)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    mime = Column(String(100))
    upload_ts = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    path = Column(String(500), nullable=False)
    size = Column(BigInteger)
    status = Column(doc_status_type, nullable=False, default="PENDING")

    chunks = relationship("DocChunk", back_populates="document", cascade="all, delete-orphan")
    jobs = relationship("JobLog", back_populates="document", cascade="all, delete-orphan")


class DocChunk(Base):
    __tablename__ = "doc_chunks"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)

    document = relationship("Document", back_populates="chunks")
    embedding = relationship("Embedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan")


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True)
    chunk_id = Column(Integer, ForeignKey("doc_chunks.id", ondelete="CASCADE"), nullable=False)
    vector = Column(JSONB, nullable=False)

    chunk = relationship("DocChunk", back_populates="embedding")


class JobLog(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    type = Column(String(50), nullable=False)
    status = Column(job_status_type, nullable=False, default="PENDING")
    started_at = Column(TIMESTAMP)
    finished_at = Column(TIMESTAMP)
    error = Column(Text)

    document = relationship("Document", back_populates="jobs")


class QueryLog(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True)
    query_text = Column(Text, nullable=False)
    ts = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    result_refs = Column(JSONB)
