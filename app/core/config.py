"""
app/core/config.py

Application configuration loaded from environment variables.
Uses Pydantic Settings for type validation and .env support.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All application configuration comes from environment variables.
    Never hard-code secrets here.
    """

    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str  # required — no default

    # ── Google OAuth ─────────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str  # required — no default

    # ── CORS ─────────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Single shared instance — imported throughout the application.
settings = Settings()  # type: ignore[call-arg]
