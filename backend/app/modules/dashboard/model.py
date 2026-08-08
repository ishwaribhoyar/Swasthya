"""
SQLAlchemy model for the dashboard module.
"""
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from app.database.base import Base

class DashboardModel(Base):
    """Database model."""
    __tablename__ = "dashboard_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
