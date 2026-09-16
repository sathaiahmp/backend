"""
app/services/auth_service.py

Authentication business logic.

Orchestrates:
  1. Verify the Google ID token (security.py)
  2. Upsert the user in the database (user_repository.py)
  3. Return the User object

This service does NOT touch HTTP — it has no knowledge of FastAPI requests.
"""

import logging

from sqlalchemy.orm import Session

from app.core.security import verify_google_token
from app.models.user import User
from app.repositories import user_repository

logger = logging.getLogger(__name__)


def authenticate_google_user(db: Session, credential: str) -> User:
    """
    Verify the Google ID token and return (or create) the local user.

    Args:
        db:         Active database session.
        credential: Raw Google ID token from the frontend.

    Returns:
        Authenticated User ORM object.

    Raises:
        ValueError: If the token is invalid (propagated from security.py).
    """
    payload = verify_google_token(credential)
    user = user_repository.upsert_user(db, payload)
    return user
