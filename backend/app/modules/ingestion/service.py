"""
Ingestion Service & UploadManager.

Orchestrates multi-document uploads, SHA256 deduplication, file storage, DocumentRouter parsing,
step-by-step pipeline logging, and batch summary metrics.
"""
from __future__ import annotations

import hashlib
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Optional, Sequence



from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.document_intelligence.document_router import DocumentRouter
from app.modules.ingestion.model import UploadJob, Document, ProcessingLog
from app.modules.ingestion.repository import IngestionRepository
from app.modules.ingestion.schema import (
    BatchUploadSummary,
    DocumentListItem,
    DocumentRead,
    ProcessingLogRead,
    UploadJobRead,
)
from app.observability.logger import get_logger

_log = get_logger(__name__)


class IngestionService:
    """Service layer controlling document ingestion and processing pipelines."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IngestionRepository(session)
        self._router = DocumentRouter()

    def _get_storage_dir(self, clinician_id: str, patient_id: str) -> Path:
        """Ensure storage directory exists under storage/uploads/{clinician_id}/{patient_id}/."""
        base_dir = Path("storage/uploads") / clinician_id / patient_id
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    def _to_doc_read(self, doc: Document) -> DocumentRead:
        """Convert Document ORM model to DocumentRead Pydantic schema."""
        from app.shared.utils.html_to_markdown import convert_html_to_markdown

        read_obj = DocumentRead.model_validate(doc)

        # Sanitize & convert HTML to clean Markdown
        clean_text = convert_html_to_markdown(read_obj.extracted_text or "")
        clean_md = convert_html_to_markdown(read_obj.extracted_markdown or read_obj.extracted_text or "")

        read_obj.extracted_text = clean_text or read_obj.extracted_text
        read_obj.extracted_markdown = clean_md or clean_text or read_obj.extracted_markdown
        read_obj.extracted_html = clean_md or clean_text or read_obj.extracted_html
        return read_obj



    def _to_doc_list_item(self, doc: Document) -> DocumentListItem:
        """Convert Document ORM model to DocumentListItem schema."""
        return DocumentListItem.model_validate(doc)

    async def _add_step_log(
        self, document_id: str, step_name: str, status: str, message: str, duration_ms: int = 0
    ) -> None:
        """Add pipeline execution log for visualization timeline."""
        log_entry = ProcessingLog(
            document_id=document_id,
            step_name=step_name,
            status=status,
            log_message=message,
            duration_ms=duration_ms,
        )
        await self._repo.add_log(log_entry)

    async def process_batch_upload(
        self,
        patient_id: str,
        clinician_id: str,
        files: List[UploadFile],
    ) -> BatchUploadSummary:
        """
        Process up to 10 uploaded files concurrently for patient_id.
        """
        if not files or len(files) == 0:
            raise ValidationError("At least one document file must be uploaded.")
        if len(files) > 10:
            raise ValidationError("Maximum 10 documents can be uploaded simultaneously per batch.")

        # Create UploadJob
        job = UploadJob(
            clinician_id=clinician_id,
            patient_id=patient_id,
            total_files=len(files),
            status="processing",
        )
        saved_job = await self._repo.create_upload_job(job)

        _log.info(
            "UPLOAD.STARTED",
            job_id=saved_job.id,
            patient_id=patient_id,
            clinician_id=clinician_id,
            file_count=len(files),
        )

        storage_dir = self._get_storage_dir(clinician_id, patient_id)
        processed_docs: List[Document] = []
        completed_cnt = 0
        duplicate_cnt = 0
        failed_cnt = 0

        # Allowed MIME types whitelist
        ALLOWED_MIME_TYPES = {
            "application/pdf",
            "image/jpeg",
            "image/jpg", 
            "image/png",
            "image/webp",
            "image/tiff",
            "text/plain",
            "text/markdown",
        }
        MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

        # Pre-validate all files before processing any
        for f in files:
            f_mime = (f.content_type or "").lower()
            f_name = (f.filename or "").lower()
            # Allow by extension as fallback for missing MIME
            ext_ok = any(f_name.endswith(ext) for ext in [".pdf", ".jpg", ".jpeg", ".png", ".webp", ".tiff", ".txt", ".md", ".text"])
            if f_mime not in ALLOWED_MIME_TYPES and not ext_ok:
                raise ValidationError(
                    f"File '{f.filename}' has unsupported type '{f_mime}'. "
                    "Only PDF, JPEG, PNG, WEBP, TIFF, TXT, and MD files are accepted."
                )
        MAGIC_SIGNATURES: dict[bytes, str] = {
            b"%PDF": "pdf",
            b"\xff\xd8\xff": "jpeg",
            b"\x89PNG\r\n\x1a\n": "png",
            b"RIFF": "webp",
            b"II*\x00": "tiff",
            b"MM\x00*": "tiff",
        }

        for f in files:
            f_name = (f.filename or "").lower()
            if f_name.endswith((".txt", ".md", ".text")) or (f.content_type and "text/" in f.content_type):
                continue

            try:
                header = await f.read(16)
                await f.seek(0)
            except Exception:
                header = b""

            if header:
                matched = False
                for sig, sig_type in MAGIC_SIGNATURES.items():
                    if header[:len(sig)] == sig:
                        if sig_type == "webp" and header[8:12] != b"WEBP":
                            continue
                        matched = True
                        break
                if not matched:
                    raise ValidationError(
                        f"File '{f.filename}' was rejected: file signature does not match "
                        "any allowed medical document format (PDF, JPEG, PNG, WEBP, TIFF, TXT, MD)."
                    )

        # We cannot check size until we read, so size check happens per-file below.

        for file in files:
            t0 = time.time()
            filename = file.filename or "medical_document.pdf"
            content = await file.read()
            mime_type = file.content_type or "application/octet-stream"
            file_size = len(content)

            if file_size > MAX_FILE_SIZE_BYTES:
                raise ValidationError(
                    f"File '{filename}' is {file_size // (1024*1024)}MB which exceeds the 20MB limit."
                )

            # 1. Create Document record
            doc = Document(
                patient_id=patient_id,
                clinician_id=clinician_id,
                upload_job_id=saved_job.id,
                original_filename=filename,
                file_type="pdf" if "pdf" in mime_type or filename.lower().endswith(".pdf") else "image",
                mime_type=mime_type,
                file_size_bytes=file_size,
                sha256_hash="",
                storage_path="",
                status="processing",
            )
            doc = await self._repo.create_document(doc)

            await self._add_step_log(doc.id, "upload", "completed", f"Received {filename} ({file_size} bytes)", int((time.time() - t0) * 1000))

            # 2. SHA256 Deduplication check
            t_sha = time.time()
            sha256_hash = DocumentRouter.compute_sha256(content)
            doc.sha256_hash = sha256_hash

            existing_duplicate = await self._repo.get_by_sha256(patient_id, sha256_hash)
            if existing_duplicate and existing_duplicate.id != doc.id:
                doc.status = "duplicate"
                doc.doc_category = existing_duplicate.doc_category
                doc.parse_source = existing_duplicate.parse_source
                doc.extracted_text = existing_duplicate.extracted_text
                doc.extracted_html = existing_duplicate.extracted_html
                doc.error_message = "Document already exists for patient (SHA256 duplicate)."
                doc.storage_path = existing_duplicate.storage_path
                await self._repo.update_document(doc)

                duplicate_cnt += 1
                await self._add_step_log(
                    doc.id, "sha256_check", "completed", "Duplicate hash detected — skipped parsing", int((time.time() - t_sha) * 1000)
                )
                processed_docs.append(doc)
                continue

            await self._add_step_log(doc.id, "sha256_check", "completed", f"SHA256 Verified: {sha256_hash[:16]}...", int((time.time() - t_sha) * 1000))

            # 3. Store file on disk
            ext = Path(filename).suffix or (".pdf" if doc.file_type == "pdf" else ".png")
            file_path = storage_dir / f"{doc.id}{ext}"
            with open(file_path, "wb") as f:
                f.write(content)
            doc.storage_path = str(file_path)

            # 4. Route document through parser
            t_route = time.time()
            await self._add_step_log(doc.id, "router", "started", "Routing document layout to parse engine...")

            try:
                result = await self._router.process_document(content, filename, mime_type)
                
                doc.file_type = "pdf" if result.file_type in ("digital_pdf", "scanned_pdf") else "txt" if result.file_type == "txt" else "image"

                doc.doc_category = result.doc_category
                doc.parse_source = result.parse_source
                doc.confidence_score = result.confidence_score
                doc.extracted_text = result.extracted_text
                doc.extracted_markdown = result.extracted_markdown or result.extracted_text
                doc.extracted_html = result.extracted_html
                doc.processing_time_ms = result.processing_time_ms
                doc.document_date = result.document_date
                doc.status = "completed"



                for step in result.steps:
                    await self._add_step_log(
                        doc.id,
                        step.step_name,
                        step.status,
                        step.message,
                        step.duration_ms,
                    )

                # Automatically reconstruct TimelineEvent & ParameterHistory
                try:
                    from app.modules.timeline.event_extractor import PriorityEventExtractor
                    from app.modules.timeline.model import TimelineEvent
                    from app.modules.analytics.model import ParameterHistory
                    import json

                    ev_data = PriorityEventExtractor.extract_priority_event(
                        filename=filename,
                        category=result.doc_category,
                        text=result.extracted_text or "",
                        upload_time=doc.created_at,
                    )
                    doc.document_date = ev_data.event_date

                    t_event = TimelineEvent(
                        patient_id=patient_id,
                        clinician_id=clinician_id,
                        record_id=doc.id,
                        event_date=ev_data.event_date,
                        date_priority_source=ev_data.date_priority_source,
                        event_type=ev_data.event_type,
                        document_type=filename.split(".")[-1].upper(),
                        title=ev_data.title,
                        summary=ev_data.summary,
                        confidence=ev_data.confidence,
                        entities_json=json.dumps(ev_data.entities),
                    )
                    self._session.add(t_event)

                    for p in ev_data.parameters:
                        p_rec = ParameterHistory(
                            patient_id=patient_id,
                            clinician_id=clinician_id,
                            record_id=doc.id,
                            parameter_name=p["parameter_name"],
                            normalized_name=p["normalized_name"],
                            value=p["value"],
                            value_str=p["value_str"],
                            unit=p["unit"],
                            reference_range=p["reference_range"],
                            status=p["status"],
                            event_date=ev_data.event_date,
                            confidence=ev_data.confidence,
                        )
                        self._session.add(p_rec)

                    await self._session.commit()
                except Exception as ex_t:
                    _log.warning("TIMELINE_EVENT.PERSIST_FAIL", error=str(ex_t))

                await self._add_step_log(doc.id, "persistence", "completed", "Persisted structured record & timeline event to SQLite")

                completed_cnt += 1

                _log.info(
                    "DOCUMENT.STORED",
                    document_id=doc.id,
                    patient_id=patient_id,
                    category=result.doc_category,
                    source=result.parse_source,
                )
            except Exception as exc:
                doc.status = "failed"
                doc.error_message = str(exc)
                failed_cnt += 1
                await self._add_step_log(doc.id, "parsing", "failed", f"Parse error: {str(exc)}")
                _log.error("UPLOAD.FAILED", document_id=doc.id, error=str(exc))

            await self._repo.update_document(doc)
            processed_docs.append(doc)

        # Update Job summary
        saved_job.completed_files = completed_cnt
        saved_job.duplicate_files = duplicate_cnt
        saved_job.failed_files = failed_cnt
        saved_job.status = "completed" if failed_cnt == 0 else "failed"
        saved_job.finished_at = datetime.now(timezone.utc)
        await self._repo.update_upload_job(saved_job)

        _log.info(
            "UPLOAD.COMPLETED",
            job_id=saved_job.id,
            completed=completed_cnt,
            duplicates=duplicate_cnt,
            failed=failed_cnt,
        )

        avg_confidence = (
            sum(d.confidence_score for d in processed_docs if d.status == "completed") / max(1, completed_cnt)
            if completed_cnt > 0
            else 1.0
        )
        total_time_ms = sum(d.processing_time_ms for d in processed_docs)

        return BatchUploadSummary(
            job_id=saved_job.id,
            total_files=len(files),
            completed_files=completed_cnt,
            duplicate_files=duplicate_cnt,
            failed_files=failed_cnt,
            average_confidence=round(avg_confidence, 4),
            total_processing_time_ms=total_time_ms,
            documents=[self._to_doc_read(d) for d in processed_docs],
        )

    async def list_patient_documents(
        self,
        patient_id: str,
        clinician_id: str,
        *,
        search: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "newest",
    ) -> List[DocumentListItem]:
        """List documents for patient owned by clinician."""
        docs = await self._repo.list_documents_for_patient(
            patient_id, clinician_id, search=search, category=category, status=status, sort_by=sort_by
        )
        return [self._to_doc_list_item(d) for d in docs]

    async def get_document(self, document_id: str, clinician_id: str) -> DocumentRead:
        """Fetch document details."""
        doc = await self._repo.get_document_by_id(document_id, clinician_id)
        if not doc:
            raise NotFoundError(f"Document with ID '{document_id}' was not found.")
        return self._to_read(doc)

    async def get_document_timeline(self, document_id: str, clinician_id: str) -> List[ProcessingLogRead]:
        """Return step-by-step pipeline execution logs for document timeline visualization."""
        doc = await self._repo.get_document_by_id(document_id, clinician_id)
        if not doc:
            raise NotFoundError(f"Document with ID '{document_id}' was not found.")

        logs = await self._repo.get_logs_for_document(document_id)
        return [ProcessingLogRead.model_validate(l) for l in logs]

    async def delete_document(self, document_id: str, clinician_id: str) -> None:
        """Delete a document record."""
        doc = await self._repo.get_document_by_id(document_id, clinician_id)
        if not doc:
            raise NotFoundError(f"Document with ID '{document_id}' was not found.")

        await self._repo.delete_document(doc)
        _log.info("DOCUMENT.DELETED", document_id=document_id, clinician_id=clinician_id)

    def _to_read(self, doc: Document) -> DocumentRead:
        return DocumentRead.model_validate(doc)

    async def retry_document(self, document_id: str, clinician_id: str) -> DocumentRead:
        """Re-process a failed document through the full pipeline."""
        doc = await self._repo.get_document_by_id(document_id, clinician_id)
        if not doc:
            raise NotFoundError(f"Document with ID '{document_id}' was not found.")
        if doc.status not in ("failed", "duplicate"):
            raise ValidationError("Only failed or duplicate documents can be retried.")

        # Read original file from storage
        storage_path = doc.storage_path
        if not storage_path or not os.path.exists(storage_path):
            raise NotFoundError("Original file not found on disk — cannot retry.")

        with open(storage_path, "rb") as f:
            content = f.read()

        # Reset status
        doc.status = "processing"
        doc.error_message = None
        await self._repo.update_document(doc)

        # Re-run pipeline
        try:
            result = await self._router.process_document(content, doc.original_filename, doc.mime_type)
            doc.file_type = "pdf" if result.file_type in ("digital_pdf", "scanned_pdf") else "image"
            doc.doc_category = result.doc_category
            doc.parse_source = result.parse_source
            doc.confidence_score = result.confidence_score
            doc.extracted_text = result.extracted_text
            doc.extracted_html = result.extracted_html
            doc.processing_time_ms = result.processing_time_ms
            doc.status = "completed"

            for step in result.steps:
                await self._add_step_log(
                    doc.id,
                    step.step_name,
                    step.status,
                    step.message,
                    step.duration_ms,
                )
            await self._add_step_log(doc.id, "retry", "completed", f"Retry succeeded via {result.parse_source}")
        except Exception as exc:
            doc.status = "failed"
            doc.error_message = str(exc)
            await self._add_step_log(doc.id, "retry", "failed", f"Retry failed: {str(exc)}")

        await self._repo.update_document(doc)
        _log.info("DOCUMENT.RETRIED", document_id=document_id, status=doc.status)
        return self._to_read(doc)

    async def process_text_entry(
        self, patient_id: str, clinician_id: str, req: TextEntryRequest
    ) -> DocumentRead:
        """
        Process direct copy-pasted clinical text entry or typed consultation notes.
        """
        if not req.raw_text.strip():
            raise ValidationError("Clinical text entry cannot be empty.")

        # Compute SHA256 Hash
        text_bytes = req.raw_text.encode("utf-8")
        sha256 = hashlib.sha256(text_bytes).hexdigest()

        # Check Duplicate
        existing = await self._repo.get_by_sha256(patient_id, sha256)

        if existing:
            _log.info("DOCUMENT.DUPLICATE_TEXT", patient_id=patient_id, document_id=existing.id)
            return self._to_read(existing)

        # Save Text File
        fname = f"{req.title.replace(' ', '_').lower()}_{uuid.uuid4().hex[:6]}.txt"
        storage_path = str(self._get_storage_dir(clinician_id, patient_id) / fname)
        with open(storage_path, "wb") as out_f:
            out_f.write(text_bytes)

        # Parse Date & Entities
        from app.modules.timeline.event_extractor import PriorityEventExtractor
        from app.modules.timeline.model import TimelineEvent
        from app.modules.analytics.model import ParameterHistory
        import json

        ev_data = PriorityEventExtractor.extract_priority_event(
            filename=fname,
            category=req.doc_category,
            text=req.raw_text,
            upload_time=datetime.now(timezone.utc),
        )

        doc = Document(
            patient_id=patient_id,
            clinician_id=clinician_id,
            original_filename=fname,
            file_type="txt",
            mime_type="text/plain",
            file_size_bytes=len(text_bytes),
            sha256_hash=sha256,
            storage_path=storage_path,
            doc_category=req.doc_category,
            status="completed",
            parse_source="direct_text",
            confidence_score=1.0,
            extracted_text=req.raw_text,
            extracted_html=f"<pre>{req.raw_text}</pre>",
            document_date=ev_data.event_date,
        )
        saved_doc = await self._repo.create_document(doc)

        # Persist TimelineEvent & ParameterHistory
        t_event = TimelineEvent(
            patient_id=patient_id,
            clinician_id=clinician_id,
            record_id=saved_doc.id,
            event_date=ev_data.event_date,
            date_priority_source=ev_data.date_priority_source,
            event_type=req.doc_category,
            document_type="TXT",
            title=req.title,
            summary=ev_data.summary,
            confidence=1.0,
            entities_json=json.dumps(ev_data.entities),
        )
        self._session.add(t_event)

        for p in ev_data.parameters:
            p_rec = ParameterHistory(
                patient_id=patient_id,
                clinician_id=clinician_id,
                record_id=saved_doc.id,
                parameter_name=p["parameter_name"],
                normalized_name=p["normalized_name"],
                value=p["value"],
                value_str=p["value_str"],
                unit=p["unit"],
                reference_range=p["reference_range"],
                status=p["status"],
                event_date=ev_data.event_date,
                confidence=1.0,
            )
            self._session.add(p_rec)

        await self._session.commit()

        _log.info("TEXT_ENTRY.COMPLETED", document_id=saved_doc.id, patient_id=patient_id)
        return self._to_read(saved_doc)



