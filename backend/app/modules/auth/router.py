"""
Auth API router.

Endpoints:
  POST  /auth/register  — Create new clinician account
  POST  /auth/login     — Authenticate and receive JWT pair
  GET   /auth/me        — Return authenticated user's profile
  PATCH /auth/me        — Update clinician profile (hospital, department, name)
  POST  /auth/refresh   — Exchange refresh token for new access token
  POST  /auth/logout    — Client-side logout (stateless)

All routes wrap response data in standard APIResponse envelope.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.modules.auth.schema import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
    UserUpdate,
)
from app.modules.auth.service import AuthService
from app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _req_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


@router.post(
    "/register",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new clinician account",
    responses={
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Create a new clinician account and return JWT token pair."""
    service = AuthService(db)
    res = await service.register(body)
    return APIResponse(
        success=True,
        message="Clinician account created successfully.",
        data=res,
        request_id=_req_id(request),
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="Authenticate and receive JWT tokens",
    responses={
        401: {"description": "Invalid credentials"},
    },
)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Authenticate with email + password."""
    service = AuthService(db)
    res = await service.login(body)
    return APIResponse(
        success=True,
        message="Authentication successful.",
        data=res,
        request_id=_req_id(request),
    )


@router.get(
    "/me",
    response_model=APIResponse[UserRead],
    summary="Get authenticated clinician profile",
)
async def get_me(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserRead]:
    """Return profile of the currently authenticated clinician."""
    service = AuthService(db)
    res = await service.get_me(str(current_user["sub"]))
    return APIResponse(
        success=True,
        message="Profile retrieved.",
        data=res,
        request_id=_req_id(request),
    )


@router.patch(
    "/me",
    response_model=APIResponse[UserRead],
    summary="Update clinician profile",
)
async def update_me(
    request: Request,
    body: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserRead]:
    """Update clinician profile attributes."""
    service = AuthService(db)
    res = await service.update_profile(str(current_user["sub"]), body)
    return APIResponse(
        success=True,
        message="Profile updated successfully.",
        data=res,
        request_id=_req_id(request),
    )


@router.post(
    "/refresh",
    response_model=APIResponse[AccessTokenResponse],
    summary="Exchange refresh token for new access token",
)
async def refresh_token(
    request: Request,
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AccessTokenResponse]:
    """Exchange refresh token for new access token."""
    service = AuthService(db)
    res = await service.refresh(body.refresh_token)
    return APIResponse(
        success=True,
        message="Access token refreshed.",
        data=res,
        request_id=_req_id(request),
    )


@router.post("/logout", summary="Log out current session")
async def logout(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> APIResponse[None]:
    """Server-side logout acknowledgement. Client must clear tokens."""
    return APIResponse(success=True, message="Logged out successfully.", data=None)
