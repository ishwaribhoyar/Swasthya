"""
Analytics Service Engine — computes longitudinal trends & anomaly alerts across all tracked parameters.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.model import ParameterHistory
from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.schema import AnalyticsOverviewRead, ParameterTrendRead
from app.modules.analytics.trend_engine import TrendEngine
from app.observability.logger import get_logger

_log = get_logger(__name__)


class AnalyticsService:
    """Service compiling longitudinal trend analytics."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AnalyticsRepository(session)

    async def get_patient_analytics(
        self, patient_id: str, clinician_id: str, parameter_name: Optional[str] = None
    ) -> AnalyticsOverviewRead:
        """
        Compute longitudinal trend metrics for all tracked parameters of a patient.
        """
        records = await self._repo.list_patient_parameters(patient_id, clinician_id, parameter_name)

        # Group records by parameter name
        series_map: Dict[str, List[ParameterHistory]] = {}
        for r in records:
            p_key = r.parameter_name
            if p_key not in series_map:
                series_map[p_key] = []
            series_map[p_key].append(r)

        trends: List[ParameterTrendRead] = []
        critical_cnt = 0

        for p_name, p_items in series_map.items():
            t_res = TrendEngine.analyze_parameter_series(p_name, p_items)
            trend_schema = ParameterTrendRead.model_validate(t_res.to_dict())
            trends.append(trend_schema)
            if t_res.anomaly or t_res.risk_level == "CRITICAL":
                critical_cnt += 1

        _log.info(
            "ANALYTICS.TRENDS_LOADED",
            patient_id=patient_id,
            parameters_tracked=len(trends),
            critical_anomalies=critical_cnt,
        )

        return AnalyticsOverviewRead(
            patient_id=patient_id,
            total_parameters_tracked=len(trends),
            critical_anomalies_count=critical_cnt,
            parameter_trends=trends,
        )
