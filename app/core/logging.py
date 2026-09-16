"""
app/core/logging.py

Standard library logging configuration.
Call configure_logging() once at application startup.

Do NOT log:
  - Google ID tokens
  - Passwords / secrets
  - Authorization headers
  - Database connection strings
"""

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """Configure root logger based on LOG_LEVEL env var."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )

    # Suppress overly noisy third-party loggers in production.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.APP_ENV == "development" else logging.WARNING
    )

    logging.getLogger(__name__).info(
        "Logging configured | level=%s | env=%s",
        settings.LOG_LEVEL,
        settings.APP_ENV,
    )
