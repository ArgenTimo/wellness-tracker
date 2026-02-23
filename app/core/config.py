"""Application configuration loaded from environment."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    api_v1_prefix: str = "/api/v1"
    secret_key: str = "dev-secret-change-in-production-min-32-chars"

    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    database_url: str = "postgresql+asyncpg://wellness:wellness_pass@localhost:5432/wellness_db"
    database_echo: bool = False

    default_clinic_id: str | None = None
    invite_base_url: str = "https://app.example.com/join"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
