from __future__ import annotations

from functools import lru_cache
from typing import List, Literal, Optional

from pydantic import Field, ValidationError, field_validator, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # =========================
    # App / Runtime
    # =========================
    APP_ENV: Literal["development", "staging", "production"] = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "app_env"),
    )
    DEBUG: bool = Field(
        default=False,
        validation_alias=AliasChoices("DEBUG", "debug"),
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        validation_alias=AliasChoices("LOG_LEVEL", "log_level"),
    )

    API_V1_PREFIX: str = Field(
        default="/api/v1",
        validation_alias=AliasChoices("API_V1_PREFIX", "api_v1_prefix"),
    )

    SECRET_KEY: str = Field(
        default="dev-secret-change-in-production-min-32-chars",
        validation_alias=AliasChoices("SECRET_KEY", "secret_key"),
    )

    # =========================
    # Auth / JWT
    # =========================
    JWT_ALGORITHM: str = Field(
        default="HS256",
        validation_alias=AliasChoices("JWT_ALGORITHM", "jwt_algorithm"),
    )
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        validation_alias=AliasChoices("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "jwt_access_token_expire_minutes"),
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        validation_alias=AliasChoices("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "jwt_refresh_token_expire_days"),
    )

    # =========================
    # Database
    # =========================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://wellness:wellness_pass@localhost:5432/wellness_db",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        validation_alias=AliasChoices("DATABASE_ECHO", "database_echo"),
    )

    # =========================
    # Clinic / Invites
    # =========================
    DEFAULT_CLINIC_ID: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("DEFAULT_CLINIC_ID", "default_clinic_id"),
    )
    INVITE_BASE_URL: str = Field(
        default="https://app.example.com/join",
        validation_alias=AliasChoices("INVITE_BASE_URL", "invite_base_url"),
    )

    # =========================
    # OpenAI Configuration
    # =========================
    OPENAI_API_KEY: str = Field(
        ...,
        validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key"),
    )
    OPENAI_BASE_MODEL: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("OPENAI_BASE_MODEL", "openai_base_model"),
    )

    # =========================
    # Security Layer
    # =========================
    SECURITY_VECTOR_STORE_IDS: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("SECURITY_VECTOR_STORE_IDS", "security_vector_store_ids"),
    )

    @field_validator("SECURITY_VECTOR_STORE_IDS", mode="before")
    @classmethod
    def parse_vector_store_ids(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        raise ValueError("Invalid SECURITY_VECTOR_STORE_IDS format")

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_api_key(cls, value: str):
        if not value or not value.strip():
            raise ValueError("OPENAI_API_KEY must not be empty")
        return value


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        raise RuntimeError(f"Configuration validation error: {e}") from e


settings = get_settings()