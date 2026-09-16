"""
alembic/env.py

Alembic environment configuration.

Key points:
  - DATABASE_URL is read from the environment (never hard-coded).
  - All ORM models are imported via app.models so that autogenerate
    can detect schema changes.
  - Runs in offline mode (generates SQL) or online mode (applies to DB).
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Make the app package importable from the alembic/ directory ───────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.base import Base  # noqa: E402  — must come after sys.path fix

# Import all models so Alembic can detect them for autogenerate.
import app.models  # noqa: F401, E402

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Target metadata (our ORM models) ─────────────────────────────────────────
target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Resolve DATABASE_URL from environment and normalize dialect prefix.
    Raises a clear error if it is not set.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Fall back to alembic.ini value if set (useful for some CI setups).
        url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Copy .env.example to .env and fill in DATABASE_URL."
        )

    # Render Managed PostgreSQL provides 'postgres://' or 'postgresql://'
    # SQLAlchemy 2.0 with psycopg v3 requires 'postgresql+psycopg://'
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Generates SQL without connecting to the database.
    Useful for reviewing migrations before applying them.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    Connects to the database and applies migrations directly.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
