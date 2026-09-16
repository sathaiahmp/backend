"""
app/db/database.py

SQLAlchemy 2.x synchronous engine and session management.

Uses a context-manager session factory compatible with FastAPI dependency injection.
The DATABASE_URL must use the psycopg (v3) driver prefix:
  postgresql+psycopg://...
"""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


def normalize_database_url(url: str) -> str:
    """
    Ensure the PostgreSQL connection URL uses the psycopg (v3) driver dialect.

    Render Managed PostgreSQL provides URLs starting with 'postgres://' or 'postgresql://'.
    SQLAlchemy 2.0 with psycopg v3 requires 'postgresql+psycopg://'.
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


# ── Engine ────────────────────────────────────────────────────────────────────
_database_url = normalize_database_url(settings.DATABASE_URL)
_is_sqlite = _database_url.startswith("sqlite")

if _is_sqlite:
    # SQLite: single-threaded, no connection pool tuning needed
    engine = create_engine(
        _database_url,
        connect_args={"check_same_thread": False},
        echo=settings.APP_ENV == "development",
    )
else:
    # PostgreSQL / psycopg3 (Docker local or Render Managed PostgreSQL)
    engine = create_engine(
        _database_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=settings.APP_ENV == "development",
    )

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session per request
    and ensures it is always closed afterward.

    Usage in a route:
        db: Session = Depends(get_session)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def verify_database_connection() -> None:
    """
    Perform a simple connectivity check at startup.
    Logs success or raises on failure.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified successfully.")
    except Exception as exc:
        logger.error("Database connection failed: %s", exc)
        raise
