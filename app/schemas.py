"""Request and response bodies. JSON fields are camelCase, Python attributes snake_case."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.answering.service import AbstainReason
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
    chunk_count: int = Field(default=0, description="Passages stored for the document.")


class ChunkOut(Schema):
    id: int
    chunk_index: int
    section: str | None = None
    token_count: int
    text: str


class DocumentDetailOut(DocumentOut):
    chunks: list[ChunkOut]


class UploadOut(Schema):
    ids: list[int]
    message: str = "uploaded"


class MessageOut(Schema):
    message: str


class HealthOut(Schema):
    status: str
    embedding_model: str
    min_similarity: float
    uploads_enabled: bool
    max_upload_mb: int
    max_files_per_upload: int
    questions_left_today: int | None = Field(
        default=None, description="Remaining questions under the daily demo cap, if there is one."
    )
    jobs: dict[str, int] = Field(description="Job count per status.")


class QueryRequest(Schema):
    q: str = Field(min_length=1, max_length=2000, description="The question.")
    k: int = Field(default=5, ge=1, le=20, description="Passages sent to the language model.")
    mode: RetrievalMode = Field(
        default=RetrievalMode.HYBRID, description="dense, lexical or hybrid (RRF of both)."
    )
    max_tokens: int = Field(
        default=4000, ge=100, le=16000, description="Token budget for the passages."
    )
    min_similarity: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Abstain below this best cosine similarity. Defaults to the calibrated value.",
    )


class Reference(Schema):
    """A passage sent to the model. ``n`` is the number used by ``[n]`` in the answer."""

    n: int
    doc_id: int
    filename: str
    chunk_index: int
    section: str | None = Field(default=None, description="Heading the passage sits under.")
    score: float
    dense_score: float | None = None
    lexical_score: float | None = None
    rerank_score: float | None = None
    cited: bool
    text: str


class Evidence(Schema):
    best_similarity: float | None = Field(description="Best cosine similarity among candidates.")
    min_similarity: float = Field(description="Threshold the engine compared it to.")


class QueryResponse(Schema):
    answered: bool
    answer: str | None = Field(description="Null when the engine abstains.")
    reason: AbstainReason | None = Field(
        description="insufficient_evidence, no_passages or model_declined when not answered."
    )
    refs: list[Reference]
    invalid_citations: list[int] = Field(
        description="Citation numbers the model produced that matched no passage (removed)."
    )
    evidence: Evidence
