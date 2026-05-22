"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://jarvis:jarvis_secret@localhost:5432/jarvis"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # ChromaDB
    chroma_url: str = "http://localhost:8000"

    # Models
    default_model: str = "qwen2.5:14b-instruct-q4_K_M"
    fast_model: str = "qwen2.5:3b"
    coding_model: str = "qwen2.5-coder:7b-instruct-q4_K_M"
    embedding_model: str = "nomic-embed-text"

    # Voice
    whisper_model: str = "small"
    tts_voice: str = "af_heart"

    # Security
    secret_key: str = "change-me-in-production"
    api_key: str = "your-api-key-here"

    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
