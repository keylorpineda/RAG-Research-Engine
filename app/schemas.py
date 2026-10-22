"""Request and response bodies. JSON fields are camelCase, Python attributes snake_case."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.retrieval.retriever import RetrievalMode


class Schema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class DocumentOut(Schema):
    id: int
    filename: str
    mime: str | None
    size: int | None
    status: str
    upload_ts: datetime | None


class ChunkOut(Schema):
    id: int
    chunk_index: int
    token_count: int
    text: str


class DocumentDetailOut(DocumentOut):
    chunks: list[ChunkOut]


class UploadOut(Schema):
    ids: list[int]
    message: str = "uploaded"


class MessageOut(Schema):
    message: str


class QueryRequest(Schema):
    q: str = Field(min_length=1, max_length=2000, description="The question.")
    k: int = Field(default=5, ge=1, le=20, description="Passages to retrieve.")
    threshold: float = Field(
        default=0.3, ge=-1.0, le=1.0, description="Minimum cosine similarity of a passage."
    )
    max_tokens: int = Field(default=4000, ge=100, le=16000)
    mode: RetrievalMode = Field(
        default=RetrievalMode.HYBRID, description="dense, lexical or hybrid (RRF of both)."
    )


class Reference(Schema):
    doc_id: int
    filename: str
    chunk_index: int
    score: float
    dense_score: float | None = None
    lexical_score: float | None = None
    text: str


class QueryResponse(Schema):
    answer: str
    refs: list[Reference]
