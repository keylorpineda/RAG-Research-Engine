from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

COHERE_EMBEDDING_DIMS = {
    "embed-multilingual-v3.0": 1024,
    "embed-english-v3.0": 1024,
    "embed-multilingual-light-v3.0": 384,
    "embed-english-light-v3.0": 384,
}
# Minimum cosine similarity of the best passage before the engine answers. Similarity scales
# differ per model, so each one needs its own value; see docs/BENCHMARKS.md for the calibration.
DEFAULT_MIN_SIMILARITY = {
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 0.55,
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": 0.52,
    "embed-multilingual-v3.0": 0.60,
}
FALLBACK_MIN_SIMILARITY = 0.30

LOCAL_EMBEDDING_DIMS = {
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": 768,
    "intfloat/multilingual-e5-large": 1024,
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ragdb"
    groq_api_key: str = "changeme"
    groq_model: str = "openai/gpt-oss-120b"
    # Reasoning models only (gpt-oss): low keeps answers fast and the token budget for the answer.
    groq_reasoning_effort: Literal["low", "medium", "high"] | None = "low"
    groq_max_output_tokens: int = 1024
    # "openai_compatible": a local server such as Ollama or llama.cpp, so nothing leaves the
    # machine. Ollama listens on http://localhost:11434/v1; llama.cpp on http://localhost:8080/v1.
    llm_provider: Literal["groq", "openai_compatible"] = "groq"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5:7b-instruct"
    llm_api_key: str | None = None
    llm_timeout_seconds: float = 180.0  # CPU inference is slow
    min_similarity: float | None = None
    cohere_api_key: str = "changeme"
    # Local by default: the project runs with a single key (Groq). See docs/DECISIONS.md.
    embedding_provider: Literal["cohere", "local"] = "local"
    cohere_embedding_model: str = "embed-multilingual-v3.0"
    # Trial keys allow 100,000 tokens per minute: set 90000 to stay under it while ingesting.
    cohere_tokens_per_minute: int | None = None
    # Trial keys also allow 100 calls per minute (every question embedding is one call).
    cohere_embed_requests_per_minute: int | None = None
    local_embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    model_cache_dir: str | None = None
    hnsw_ef_search: int = 100
    chunk_size: int = 1000  # characters
    chunk_overlap: int = 200
    # "sections": split at headings first, then by size (app/ingestion/sections.py).
    chunking: Literal["window", "sections"] = "window"
    rerank_provider: Literal["none", "cohere"] = "none"
    cohere_rerank_model: str = "rerank-v3.5"
    # Trial keys allow 10 rerank calls per minute.
    cohere_rerank_requests_per_minute: int | None = None
    rerank_candidates: int = 30
    uploads_dir: str = "uploads"
    max_upload_mb: int = 20
    max_files_per_upload: int = 10
    # Off for a public demo: visitors ask about the documents already indexed.
    uploads_enabled: bool = True
    # Public demo on a provider quota (app/core/demo_limits.py). All off by default.
    daily_question_limit: int | None = None
    questions_per_client_per_hour: int | None = None
    answer_cache_size: int = 0  # 0 = no cache; only for instances whose documents do not change
    answer_cache_seconds: int = 86400
    # Read the client address from X-Forwarded-For (set it only behind a proxy you trust).
    trust_proxy_headers: bool = False
    # Origins allowed to call the API from a browser, comma separated. Empty = same origin only.
    cors_origins: str = ""
    # Ingestion worker (python -m app.worker). EMBEDDED_WORKER runs one inside the API process,
    # handy for a single-container setup.
    embedded_worker: bool = False
    worker_poll_seconds: float = 2.0
    job_lease_seconds: float = 900.0
    job_max_attempts: int = 5

    @field_validator("database_url")
    @classmethod
    def _use_psycopg3(cls, url: str) -> str:
        """Accept plain ``postgresql://`` and the old psycopg2 URLs."""
        for prefix in ("postgresql+psycopg2://", "postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url

    @property
    def embedding_model(self) -> str:
        if self.embedding_provider == "local":
            return self.local_embedding_model
        return self.cohere_embedding_model

    @property
    def embedding_dim(self) -> int:
        """Vector size of the configured model; the database column is created with it."""
        dims = LOCAL_EMBEDDING_DIMS if self.embedding_provider == "local" else COHERE_EMBEDDING_DIMS
        if self.embedding_model not in dims:
            raise ValueError(f"Unknown {self.embedding_provider} model: {self.embedding_model}")
        return dims[self.embedding_model]

    @property
    def abstain_threshold(self) -> float:
        """MIN_SIMILARITY when set, otherwise the calibrated value for the embedding model."""
        if self.min_similarity is not None:
            return self.min_similarity
        return DEFAULT_MIN_SIMILARITY.get(self.embedding_model, FALLBACK_MIN_SIMILARITY)

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


settings = Settings()
