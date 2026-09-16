"""
app/api/deps.py

FastAPI reusable dependencies.

get_current_user():
  Resolves the authenticated user from the Authorization: Bearer header.
  The token must be a valid Google ID token — the backend re-verifies it
  on every protected request (stateless authentication).

  Why re-verify?
    - Google ID tokens expire after ~1 hour.
    - Re-verification ensures the token is still valid on every request.
    - No custom session store or JWT library is needed.

Usage in a route:
    current_user: User = Depends(get_current_user)
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import verify_google_token
from app.db.database import get_session
from app.models.user import User
from app.repositories import user_repository

logger = logging.getLogger(__name__)

# HTTPBearer reads the Authorization: Bearer <token> header.
# auto_error=False lets us return a clean 401 instead of a 403.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_session),
) -> User:
    """
    FastAPI dependency that resolves the authenticated user.

    Extracts and verifies the Google ID token from the Authorization header.
    Looks up the user in the database by google_id.

    Returns:
        Authenticated User ORM object.

    Raises:
        HTTPException 401: If the token is missing, invalid, or the user
                           does not exist in the database.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = verify_google_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    google_id: str | None = payload.get("sub")
    if not google_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    user = user_repository.get_by_google_id(db, google_id)
    if user is None:
        # Token is valid but this Google account has never authenticated.
        # This guards against edge cases (e.g., database wiped after token issued).
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please sign in via POST /api/v1/auth/google first.",
        )

    return user
