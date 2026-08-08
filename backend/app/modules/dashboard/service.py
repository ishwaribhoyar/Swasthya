"""
Dashboard Service — real aggregated statistics from SQLite.
All queries are scoped to the authenticated clinician.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Dict

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.model import Patient
from app.modules.ingestion.model import Document
from app.modules.clinical_engine.model import ClinicalAlert
from app.observability.logger import get_logger

_log = get_logger(__name__)


class DashboardService:
    """Service aggregating real-time clinical statistics for the dashboard."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_overview(self, clinician_id: str) -> Dict:
        """
        Return aggregated dashboard statistics for the authenticated clinician.
        All counts come directly from SQLite — no hardcoded values.
        """
        # 1. Patient counts
        total_patients_res = await self._session.execute(
            select(func.count()).select_from(Patient).where(Patient.clinician_id == clinician_id)
        )
        total_patients = total_patients_res.scalar_one()

        active_patients_res = await self._session.execute(
            select(func.count()).select_from(Patient).where(
                Patient.clinician_id == clinician_id,
                Patient.is_active == True,
            )
        )
        active_patients = active_patients_res.scalar_one()

        # 2. Documents processed
        docs_res = await self._session.execute(
            select(func.count()).select_from(Document).where(
                Document.clinician_id == clinician_id,
                Document.status == "completed",
            )
        )
        documents_processed = docs_res.scalar_one()

        # 3. Critical alerts (unacknowledged)
        alerts_res = await self._session.execute(
            select(func.count()).select_from(ClinicalAlert).where(
                ClinicalAlert.clinician_id == clinician_id,
                ClinicalAlert.severity == "CRITICAL",
                ClinicalAlert.is_acknowledged == False,
            )
        )
        critical_alerts = alerts_res.scalar_one()

        # 4. Patients registered this calendar month
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_res = await self._session.execute(
            select(func.count()).select_from(Patient).where(
                Patient.clinician_id == clinician_id,
                Patient.created_at >= month_start,
            )
        )
        new_this_month = month_res.scalar_one()

        _log.info(
            "DASHBOARD.OVERVIEW",
            clinician_id=clinician_id,
            total_patients=total_patients,
            documents_processed=documents_processed,
            critical_alerts=critical_alerts,
            new_this_month=new_this_month,
        )

        return {
            "total_patients": total_patients,
            "active_patients": active_patients,
            "documents_processed": documents_processed,
            "critical_alerts": critical_alerts,
            "new_this_month": new_this_month,
        }

    async def get_admissions_trend(self, clinician_id: str, days: int = 30) -> List[Dict]:
        """
        Return daily patient registration counts for the last `days` days.
        Returns a list of {date: 'YYYY-MM-DD', count: int} dicts.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self._session.execute(
            select(Patient.created_at).where(
                Patient.clinician_id == clinician_id,
                Patient.created_at >= cutoff,
            ).order_by(Patient.created_at.asc())
        )
        rows = result.scalars().all()

        # Group by date
        counts: Dict[str, int] = {}
        for ts in rows:
            if ts:
                d = ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)[:10]
                counts[d] = counts.get(d, 0) + 1

        # Build full date range (fill missing days with 0)
        trend = []
        for i in range(days):
            day = (datetime.now(timezone.utc) - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
            trend.append({"date": day, "count": counts.get(day, 0)})

        return trend

    async def get_document_category_distribution(self, clinician_id: str) -> List[Dict]:
        """
        Return document counts grouped by category for donut chart.
        """
        result = await self._session.execute(
            select(Document.doc_category, func.count().label("count"))
            .where(
                Document.clinician_id == clinician_id,
                Document.status == "completed",
            )
            .group_by(Document.doc_category)
        )
        rows = result.all()

        CATEGORY_COLORS = {
            "lab": "#1D6FA4",
            "prescription": "#2E9B6B",
            "vitals": "#E9A835",
            "summary": "#9B5DE5",
            "note": "#F15BB5",
        }

        return [
            {
                "name": (row[0] or "other").title(),
                "value": row[1],
                "color": CATEGORY_COLORS.get(row[0] or "other", "#94A3B8"),
            }
            for row in rows
        ]
