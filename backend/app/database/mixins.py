"""
Additional SQLAlchemy mixins.
"""
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, String

class SoftDeleteMixin:
    """Mixin for soft deletion support."""
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

class AuditMixin:
    """Mixin for tracking who created or updated a record."""
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String, nullable=True)
