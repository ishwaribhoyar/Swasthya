"""
Dashboard API router — real statistics from SQLite.

Endpoints:
  GET /dashboard/overview            — 4 key metrics for stat cards
  GET /dashboard/admissions-trend    — daily patient registrations (last 30 days)
  GET /dashboard/document-categories — document category distribution
"""
from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.modules.dashboard.service import DashboardService
from app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=APIResponse[Dict])
async def get_overview(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Dict]:
    """Return total_patients, documents_processed, critical_alerts for dashboard stat cards."""
    svc = DashboardService(db)
    data = await svc.get_overview(str(current_user["sub"]))
    return APIResponse(success=True, message="Dashboard overview retrieved.", data=data)


@router.get("/admissions-trend", response_model=APIResponse[List[Dict]])
async def get_admissions_trend(
    request: Request,
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[Dict]]:
    """Return daily patient registration counts for the last N days."""
    svc = DashboardService(db)
    trend = await svc.get_admissions_trend(str(current_user["sub"]), days=days)
    return APIResponse(success=True, message="Admissions trend retrieved.", data=trend)


@router.get("/document-categories", response_model=APIResponse[List[Dict]])
async def get_document_categories(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[Dict]]:
    """Return document counts by category for donut chart."""
    svc = DashboardService(db)
    cats = await svc.get_document_category_distribution(str(current_user["sub"]))
    return APIResponse(success=True, message="Document categories retrieved.", data=cats)
