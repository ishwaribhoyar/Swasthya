"""
Main API router aggregating all module routers and registering domain models.
"""
from __future__ import annotations
from fastapi import APIRouter

# Explicitly import all SQLAlchemy ORM models so Base.metadata is fully populated
from app.modules.auth.model import User  # noqa: F401
from app.modules.patients.model import Patient  # noqa: F401
from app.modules.ingestion.model import Document, UploadJob, ProcessingLog  # noqa: F401
from app.modules.clinical_engine.model import LabResult, VitalSign, OrganScore, ClinicalAlert  # noqa: F401
from app.modules.ai_copilot.model import AIChatLog  # noqa: F401
from app.modules.timeline.model import TimelineEvent  # noqa: F401
from app.modules.analytics.model import ParameterHistory  # noqa: F401
from app.modules.medicine_engine.prescription_model import Prescription, PrescriptionMedicine  # noqa: F401

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
