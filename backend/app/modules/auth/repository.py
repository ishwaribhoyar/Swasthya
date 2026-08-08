"""
Auth repository.

All database access for the auth module goes through this class.
No raw SQL queries outside the repository.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.model import User


class AuthRepository:
    """
    Data-access layer for User records.

    Methods operate on the SQLite users table via SQLAlchemy async ORM.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """
        Return the User with the given email, or None if not found.

        Args:
            email: The email address to look up (case-sensitive).
        """
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        """
        Return the User with the given UUID primary key, or None.

        Args:
            user_id: UUID string.
        """
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        email: str,
        first_name: str,
        last_name: str,
        password_hash: str,
    ) -> User:
        """
        Insert a new User row and return the persisted object.

        Args:
            email:         Unique email.
            first_name:    Given name.
            last_name:     Family name.
            password_hash: Pre-hashed password (bcrypt).

        Returns:
            The newly created User with all database-generated fields populated.
        """
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def update(self, user: User, updates: dict) -> User:
        """Apply updates to a User record."""
        for field, value in updates.items():
            if value is not None and hasattr(user, field):
                setattr(user, field, value)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def email_exists(self, email: str) -> bool:
        """Return True if any User row has the given email."""
        result = await self._session.execute(
            select(User.id).where(User.email == email)
        )
        return result.first() is not None
