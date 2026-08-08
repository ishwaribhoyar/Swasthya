"""
Ingestion repository — SQLAlchemy database access for upload jobs, documents, and processing logs.
All queries enforce multi-tenant isolation by clinician_id and patient_id.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence, Optional

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.model import UploadJob, Document, ProcessingLog


from app.modules.patients.model import Patient


class IngestionRepository:
    """Data-access layer for Document Ingestion."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ─── UploadJob Methods ───────────────────────────────────────────────────

    async def create_upload_job(self, job: UploadJob) -> UploadJob:
        self._session.add(job)
        await self._session.commit()
        await self._session.refresh(job)
        return job

    async def get_upload_job(self, job_id: str, clinician_id: str) -> UploadJob | None:
        stmt = select(UploadJob).where(
            UploadJob.id == job_id,
            UploadJob.clinician_id == clinician_id,
        )
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def update_upload_job(self, job: UploadJob) -> UploadJob:
        await self._session.commit()
        await self._session.refresh(job)
        return job

    # ─── Document Methods ────────────────────────────────────────────────────

    async def create_document(self, doc: Document) -> Document:
        self._session.add(doc)
        await self._session.commit()
        await self._session.refresh(doc)
        return doc

    async def get_document_by_id(self, doc_id: str, clinician_id: str) -> Document | None:
        stmt = (
            select(Document)
            .join(Patient, Document.patient_id == Patient.id)
            .where(
                Document.id == doc_id,
                or_(Document.clinician_id == clinician_id, Patient.clinician_id == clinician_id),
            )
        )
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_sha256(self, patient_id: str, sha256_hash: str) -> Document | None:
        """Find an existing completed or processing document with exact same SHA256 hash for patient."""
        stmt = select(Document).where(
            Document.patient_id == patient_id,
            Document.sha256_hash == sha256_hash,
            Document.status.in_(["completed", "processing", "duplicate"]),
        ).order_by(Document.created_at.asc())
        res = await self._session.execute(stmt)
        return res.scalars().first()

    async def list_documents_for_patient(
        self,
        patient_id: str,
        clinician_id: str,
        *,
        search: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "newest",
    ) -> Sequence[Document]:
        """List documents owned by clinician for patient."""
        query = select(Document).where(
            Document.patient_id == patient_id,
            Document.clinician_id == clinician_id,
        )

        if category:
            query = query.where(Document.doc_category == category)

        if status:
            query = query.where(Document.status == status)

        if search:
            term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(Document.original_filename).like(term),
                    func.lower(Document.extracted_text).like(term),
                )
            )

        if sort_by == "oldest":
            query = query.order_by(Document.created_at.asc())
        elif sort_by == "filename":
            query = query.order_by(Document.original_filename.asc())
        elif sort_by == "processing_time":
            query = query.order_by(Document.processing_time_ms.desc())
        else:
            query = query.order_by(Document.created_at.desc())

        res = await self._session.execute(query)
        return res.scalars().all()

    async def update_document(self, doc: Document) -> Document:
        await self._session.commit()
        await self._session.refresh(doc)
        return doc

    async def delete_document(self, doc: Document) -> None:
        await self._session.delete(doc)
        await self._session.commit()

    # ─── ProcessingLog Methods ───────────────────────────────────────────────

    async def add_log(self, log: ProcessingLog) -> ProcessingLog:
        self._session.add(log)
        await self._session.commit()
        await self._session.refresh(log)
        return log

    async def get_logs_for_document(self, document_id: str) -> Sequence[ProcessingLog]:
        stmt = (
            select(ProcessingLog)
            .where(ProcessingLog.document_id == document_id)
            .order_by(ProcessingLog.timestamp.asc())
        )
        res = await self._session.execute(stmt)
        return res.scalars().all()
