"""Application configuration loaded from environment variables."""

import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Airport AI Platform"
    app_env: str = "development"
    debug: bool = True

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # Security: Use a strong default secret key, but require override in prod
    secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # API Security
    rate_limit_enabled: bool = True
    rate_limit_string: str = "100/minute"

    database_url: str = "sqlite:////app/data/sqlite/airport.db"

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"

    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    rag_top_k: int = 5

    pdf_storage_path: str = "/app/data/pdfs"
    faiss_index_path: str = "/app/data/faiss"
    log_path: str = "/app/data/logs"

    sql_max_rows: int = 100

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
