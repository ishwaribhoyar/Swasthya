"""
SQLAlchemy ORM model for AI Copilot audit logs & chat history.
"""
from __future__ import annotations

from typing import Optional
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class AIChatLog(Base, TimestampMixin):
    """ORM model storing full clinical AI query execution logs, citations, and audit hashes."""

    __tablename__ = "ai_chat_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    clinician_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)

    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.95)
    sources_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    audit_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
