"""
app/core/security.py

Google ID token verification.

The backend MUST verify the Google ID token — never trust profile information
supplied by the browser without verification.

Validates:
  - Token signature (Google's public keys)
  - Issuer (accounts.google.com / https://accounts.google.com)
  - Audience (GOOGLE_CLIENT_ID)
  - Expiration

Reference: https://developers.google.com/identity/gsi/web/guides/verify-google-id-token
"""

import logging
from typing import Any

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config import settings

logger = logging.getLogger(__name__)


def verify_google_token(credential: str) -> dict[str, Any]:
    """
    Verify a Google ID token and return the decoded token payload.

    Args:
        credential: Raw Google ID token string from the frontend.

    Returns:
        Decoded token payload dict containing at minimum:
          - sub      (google_id — unique user identifier)
          - email
          - name
          - picture  (optional)

    Raises:
        ValueError: If the token is invalid, expired, wrong audience, etc.
    """
    try:
        payload: dict[str, Any] = id_token.verify_oauth2_token(
            id_token=credential,
            request=google_requests.Request(),
            audience=settings.GOOGLE_CLIENT_ID,
        )
    except Exception as exc:
        # Do NOT log the credential — it is a sensitive bearer token.
        logger.warning("Google ID token verification failed: %s", exc)
        raise ValueError("Invalid Google ID token") from exc

    logger.info(
        "Google ID token verified | google_id=%s | email=%s",
        payload.get("sub"),
        payload.get("email"),
    )
    return payload
