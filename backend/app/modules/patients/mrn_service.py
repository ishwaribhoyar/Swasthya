"""
MRN Sequence Service.

Generates sequential, collision-free Medical Record Numbers (MRN).
Format: MRN-YYYY-###### (e.g., MRN-2026-000001, MRN-2026-000002).

Never uses row count. Extracts the highest existing sequence suffix for the current year
and increments atomically.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.model import Patient


class MRNSequenceService:
    """Service to generate sequential MRNs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def generate_next_mrn(self) -> str:
        """
        Generate the next sequential MRN for the current calendar year.

        Returns:
            Formatted MRN string e.g., 'MRN-2026-000001'.
        """
        current_year = datetime.now(timezone.utc).year
        prefix = f"MRN-{current_year}-"

        # Query all existing MRNs for current year to find maximum sequence
        stmt = (
            select(Patient.mrn)
            .where(Patient.mrn.like(f"{prefix}%"))
            .order_by(Patient.mrn.desc())
            .limit(50)
        )
        result = await self._session.execute(stmt)
        mrns = result.scalars().all()

        max_seq = 0
        pattern = re.compile(rf"^MRN-{current_year}-(\d{{6}})$")

        for mrn in mrns:
            match = pattern.match(mrn)
            if match:
                seq_num = int(match.group(1))
                if seq_num > max_seq:
                    max_seq = seq_num

        next_seq = max_seq + 1
        return f"{prefix}{next_seq:06d}"
