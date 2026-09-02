"""
FinSight AI — Authentication Dependencies

Supports:
- Local development with mock authentication
- Supabase JWT authentication in production
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError, jwt
from loguru import logger
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env", override=True)


security = HTTPBearer(
    auto_error=True
)


SUPABASE_JWT_SECRET = os.getenv(
    "SUPABASE_JWT_SECRET",
    "",
).strip()

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development",
).lower()

# Never enable mock auth in production, even if MOCK_AUTH is missing or true.
if ENVIRONMENT == "production":
    MOCK_AUTH_ENABLED = False
else:
    MOCK_AUTH_ENABLED = (
        os.getenv(
            "MOCK_AUTH",
            "true",
        ).lower()
        == "true"
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
) -> str:
    """
    Resolve the authenticated user ID.

    Development:
        Bearer mock_jwt_token
        -> "default"

    Production:
        Supabase JWT
        -> JWT 'sub'
    """

    token = (
        credentials.credentials.strip()
    )

    # ========================================================
    # Local development mock authentication
    # ========================================================

    if (
        ENVIRONMENT == "development"
        and MOCK_AUTH_ENABLED
        and token == "mock_jwt_token"
    ):
        logger.warning(
            "⚠️ Using local mock authentication "
            "(user_id='default')."
        )

        return "default"

    # ========================================================
    # Production configuration validation
    # ========================================================

    if not SUPABASE_JWT_SECRET:

        logger.error(
            "SUPABASE_JWT_SECRET is not configured."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Authentication is not configured "
                "on the server."
            ),
        )

    # ========================================================
    # Decode Supabase JWT
    # ========================================================

    try:

        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={
                "verify_aud": False,
            },
        )

        user_id = payload.get(
            "sub"
        )

        if not user_id:

            logger.warning(
                "JWT does not contain a valid 'sub' claim."
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Invalid authentication credentials."
                ),
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )

        return str(user_id)

    except JWTError as exc:

        logger.warning(
            f"JWT validation failed: {exc}"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Invalid authentication credentials."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> str | None:
    """
    Optional authentication dependency.

    Useful for endpoints that should work for both
    authenticated and unauthenticated users.
    """

    if credentials is None:
        return None

    try:

        return await get_current_user(
            credentials
        )

    except HTTPException:

        return None