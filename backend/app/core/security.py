"""
Security utilities: password hashing and JWT token operations.

Uses bcrypt directly for password hashing (Python 3.14 safe).
All token operations use the application SECRET_KEY from settings.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config.jwt import (
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
)


# ─── Password Hashing ─────────────────────────────────────────────────────────

def get_password_hash(password: str) -> str:
    """Return a bcrypt hash of the given password string."""
    pwd_bytes = password.encode("utf-8")[:72]  # bcrypt 72 byte limit
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plain password matches the stored bcrypt hash."""
    pwd_bytes = plain_password.encode("utf-8")[:72]
    hash_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


# ─── Token Creation ───────────────────────────────────────────────────────────

def create_access_token(data: dict[str, Any], secret_key: str) -> str:
    """
    Create a signed JWT access token.

    Args:
        data:       Payload dict. Must include 'sub' (subject = user id as str).
        secret_key: Application secret key from settings.

    Returns:
        Signed JWT string.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any], secret_key: str) -> str:
    """
    Create a signed JWT refresh token with a longer expiry.

    Args:
        data:       Payload dict. Must include 'sub'.
        secret_key: Application secret key from settings.

    Returns:
        Signed JWT string.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire, "type": "refresh"})
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Args:
        token:      The raw JWT string.
        secret_key: Application secret key.

    Returns:
        Decoded payload dict.

    Raises:
        JWTError: If the token is expired, malformed, or signature-invalid.
    """
    return jwt.decode(token, secret_key, algorithms=[ALGORITHM])


def decode_refresh_token(token: str, secret_key: str) -> dict[str, Any]:
    """
    Decode and validate a JWT refresh token.

    Raises:
        JWTError: On any validation failure.
        ValueError: If the token type claim is not 'refresh'.
    """
    payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    if payload.get("type") != "refresh":
        raise ValueError("Token is not a refresh token.")
    return payload
