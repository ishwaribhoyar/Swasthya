"""
Clinical Engine API router.

Endpoints:
  POST /clinical/patients/{patient_id}/analyze — Run clinical analysis
  GET  /clinical/patients/{patient_id}/overview — Clinical overview
  GET  /clinical/patients/{patient_id}/labs — List lab results
  GET  /clinical/patients/{patient_id}/vitals — List vitals history
  GET  /clinical/patients/{patient_id}/organ-scores — 8-Organ health scores
  GET  /clinical/patients/{patient_id}/alerts — Active severity alerts
  POST /clinical/alerts/{alert_id}/acknowledge — Acknowledge alert
"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.modules.clinical_engine.schema import (
    ClinicalAlertRead,
    ClinicalOverviewRead,
    LabResultRead,
    OrganScoreRead,
    VitalSignRead,
)
from app.modules.clinical_engine.service import ClinicalService
from app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/clinical", tags=["Clinical Intelligence Engine"])


def _req_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


@router.post(
    "/patients/{patient_id}/analyze",
    response_model=APIResponse[ClinicalOverviewRead],
    summary="Trigger clinical intelligence analysis over ingested documents",
)
async def analyze_patient(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ClinicalOverviewRead]:
    """Run lab extraction, vital signs parsing, 8-organ system scoring, and severity alert generation."""
    service = ClinicalService(db)
    clinician_id = str(current_user["sub"])
    overview = await service.analyze_patient(patient_id, clinician_id)
    return APIResponse(
        success=True,
        message="Clinical analysis completed.",
        data=overview,
        request_id=_req_id(request),
    )


@router.get(
    "/patients/{patient_id}/overview",
    response_model=APIResponse[ClinicalOverviewRead],
    summary="Get clinical overview (Organ scores, Alerts, Latest Labs & Vitals)",
)
async def get_overview(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ClinicalOverviewRead]:
    """Get comprehensive clinical summary."""
    service = ClinicalService(db)
    clinician_id = str(current_user["sub"])
    overview = await service.get_clinical_overview(patient_id, clinician_id)
    return APIResponse(
        success=True,
        message="Clinical overview retrieved.",
        data=overview,
        request_id=_req_id(request),
    )


@router.get(
    "/patients/{patient_id}/labs",
    response_model=APIResponse[List[LabResultRead]],
    summary="List structured laboratory test results",
)
async def list_labs(
    request: Request,
    patient_id: str,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter status (NORMAL, HIGH, LOW, CRITICAL_HIGH)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[LabResultRead]]:
    """List LOINC-aligned lab test results."""
    service = ClinicalService(db)
    clinician_id = str(current_user["sub"])
    labs = await service.list_labs(patient_id, clinician_id, status=status_filter)
    return APIResponse(
        success=True,
        message="Lab results retrieved.",
        data=labs,
        request_id=_req_id(request),
    )


@router.get(
    "/patients/{patient_id}/vitals",
    response_model=APIResponse[List[VitalSignRead]],
    summary="List vital signs history",
)
async def list_vitals(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[VitalSignRead]]:
    """List vital sign observations."""
    service = ClinicalService(db)
    clinician_id = str(current_user["sub"])
    vitals = await service.list_vitals(patient_id, clinician_id)
    return APIResponse(
        success=True,
        message="Vital signs retrieved.",
        data=vitals,
        request_id=_req_id(request),
    )


@router.get(
    "/patients/{patient_id}/organ-scores",
    response_model=APIResponse[List[OrganScoreRead]],
    summary="Get 8-organ system health scores",
)
async def get_organ_scores(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[OrganScoreRead]]:
    """Fetch 8-organ system health scores (0-100%)."""
    service = ClinicalService(db)
    clinician_id = str(current_user["sub"])
    scores = await service.get_organ_scores(patient_id, clinician_id)
    return APIResponse(
        success=True,
        message="Organ scores retrieved.",
        data=scores,
        request_id=_req_id(request),
    )


@router.get(
    "/patients/{patient_id}/alerts",
    response_model=APIResponse[List[ClinicalAlertRead]],
    summary="List active clinical severity alerts",
)
async def list_alerts(
    request: Request,
    patient_id: str,
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MODERATE)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[ClinicalAlertRead]]:
    """List clinical alerts for patient."""
    service = ClinicalService(db)
    clinician_id = str(current_user["sub"])
    alerts = await service.list_alerts(patient_id, clinician_id, severity=severity)
    return APIResponse(
        success=True,
        message="Clinical alerts retrieved.",
        data=alerts,
        request_id=_req_id(request),
    )


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=APIResponse[ClinicalAlertRead],
    summary="Mark clinical alert as acknowledged",
)
async def acknowledge_alert(
    request: Request,
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ClinicalAlertRead]:
    """Acknowledge a clinical alert."""
    service = ClinicalService(db)
    clinician_id = str(current_user["sub"])
    alert = await service.acknowledge_alert(alert_id, clinician_id)
    return APIResponse(
        success=True,
        message="Alert acknowledged.",
        data=alert,
        request_id=_req_id(request),
    )
