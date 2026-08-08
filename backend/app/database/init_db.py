"""
Database initialization logic.
Ensures all domain models are imported so SQLAlchemy Base metadata holds all tables.
Handles automatic column migrations for SQLite.
"""
from __future__ import annotations

from sqlalchemy import text
from app.database.session import engine
from app.database.base import Base

# Import all SQLAlchemy models to register them with Base.metadata
from app.modules.auth.model import User  # noqa: F401
from app.modules.patients.model import Patient  # noqa: F401
from app.modules.ingestion.model import Document, UploadJob, ProcessingLog  # noqa: F401
from app.modules.clinical_engine.model import LabResult, VitalSign, OrganScore, ClinicalAlert  # noqa: F401
from app.modules.ai_copilot.model import AIChatLog  # noqa: F401
from app.modules.timeline.model import TimelineEvent  # noqa: F401
from app.modules.analytics.model import ParameterHistory  # noqa: F401
from app.modules.medicine_engine.prescription_model import Prescription, PrescriptionMedicine  # noqa: F401



async def init_db() -> None:
    """Create all tables in SQLite if they don't exist and auto-migrate missing columns."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # SQLite schema auto-migrations for development
        migrations = [
            "ALTER TABLE patients ADD COLUMN clinician_id VARCHAR(36)",
            "ALTER TABLE patients ADD COLUMN blood_group VARCHAR(10)",
            "ALTER TABLE patients ADD COLUMN emergency_contact_name VARCHAR(100)",
            "ALTER TABLE patients ADD COLUMN emergency_contact_phone VARCHAR(30)",
            "ALTER TABLE patients ADD COLUMN allergies TEXT",
            "ALTER TABLE patients ADD COLUMN chronic_conditions TEXT",
            "ALTER TABLE patients ADD COLUMN notes TEXT",
            "ALTER TABLE patients ADD COLUMN archived_at DATETIME",
            "ALTER TABLE documents ADD COLUMN document_date DATETIME",
            "ALTER TABLE documents ADD COLUMN extracted_markdown TEXT",
        ]

        for m in migrations:
            try:
                await conn.execute(text(m))
            except Exception:
                pass  # Ignore if column already exists
