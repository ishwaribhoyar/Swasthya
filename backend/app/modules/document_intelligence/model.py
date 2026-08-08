"""
SQLAlchemy model for the document_intelligence module.
"""
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from app.database.base import Base

class Document_intelligenceModel(Base):
    """Database model."""
    __tablename__ = "document_intelligence_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
