from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ragdb"
    groq_api_key: str = "changeme"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_max_output_tokens: int = 2048
    cohere_api_key: str = "changeme"
    cohere_embedding_model: str = "embed-multilingual-v3.0"
    cohere_embedding_input_type: str = "search_document"
    uploads_dir: str = "uploads"
    ingestion_poll_interval_ms: int = 2000


settings = Settings()
