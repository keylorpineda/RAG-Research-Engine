from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

COHERE_EMBEDDING_DIMS = {
    "embed-multilingual-v3.0": 1024,
    "embed-english-v3.0": 1024,
    "embed-multilingual-light-v3.0": 384,
    "embed-english-light-v3.0": 384,
}
LOCAL_EMBEDDING_DIMS = {
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": 768,
    "intfloat/multilingual-e5-large": 1024,
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ragdb"
    groq_api_key: str = "changeme"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_max_output_tokens: int = 2048
    cohere_api_key: str = "changeme"
    embedding_provider: Literal["cohere", "local"] = "cohere"
    cohere_embedding_model: str = "embed-multilingual-v3.0"
    local_embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    model_cache_dir: str | None = None
    hnsw_ef_search: int = 100
    uploads_dir: str = "uploads"
    max_upload_mb: int = 20
    max_files_per_upload: int = 10
    ingestion_poll_interval_ms: int = 2000

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
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


settings = Settings()
