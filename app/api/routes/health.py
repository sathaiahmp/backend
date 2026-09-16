"""
app/api/routes/health.py

GET /api/v1/health

Used for:
  - Render health checks
  - Deployment verification
  - Database connectivity detection
  - Local debugging
"""

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.database import engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", summary="Health check")
def health_check() -> JSONResponse:
    """
    Verify application and database health.

    - Returns 200 {"status": "ok"} when the service and database are reachable.
    - Returns 503 {"status": "unhealthy"} if the database is unreachable.
    Never exposes internal error details or connection strings in the response.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ok"},
        )
    except Exception as exc:
        logger.warning("Health check failed — database unreachable: %s", type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy"},
        )
