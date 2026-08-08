"""
Main API router aggregating all module routers.
"""
from __future__ import annotations
from fastapi import APIRouter

# Import all module routers
from app.modules.auth.router import router as auth_router
from app.modules.patients.router import router as patients_router
from app.modules.ingestion.router import router as ingestion_router
from app.modules.document_intelligence.router import router as doc_intel_router
from app.modules.clinical_engine.router import router as clinical_router
from app.modules.medicine_engine.router import router as medicine_router
from app.modules.timeline.router import router as timeline_router
from app.modules.analytics.router import router as analytics_router
from app.modules.ai_copilot.router import router as copilot_router
from app.modules.dashboard.router import router as dashboard_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(patients_router)
api_router.include_router(ingestion_router)
api_router.include_router(doc_intel_router)
api_router.include_router(clinical_router)
api_router.include_router(medicine_router)
api_router.include_router(timeline_router)
api_router.include_router(analytics_router)
api_router.include_router(copilot_router)
api_router.include_router(dashboard_router)
