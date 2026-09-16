"""
tests/conftest.py

Shared pytest fixtures for all test modules.

Strategy:
  - Use SQLite in-memory database for tests (no Docker required).
  - Override the get_session and get_current_user FastAPI dependencies.
  - Patch google-auth verification so tests don't call Google's servers.
"""

import os

# ── Set required env vars BEFORE any app module is imported ──────────────────
# Pydantic Settings validates these at import time.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:?check_same_thread=False")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-client-id.apps.googleusercontent.com")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("LOG_LEVEL", "WARNING")


import uuid
from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.database import get_session
from app.main import app
from app.models.user import User

# ── In-memory SQLite for tests ────────────────────────────────────────────────
# check_same_thread=False is required for SQLite + TestClient's threading model.
TEST_DATABASE_URL = "sqlite:///:memory:?check_same_thread=False"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables() -> None:
    """Create all tables once for the entire test session."""
    # SQLite doesn't support PostgreSQL ENUMs — use a VARCHAR-backed version.
    # The ORM models still work; only PostgreSQL ENUM creation is skipped.
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """Provide a fresh database session per test, rolled back afterward."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    TestClient with get_session dependency overridden to use the test DB.
    """
    def override_get_session() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_user(db: Session) -> User:
    """Create and persist a sample user for tests that need one."""
    user = User(
        id=uuid.uuid4(),
        google_id="google-sub-test-001",
        email="test@example.com",
        name="Test User",
        profile_picture="https://example.com/pic.jpg",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture()
def another_user(db: Session) -> User:
    """A second user — used to test cross-user access is blocked."""
    user = User(
        id=uuid.uuid4(),
        google_id="google-sub-test-002",
        email="other@example.com",
        name="Other User",
        profile_picture=None,
    )
    db.add(user)
    db.commit()
    return user


FAKE_GOOGLE_TOKEN = "fake.google.id.token"


def make_auth_headers(token: str = FAKE_GOOGLE_TOKEN) -> dict[str, str]:
    """Return Authorization header dict for protected endpoints."""
    return {"Authorization": f"Bearer {token}"}


def mock_verify_token(google_id: str, email: str, name: str) -> dict[str, Any]:
    """Return a fake verified Google token payload."""
    return {
        "sub": google_id,
        "email": email,
        "name": name,
        "picture": "https://example.com/pic.jpg",
    }
