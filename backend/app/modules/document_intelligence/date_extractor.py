"""
Medical Document Date Extractor.

Extracts the actual clinical report date / sample collection date from:
  1. Document text & OCR annotations (e.g. "Report Date: 2026-07-31", "Collection Date: 15/05/2025", "Dated: 29 Jun 2025")
  2. Filename timestamp patterns (e.g. "WhatsApp Image 2026-07-31...", "IMG_20250629_132842.jpg")
  3. Fallback to current UTC timestamp if no clinical date is specified.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional
from app.observability.logger import get_logger

_log = get_logger(__name__)

# Common date formats found in medical reports & filenames
MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
}


class MedicalDateExtractor:
    """Intelligent clinical report date parser."""

    @classmethod
    def extract_document_date(cls, filename: str, extracted_text: str) -> datetime:
        """
        Extract clinical date from document text or filename.
        Returns timezone-aware datetime.
        """
        # 1. Search text for explicit clinical date headers first
        if extracted_text:
            text_date = cls._extract_from_text(extracted_text)
            if text_date:
                _log.info("DATE_EXTRACTED.TEXT", filename=filename, date=text_date.strftime("%Y-%m-%d"))
                return text_date

        # 2. Search filename patterns (e.g. IMG_20250629_..., WhatsApp Image 2026-07-31...)
        if filename:
            filename_date = cls._extract_from_filename(filename)
            if filename_date:
                _log.info("DATE_EXTRACTED.FILENAME", filename=filename, date=filename_date.strftime("%Y-%m-%d"))
                return filename_date

        # 3. Fallback to current UTC time
        return datetime.now(timezone.utc)

    @classmethod
    def _extract_from_filename(cls, filename: str) -> Optional[datetime]:
        """Parse dates embedded in camera / messaging filenames."""
        # Pattern 1: YYYY-MM-DD or YYYY_MM_DD (e.g. 2026-07-31)
        m1 = re.search(r"\b(20[2-3][0-9])[-_](0[1-9]|1[0-2])[-_](0[1-9]|[12][0-9]|3[01])\b", filename)
        if m1:
            try:
                y, m, d = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
                return datetime(y, m, d, tzinfo=timezone.utc)
            except ValueError:
                pass

        # Pattern 2: IMG_YYYYMMDD_ (e.g. IMG_20250629_132842)
        m2 = re.search(r"\b(20[2-3][0-9])(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])\b", filename)
        if m2:
            try:
                y, m, d = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
                return datetime(y, m, d, tzinfo=timezone.utc)
            except ValueError:
                pass

        return None

    @classmethod
    def _extract_from_text(cls, text: str) -> Optional[datetime]:
        """Parse explicit report/collection dates from extracted OCR text."""
        # Pattern 1: Keywords followed by YYYY-MM-DD or DD/MM/YYYY
        # (e.g. "Report Date: 2026-07-31", "Collection Date: 15/05/2025")
        keywords = r"(?:report\s*date|date\s*of\s*collection|sample\s*date|dated|collected\s*on|date)"
        m1 = re.search(
            rf"(?i){keywords}\s*[:\-]?\s*\b(20[2-3][0-9])[-/\.](0[1-9]|1[0-2])[-/\.](0[1-9]|[12][0-9]|3[01])\b",
            text,
        )
        if m1:
            try:
                return datetime(int(m1.group(1)), int(m1.group(2)), int(m1.group(3)), tzinfo=timezone.utc)
            except ValueError:
                pass

        # Pattern 2: DD/MM/YYYY or DD-MM-YYYY near header
        m2 = re.search(
            rf"(?i){keywords}\s*[:\-]?\s*\b(0[1-9]|[12][0-9]|3[01])[-/\.](0[1-9]|1[0-2])[-/\.](20[2-3][0-9])\b",
            text,
        )
        if m2:
            try:
                return datetime(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)), tzinfo=timezone.utc)
            except ValueError:
                pass

        # Pattern 3: DD-MMM-YYYY (e.g. 31-Jul-2026, 29 Jun 2025)
        m3 = re.search(
            r"\b(0[1-9]|[12][0-9]|3[01])\s*[-/\s]\s*([a-zA-Z]{3,9})\s*[-/\s]\s*(20[2-3][0-9])\b",
            text,
        )
        if m3:
            day = int(m3.group(1))
            m_str = m3.group(2).lower()
            year = int(m3.group(3))
            month = MONTH_MAP.get(m_str)
            if month:
                try:
                    return datetime(year, month, day, tzinfo=timezone.utc)
                except ValueError:
                    pass

        return None
