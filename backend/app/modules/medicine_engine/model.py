"""
SQLAlchemy model for the medicine_engine module.
"""
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from app.database.base import Base

class Medicine_engineModel(Base):
    """Database model."""
    __tablename__ = "medicine_engine_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
