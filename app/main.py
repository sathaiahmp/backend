"""
app/main.py

FastAPI application factory.

Responsibilities:
  - Create the FastAPI app instance
  - Configure CORS (restricted to FRONTEND_URL)
  - Register exception handlers
  - Mount API routers
  - Verify database connectivity on startup
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.database import verify_database_connection
from app.exceptions.handlers import register_exception_handlers

# Routes
from app.api.routes import auth, health, tasks

# Configure logging before anything else.
configure_logging()

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Task Management API",
        description=(
            "Graduate Support Engineer Trainee Assessment — "
            "Task management API with Google Authentication."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Restricts cross-origin requests to the configured frontend origin only.
    # Do NOT use allow_origins=["*"] in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
    app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])

    # ── Startup event ─────────────────────────────────────────────────────────
    @app.on_event("startup")
    def on_startup() -> None:
        logger.info("Starting Task Management API | env=%s", settings.APP_ENV)

        # Auto-create tables for SQLite (local dev without running Alembic)
        from app.db.database import engine, _is_sqlite
        from app.db.base import Base
        # Import all models so Base.metadata knows about them
        import app.models.user  # noqa: F401
        import app.models.task  # noqa: F401

        if _is_sqlite:
            logger.info("SQLite detected — creating tables automatically (skipping Alembic).")
            Base.metadata.create_all(bind=engine)
            logger.info("Tables created successfully.")

        verify_database_connection()
        logger.info("Application started successfully.")

    return app


app = create_app()
