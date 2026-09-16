"""
tests/test_health.py

Tests for GET /api/v1/health
"""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """Health endpoint must return 200 with {"status": "ok"}."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_does_not_require_auth(client: TestClient) -> None:
    """Health endpoint must be public — no auth header needed."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_returns_unhealthy_when_db_fails(client: TestClient) -> None:
    """Health endpoint must return 503 {"status": "unhealthy"} when database fails."""
    from unittest.mock import patch
    with patch("app.api.routes.health.engine.connect", side_effect=Exception("DB connection refused")):
        response = client.get("/api/v1/health")
        assert response.status_code == 503
        assert response.json() == {"status": "unhealthy"}

