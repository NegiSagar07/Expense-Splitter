"""
app/core/config.py
------------------
Application settings loaded from environment variables / .env file.
All secrets and external config are accessed ONLY through this module.
No sensitive value is ever hardcoded in source code.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration object.

    Pydantic-Settings reads values from:
      1. Environment variables (highest priority)
      2. .env file in the project root
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    debug: bool = Field(default=False)

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: str = Field(
        ...,
        description=(
            "Full async database URL, e.g. "
            "postgresql+asyncpg://user:pass@host:port/db"
        ),
    )

    # ------------------------------------------------------------------
    # Security / JWT
    # ------------------------------------------------------------------
    secret_key: str = Field(
        ...,
        description="HMAC secret — generate with: openssl rand -hex 32",
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins.",
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        """Return ALLOWED_ORIGINS as a list of stripped strings."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    # ------------------------------------------------------------------
    # Background Jobs
    # ------------------------------------------------------------------
    join_request_expiry_days: int = Field(default=7)


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached singleton Settings instance.

    Using @lru_cache ensures the .env file is only parsed once at startup,
    not on every function call.  In tests, call get_settings.cache_clear()
    before overriding env vars.
    """
    return Settings()
