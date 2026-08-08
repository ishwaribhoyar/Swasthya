"""
Auth service — business logic layer.

All authentication decisions live here. The router delegates to this class;
the repository handles all database access.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError, NotFoundError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from app.modules.auth.model import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schema import (
    AccessTokenResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
    UserUpdate,
)
from app.observability.logger import get_logger

_log = get_logger(__name__)


class AuthService:
    """
    Authentication business logic.

    Raises:
        ConflictError:    When email already exists (register).
        UnauthorizedError: When credentials are wrong or token is invalid.
        NotFoundError:    When a user ID from a valid token no longer exists.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo     = AuthRepository(session)
        self._settings = get_settings()

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _build_token_response(self, user: User) -> TokenResponse:
        """Create access + refresh tokens for a clinician and package with UserRead."""
        payload = {"sub": user.id, "email": user.email}
        return TokenResponse(
            access_token=create_access_token(payload, self._settings.SECRET_KEY),
            refresh_token=create_refresh_token(payload, self._settings.SECRET_KEY),
            user=UserRead.model_validate(user),
        )

    # ─── Public Methods ───────────────────────────────────────────────────────

    async def register(self, data: RegisterRequest) -> TokenResponse:
        """
        Register a new clinician account.

        Steps:
          1. Check that no existing account uses the same email.
          2. Hash the password with bcrypt.
          3. Persist the User row.
          4. Return a full token response so the clinician is immediately logged in.

        Raises:
            ConflictError: If email already registered.
        """
        if await self._repo.email_exists(data.email):
            raise ConflictError(f"An account with email '{data.email}' already exists.")

        user = await self._repo.create(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            password_hash=get_password_hash(data.password),
        )
        _log.info("user_registered", user_id=user.id, email=user.email)
        return self._build_token_response(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """
        Authenticate a clinician with email + password.

        Steps:
          1. Look up the user by email.
          2. Verify the password against the stored bcrypt hash.
          3. Confirm the account is active.
          4. Return a full token response.

        Raises:
            UnauthorizedError: If email not found, password wrong, or account inactive.
        """
        user = await self._repo.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")
        if not user.is_active:
            raise UnauthorizedError("This account has been deactivated.")

        _log.info("user_login", user_id=user.id)
        return self._build_token_response(user)

    async def get_me(self, user_id: str) -> UserRead:
        """
        Return the profile for an authenticated clinician.

        Args:
            user_id: Extracted from the validated JWT 'sub' claim.

        Raises:
            NotFoundError: If the user ID from the token no longer exists in the DB.
        """
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User account no longer exists.")
        return UserRead.model_validate(user)

    async def update_profile(self, user_id: str, data: UserUpdate) -> UserRead:
        """
        Update profile details (hospital, department, name).
        """
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User account no longer exists.")

        updates = data.model_dump(exclude_unset=True)
        updated = await self._repo.update(user, updates)
        _log.info("user_profile_updated", user_id=user_id)
        return UserRead.model_validate(updated)

    async def refresh(self, refresh_token: str) -> AccessTokenResponse:
        """
        Exchange a valid refresh token for a new access token.

        Raises:
            UnauthorizedError: If the refresh token is invalid, expired, or user gone.
        """
        from jose import JWTError

        try:
            payload = decode_refresh_token(refresh_token, self._settings.SECRET_KEY)
        except (JWTError, ValueError) as exc:
            raise UnauthorizedError("Refresh token is invalid or expired.") from exc

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Refresh token missing subject claim.")

        user = await self._repo.get_by_id(str(user_id))
        if user is None or not user.is_active:
            raise UnauthorizedError("User account no longer exists or is inactive.")

        new_access = create_access_token(
            {"sub": user.id, "email": user.email},
            self._settings.SECRET_KEY,
        )
        return AccessTokenResponse(access_token=new_access)
