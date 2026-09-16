"""
app/api/routes/auth.py

POST /api/v1/auth/google

Accepts a Google ID token from the frontend, verifies it on the backend,
and returns the authenticated user's information.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.schemas.auth import AuthResponse, GoogleAuthRequest, UserResponse
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/auth/google",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate with Google",
    description=(
        "Verify a Google ID token and return the authenticated user. "
        "Creates a new user record if the Google account has not signed in before."
    ),
)
def google_auth(
    body: GoogleAuthRequest,
    db: Session = Depends(get_session),
) -> AuthResponse:
    """
    POST /api/v1/auth/google

    The backend verifies the Google ID token — never trusting browser-supplied
    identity information without cryptographic verification.
    """
    try:
        user = auth_service.authenticate_google_user(db, body.credential)
    except ValueError as exc:
        # Invalid token — do not expose the internal error message.
        logger.warning("Google authentication rejected: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google credential",
        )

    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            profile_picture=user.profile_picture,
        )
    )
