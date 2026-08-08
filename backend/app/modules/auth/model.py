"""
User SQLAlchemy model.

Represents a registered clinician. Passwords are stored as bcrypt hashes.
No plaintext credentials are ever persisted. All users are Clinicians.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    Clinician user account.

    Attributes:
        id:            UUID primary key.
        email:         Unique email address used for login.
        first_name:    Given name.
        last_name:     Family name.
        hospital:      Hospital / Clinic name (optional).
        department:    Department name (optional).
        password_hash: bcrypt hash of the user's password.
        is_active:     False for suspended/deleted accounts.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str]  = mapped_column(String(100), nullable=False)
    hospital: Mapped[Optional[str]]   = mapped_column(String(255))
    department: Mapped[Optional[str]] = mapped_column(String(255))
    password_hash: Mapped[str]        = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool]           = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
