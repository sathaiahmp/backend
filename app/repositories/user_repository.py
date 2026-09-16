"""
app/repositories/user_repository.py

Database access layer for users.
All SQL queries are isolated here — no raw SQL in services or routes.

Security note:
  - get_by_google_id is the primary lookup used during auth.
  - upsert_user creates or updates the user record based on the verified
    Google token payload — never raw browser-supplied data.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User

logger = logging.getLogger(__name__)


def get_by_google_id(db: Session, google_id: str) -> User | None:
    """Return the user matching the given Google ID, or None."""
    return db.execute(
        select(User).where(User.google_id == google_id)
    ).scalar_one_or_none()


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    """Return a user by their internal UUID, or None."""
    return db.get(User, user_id)


def upsert_user(db: Session, payload: dict[str, Any]) -> User:
    """
    Find an existing user by google_id or create a new one.

    Args:
        db:      Active database session.
        payload: Verified Google ID token payload containing:
                   sub, email, name, picture (optional)

    Returns:
        The existing or newly created User.
    """
    google_id: str = payload["sub"]
    email: str = payload["email"]
    name: str = payload.get("name", email)
    picture: str | None = payload.get("picture")

    user = get_by_google_id(db, google_id)

    if user is None:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            profile_picture=picture,
        )
        db.add(user)
        db.flush()  # assigns the UUID without committing
        logger.info("New user created | google_id=%s | email=%s", google_id, email)
    else:
        # Update mutable fields in case Google updates the profile.
        user.name = name
        user.profile_picture = picture
        user.updated_at = datetime.now(timezone.utc)
        logger.info("Existing user logged in | google_id=%s", google_id)

    return user
