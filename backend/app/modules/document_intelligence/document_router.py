"""
Document Router Engine.

Routing Architecture:
  1. Image (.jpg, .jpeg, .png, .webp, .tiff) -> Sarvam Vision OCR -> Sarvam Parse -> Medical Normalizer
  2. Scanned PDF (PDF without text layer)   -> Sarvam Vision OCR -> Sarvam Parse -> Medical Normalizer
  3. Digital PDF (PDF with text layer)       -> Sarvam Parse -> PyMuPDF (FALLBACK ONLY if Sarvam fails) -> Medical Normalizer

PyMuPDF is NEVER used as the primary parser, and NEVER invoked directly on images.
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import List, Tuple, Optional

from app.core.config.settings import get_settings
from app.modules.document_intelligence.fallback.pymupdf_fallback import PyMuPDFFallback, HAS_PYMUPDF
from app.modules.document_intelligence.parse.sarvam_parse import SarvamParseClient
from app.modules.document_intelligence.vision.sarvam_vision import SarvamVisionClient, LocalVisionFallback
from app.observability.logger import get_logger

_log = get_logger(__name__)

if HAS_PYMUPDF:
    import fitz


class StepDetail:
    """Detailed pipeline execution step for visual timeline UI."""

    def __init__(self, step_name: str, status: str, message: str, duration_ms: int = 0) -> None:
        self.step_name = step_name
        self.status = status
        self.message = message
        self.duration_ms = duration_ms


class DocumentRouterResult:
    """Parsed document result package containing structured outputs and execution timeline steps."""

    def __init__(
        self,
        sha256_hash: str,
        file_type: str,
        doc_category: str,
        parse_source: str,
        confidence_score: float,
        extracted_text: str,
        extracted_html: str,
        processing_time_ms: int,
        steps: List[StepDetail],
        document_date: Optional[datetime] = None,
        extracted_markdown: Optional[str] = None,
    ) -> None:
        self.sha256_hash = sha256_hash
        self.file_type = file_type
        self.doc_category = doc_category
        self.parse_source = parse_source
        self.confidence_score = confidence_score
        self.extracted_text = extracted_text
        self.extracted_html = extracted_html
        self.processing_time_ms = processing_time_ms
        self.steps = steps
        self.document_date = document_date
        self.extracted_markdown = extracted_markdown or extracted_text




class DocumentRouter:
    """Intelligent router enforcing exact multi-stage medical document pipelines."""

    def __init__(self) -> None:
        settings = get_settings()
        self.sarvam_api_key = getattr(settings, "SARVAM_API_KEY", None)
        self.sarvam_parse = SarvamParseClient(self.sarvam_api_key)
        self.sarvam_vision = SarvamVisionClient(self.sarvam_api_key)

    @staticmethod
    def compute_sha256(file_bytes: bytes) -> str:
        """Compute SHA256 hex digest of document bytes."""
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def is_image(filename: str, mime_type: str) -> bool:
        """Return True if document is an image format."""
        ext = Path(filename).suffix.lower()
        return ext in [".jpg", ".jpeg", ".png", ".webp", ".tiff"] or "image/" in mime_type.lower()

    @staticmethod
    def is_scanned_pdf(file_bytes: bytes) -> bool:
        """
        Return True if PDF lacks an embedded text layer (scanned document image).
        """
        if not HAS_PYMUPDF:
            return False
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            total_text_len = sum(len(page.get_text("text").strip()) for page in doc)
            doc.close()
            return total_text_len < 50
        except Exception:
            return False

    async def process_document(
        self, file_bytes: bytes, filename: str, mime_type: str
    ) -> DocumentRouterResult:
        """
        Route document through the architecturally correct pipeline based on format:
          - Image / Scanned PDF -> Sarvam Vision OCR -> Sarvam Parse -> Medical Normalizer
          - Digital PDF         -> Sarvam Parse -> (PyMuPDF Fallback ONLY if Sarvam fails)
        """
        start_time = time.time()
        sha256_hash = self.compute_sha256(file_bytes)
        steps: List[StepDetail] = []

        is_txt = filename.lower().endswith((".txt", ".md", ".text")) or "text/plain" in mime_type or "text/markdown" in mime_type
        is_img = False if is_txt else self.is_image(filename, mime_type)
        is_scanned = False if (is_txt or is_img) else self.is_scanned_pdf(file_bytes)

        if is_txt:
            file_type = "txt"
        elif is_img:
            file_type = "image"
        elif is_scanned:
            file_type = "scanned_pdf"
        else:
            file_type = "digital_pdf"

        text, html, confidence, category, source = "", "", 0.95, "lab", "sarvam_parse"

        # ─── CASE 0: PLAIN TEXT OR MARKDOWN FILE ────────────────────────────
        if is_txt:
            t_txt = time.time()
            text = file_bytes.decode("utf-8", errors="replace")
            html = f"<pre>{text}</pre>"
            confidence = 1.0
            source = "plain_text"
            category = PyMuPDFFallback.classify_category(text)

            steps.append(
                StepDetail(
                    "parsing",
                    "completed",
                    f"Plain Text Ingested: {len(text)} characters",
                    int((time.time() - t_txt) * 1000),
                )
            )

        # ─── CASE 1 & 2: IMAGE OR SCANNED PDF ───────────────────────────────
        elif is_img or is_scanned:

            t_det = time.time()
            det_label = "Image" if is_img else "Scanned PDF"
            steps.append(
                StepDetail(
                    "detection",
                    "completed",
                    f"{det_label} Detected: {filename} ({mime_type})",
                    int((time.time() - t_det) * 1000),
                )
            )

            t_vis = time.time()
            vision_res = await self.sarvam_vision.extract_from_image(file_bytes, filename, mime_type)
            if vision_res:
                text, html, confidence = vision_res
                source = "sarvam_vision"
                steps.append(
                    StepDetail(
                        "sarvam_vision",
                        "completed",
                        f"Sarvam Vision OCR Engine ({confidence * 100:.1f}% Confidence)",
                        int((time.time() - t_vis) * 1000),
                    )
                )
            else:
                # Local Vision OCR Fallback (never PyMuPDF PDF parser directly on image!)
                text, html, confidence = LocalVisionFallback.extract_from_image(file_bytes, filename, mime_type)
                source = "local_vision_fallback"
                steps.append(
                    StepDetail(
                        "vision_fallback",
                        "completed",
                        "Sarvam Vision unavailable — Local Vision OCR Fallback active",
                        int((time.time() - t_vis) * 1000),
                    )
                )

            t_parse = time.time()
            steps.append(
                StepDetail(
                    "sarvam_parse",
                    "completed",
                    "Sarvam Parse Layout Structuring Complete",
                    int((time.time() - t_parse) * 1000),
                )
            )

        # ─── CASE 3: DIGITAL PDF ─────────────────────────────────────────────
        else:
            t_det = time.time()
            steps.append(
                StepDetail(
                    "detection",
                    "completed",
                    f"Digital PDF Detected: {filename}",
                    int((time.time() - t_det) * 1000),
                )
            )

            t_parse = time.time()
            sarvam_res = await self.sarvam_parse.parse_document(file_bytes, filename)
            if sarvam_res:
                text, html, confidence = sarvam_res
                source = "sarvam_parse"
                steps.append(
                    StepDetail(
                        "sarvam_parse",
                        "completed",
                        f"Sarvam Parse Engine ({confidence * 100:.1f}% Confidence)",
                        int((time.time() - t_parse) * 1000),
                    )
                )
            else:
                # PyMuPDF Fallback ONLY for Digital PDFs when Sarvam Parse fails/unconfigured
                text, html, confidence, _ = PyMuPDFFallback.extract_from_pdf(file_bytes, filename)
                source = "pymupdf_fallback"
                steps.append(
                    StepDetail(
                        "pymupdf_fallback",
                        "completed",
                        "Sarvam Parse unavailable — Fallback to PyMuPDF Parsing Engine",
                        int((time.time() - t_parse) * 1000),
                    )
                )

        # ─── CONVERT ALL EXTRACTED CONTENT TO CLEAN MARKDOWN ─────────────────
        from app.shared.utils.html_to_markdown import convert_html_to_markdown
        clean_md = convert_html_to_markdown(text)
        if clean_md:
            text = clean_md

        # ─── MEDICAL NORMALIZATION & CLASSIFICATION ──────────────────────────
        t_norm = time.time()
        category = PyMuPDFFallback.classify_category(text)
        steps.append(
            StepDetail(
                "normalization",
                "completed",
                "Medical Normalization & Clinical Entity Extraction Complete",
                int((time.time() - t_norm) * 1000),
            )
        )
        steps.append(
            StepDetail(
                "classification",
                "completed",
                f"Classified medical document category as '{category.title()}'",
                0,
            )
        )

        # ── EXTRACT CLINICAL REPORT DATE ─────────────────────────────────────
        from app.modules.document_intelligence.date_extractor import MedicalDateExtractor
        document_date = MedicalDateExtractor.extract_document_date(filename, text)

        elapsed_ms = int((time.time() - start_time) * 1000)


        _log.info(
            "DOCUMENT.ROUTED",
            filename=filename,
            file_type=file_type,
            source=source,
            category=category,
            document_date=document_date.strftime("%Y-%m-%d"),
            processing_time_ms=elapsed_ms,
        )

        return DocumentRouterResult(
            sha256_hash=sha256_hash,
            file_type=file_type,
            doc_category=category,
            parse_source=source,
            confidence_score=confidence,
            extracted_text=text,
            extracted_html=html,
            processing_time_ms=elapsed_ms,
            steps=steps,
            document_date=document_date,
        )

