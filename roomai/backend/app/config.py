"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Core
    environment: str = "development"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    # Database. Defaults to local SQLite so dev works without Postgres.
    # Swap to a postgresql:// URL to use Postgres (models are DB-agnostic).
    database_url: str = "sqlite:///./roomai.db"

    # Auth
    jwt_secret: str = "dev-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 1 week

    # Storage
    storage_path: str = "./storage/uploads"

    # Credits
    free_signup_credits: int = 3

    # Upload validation
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB
    min_image_dimension: int = 400


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
