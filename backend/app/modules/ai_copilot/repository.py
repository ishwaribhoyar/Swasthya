"""
AI Copilot Repository — persistence for AI query audit logs.
"""
from __future__ import annotations

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_copilot.model import AIChatLog


class AICopilotRepository:
    """Repository for AI Copilot audit logs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log_query(self, log: AIChatLog) -> AIChatLog:
        """Persist AI query execution log and audit hash."""
        self._session.add(log)
        await self._session.commit()
        await self._session.refresh(log)
        return log

    async def list_chat_history(
        self, patient_id: str, clinician_id: str, limit: int = 20
    ) -> Sequence[AIChatLog]:
        """Fetch chat history for patient owned by clinician."""
        stmt = (
            select(AIChatLog)
            .where(
                AIChatLog.patient_id == patient_id,
                AIChatLog.clinician_id == clinician_id,
            )
            .order_by(AIChatLog.created_at.desc())
            .limit(limit)
        )
        res = await self._session.execute(stmt)
        return res.scalars().all()
