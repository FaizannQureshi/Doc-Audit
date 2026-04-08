from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Phase 2 settings.

    Production notes:
    - Set DATABASE_URL to a Postgres URL.
    - Configure AUTH0_* to enforce JWT authentication.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="allow",
    )

    DATABASE_URL: str = "sqlite:///./dev.db"
    ENVIRONMENT: str = "dev"  # dev | prod

    # Auth0 (optional but recommended for multi-tenant)
    AUTH0_DOMAIN: str | None = None
    AUTH0_AUDIENCE: str | None = None
    AUTH0_ISSUER: str | None = None


settings = Settings()

