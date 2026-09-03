"""Application configuration.

Settings are loaded from environment variables (and an optional local ``.env``)
and validated at import/startup time via pydantic-settings. Missing or invalid
*required* values fail fast rather than surfacing later as obscure runtime errors.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "staging", "production"]


class Settings(BaseSettings):
    """Typed, validated application settings."""

    model_config = SettingsConfigDict(
        # Load the repo-root .env when present; real deployments inject real env vars.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    app_env: Environment = "development"
    app_name: str = "Rice Mill ERP"
    log_level: str = "INFO"
    log_json: bool = False

    # ---- HTTP ----
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_allow_origins: str = "http://localhost:3000"

    # ---- Security / session ----
    secret_key: str = Field(min_length=16)
    session_cookie_name: str = "rmerp_session"
    session_cookie_secure: bool = False
    session_ttl_seconds: int = 43_200

    # ---- PostgreSQL ----
    # A full SQLAlchemy URL. Accepts the production ``postgresql+psycopg://`` form
    # and ``sqlite://`` for hermetic tests. Validated by SQLAlchemy at connect time.
    database_url: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "rice_mill_erp"
    postgres_user: str = "rice_mill"
    postgres_password: str = "rice_mill"

    # ---- Redis ----
    redis_url: str = "redis://localhost:6379/0"

    # ---- S3-compatible object storage ----
    s3_endpoint_url: str = "http://localhost:9000"
    s3_region: str = "us-east-1"
    s3_bucket: str = "rice-mill-documents"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_use_path_style: bool = True

    # ---- Observability ----
    sentry_dsn: str | None = None

    @field_validator("log_level")
    @classmethod
    def _normalise_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}")
        return upper

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri(self) -> str:
        """Resolved database URL.

        Prefer an explicit ``DATABASE_URL``; otherwise assemble one from the
        discrete Postgres settings using the psycopg (v3) driver.
        """
        if self.database_url is not None:
            return str(self.database_url)
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (single load per process)."""
    return Settings()
