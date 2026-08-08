"""
Auth module Pydantic schemas.

Input schemas validate and document what the API accepts.
Output schemas control exactly what is returned — password hashes
are never included in any response.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ─── Input Schemas ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Body for POST /auth/register."""

    first_name: str = Field(
        ..., min_length=1, max_length=100, description="Clinician's given name"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=100, description="Clinician's family name"
    )
    email: EmailStr = Field(..., description="Unique email address used for login")
    password: str = Field(
        ..., min_length=8, max_length=128,
        description="Password (min 8 chars). Stored as bcrypt hash."
    )


class LoginRequest(BaseModel):
    """Body for POST /auth/login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    """Body for POST /auth/refresh."""

    refresh_token: str = Field(..., description="A valid, unexpired refresh JWT")


class UserUpdate(BaseModel):
    """Body for PATCH /auth/me — profile update."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name:  Optional[str] = Field(None, min_length=1, max_length=100)
    hospital:   Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=255)


# ─── Output Schemas ───────────────────────────────────────────────────────────

class UserRead(BaseModel):
    """
    Safe user representation returned to clients.
    password_hash is deliberately excluded.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    first_name: str
    last_name: str
    hospital: Optional[str] = None
    department: Optional[str] = None
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Returned on successful login or register."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead


class AccessTokenResponse(BaseModel):
    """Returned on token refresh."""

    access_token: str
    token_type: str = "bearer"
