"""
app/schemas/auth.py

Pydantic schemas for authentication endpoints.
"""

import uuid

from pydantic import BaseModel, EmailStr, Field


class GoogleAuthRequest(BaseModel):
    """
    Request body for POST /api/v1/auth/google.

    The frontend sends the Google ID token (credential) received from
    Google Identity Services directly to this endpoint.
    The backend verifies it — never trust the frontend's claimed identity.
    """

    credential: str = Field(
        ...,
        description="Google ID token received from Google Identity Services",
        min_length=1,
    )


class UserResponse(BaseModel):
    """User information returned after successful authentication."""

    id: uuid.UUID
    email: str
    name: str
    profile_picture: str | None = None

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Response for POST /api/v1/auth/google."""

    user: UserResponse
