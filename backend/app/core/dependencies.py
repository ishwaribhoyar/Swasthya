"""
FastAPI dependency injectors for ClinIQ.

These functions are used with FastAPI's Depends() system to inject
shared resources — database sessions, configuration, and the
authenticated clinician — into route handlers.

Authentication dependency (get_current_user):
- Reads the Authorization: Bearer <token> header.
- Validates the JWT signature and expiry using the application secret key.
- Raises HTTP 401 Unauthorized for any missing, malformed, or expired token.
- Returns the decoded token payload as a typed dict.

Every authenticated user is a Clinician. No role hierarchies or RBAC exist.
"""
from __future__ import annotations

from typing import AsyncGenerator, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import get_settings, Settings
from app.database.session import get_db_session

# ─── HTTP Bearer scheme ───────────────────────────────────────────────────────

_bearer_scheme = HTTPBearer(auto_error=False)


# ─── Database ─────────────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async SQLAlchemy session for the current request.

    The session is committed on success and rolled back on exception.
    Always closed after the request completes.
    """
    async for session in get_db_session():
        yield session


# ─── Settings ─────────────────────────────────────────────────────────────────

def get_app_settings() -> Settings:
    """Return the application settings singleton."""
    return get_settings()


# ─── Authentication ───────────────────────────────────────────────────────────

async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, object]:
    """
    Validate the Bearer JWT and return the decoded payload.

    Raises:
        HTTP 401 Unauthorized — if the Authorization header is absent.
        HTTP 401 Unauthorized — if the token is malformed or expired.
        HTTP 401 Unauthorized — if the token signature is invalid.

    Returns:
        dict containing at minimum: sub (user id), email.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.core.security import decode_access_token  # local import avoids circular dep
    from jose import JWTError

    try:
        payload = decode_access_token(credentials.credentials, settings.SECRET_KEY)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing the subject claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


# ─── Type aliases for injection ───────────────────────────────────────────────

CurrentUser  = Annotated[dict[str, object], Depends(get_current_user)]
DbSession    = Annotated[AsyncSession,       Depends(get_db)]
AppSettings  = Annotated[Settings,           Depends(get_app_settings)]
