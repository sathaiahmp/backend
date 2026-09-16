"""
tests/test_auth.py

Tests for POST /api/v1/auth/google

Covers:
  - Valid Google credential → 200 + user info
  - Invalid credential → 401
  - New user is created on first login
  - Existing user is returned on subsequent login
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.conftest import FAKE_GOOGLE_TOKEN, mock_verify_token

AUTH_URL = "/api/v1/auth/google"


def test_valid_google_credential_returns_user(client: TestClient, db: Session) -> None:
    """A valid Google token must return 200 with the user object."""
    fake_payload = mock_verify_token("sub-001", "alice@example.com", "Alice")

    with patch("app.core.security.id_token.verify_oauth2_token", return_value=fake_payload):
        response = client.post(AUTH_URL, json={"credential": FAKE_GOOGLE_TOKEN})

    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["name"] == "Alice"
    assert "id" in data["user"]


def test_invalid_credential_returns_401(client: TestClient) -> None:
    """An invalid Google token must return 401."""
    with patch(
        "app.core.security.id_token.verify_oauth2_token",
        side_effect=ValueError("Token invalid"),
    ):
        response = client.post(AUTH_URL, json={"credential": "bad.token"})

    assert response.status_code == 401
    assert "detail" in response.json()


def test_missing_credential_field_returns_422(client: TestClient) -> None:
    """Omitting the credential field must return 422 validation error."""
    response = client.post(AUTH_URL, json={})
    assert response.status_code == 422


def test_empty_credential_returns_422(client: TestClient) -> None:
    """An empty string credential must be rejected at schema level."""
    response = client.post(AUTH_URL, json={"credential": ""})
    assert response.status_code == 422


def test_new_user_is_created_in_database(client: TestClient, db: Session) -> None:
    """First-time login must create a new User record in the database."""
    fake_payload = mock_verify_token("sub-new-user", "newuser@example.com", "New User")

    # Confirm user does not exist yet
    existing = db.query(User).filter_by(google_id="sub-new-user").first()
    assert existing is None

    with patch("app.core.security.id_token.verify_oauth2_token", return_value=fake_payload):
        response = client.post(AUTH_URL, json={"credential": FAKE_GOOGLE_TOKEN})

    assert response.status_code == 200
    created = db.query(User).filter_by(google_id="sub-new-user").first()
    assert created is not None
    assert created.email == "newuser@example.com"


def test_existing_user_is_returned_on_second_login(
    client: TestClient, db: Session, sample_user: User
) -> None:
    """Second login with the same Google account must return the existing user."""
    fake_payload = mock_verify_token(
        sample_user.google_id, sample_user.email, sample_user.name
    )

    with patch("app.core.security.id_token.verify_oauth2_token", return_value=fake_payload):
        response = client.post(AUTH_URL, json={"credential": FAKE_GOOGLE_TOKEN})

    assert response.status_code == 200
    data = response.json()
    assert str(data["user"]["id"]) == str(sample_user.id)
    assert data["user"]["email"] == sample_user.email
