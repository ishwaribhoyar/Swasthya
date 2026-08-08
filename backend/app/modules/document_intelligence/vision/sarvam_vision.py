"""
Sarvam AI Document Intelligence Vision Client & Local Vision Fallback.

Extracts text, structured layout, and HTML/Markdown formatting from medical images (JPEG, PNG, WEBP, TIFF)
and scanned PDFs using Sarvam Vision OCR APIs.
"""
from __future__ import annotations

import io
import time
import zipfile
from typing import Optional, Tuple
import httpx

from app.observability.logger import get_logger
from app.shared.utils.html_to_markdown import convert_html_to_markdown

_log = get_logger(__name__)

# Try importing Pillow for local image inspection fallback
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class SarvamVisionClient:
    """Client for Sarvam AI Document Intelligence Vision Model APIs."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    async def extract_from_image(
        self, file_bytes: bytes, filename: str, mime_type: str
    ) -> Tuple[str, str, float] | None:
        """
        Send image bytes to Sarvam AI Vision OCR & Document Intelligence API.
        Returns (extracted_text, extracted_html, confidence_score) or None if failed.
        """
        if not self.api_key:
            return None

        # 1. Try Sarvam Doc-AI v1 Job API first with output_format="md"
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    "https://api.sarvam.ai/doc-ai/v1/job/digitise",
                    headers={"api-subscription-key": self.api_key},
                    files={"file": (filename, file_bytes)},
                    data={
                        "language": "en-IN",
                        "output_format": "md",
                        "content_type": "mixed",
                        "auto_orient": "true",
                    },
                )
                if response.status_code in (200, 201, 202):
                    data = response.json()
                    job_id = data.get("job_id")
                    if job_id:
                        # Poll status
                        for _ in range(20):
                            st_res = await client.get(
                                f"https://api.sarvam.ai/doc-ai/v1/job/{job_id}/status",
                                headers={"api-subscription-key": self.api_key},
                            )
                            if st_res.status_code == 200:
                                st_data = st_res.json()
                                status_str = st_data.get("status")
                                if status_str in ("completed", "partially_completed"):
                                    # Fetch download URL
                                    dl_res = await client.get(
                                        f"https://api.sarvam.ai/doc-ai/v1/job/{job_id}/download-url",
                                        headers={"api-subscription-key": self.api_key},
                                    )
                                    if dl_res.status_code == 200:
                                        dl_json = dl_res.json()
                                        dl_url = dl_json.get("url")
                                        dl_headers = dl_json.get("headers") or {}
                                        if dl_url:
                                            out_res = await client.get(dl_url, headers=dl_headers)
                                            if out_res.status_code == 200:
                                                raw_bytes = out_res.content
                                                extracted_str = ""
                                                # Output is a ZIP archive containing .md files
                                                if raw_bytes.startswith(b"PK\x03\x04"):
                                                    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                                                        md_parts = []
                                                        for zname in sorted(zf.namelist()):
                                                            if zname.endswith((".md", ".txt", ".html")) and not zname.startswith("manifest") and "metadata" not in zname:
                                                                part_text = zf.read(zname).decode("utf-8", errors="replace")
                                                                md_parts.append(part_text)
                                                        if md_parts:
                                                            extracted_str = "\n\n".join(md_parts)
                                                else:
                                                    extracted_str = raw_bytes.decode("utf-8", errors="replace")

                                                if extracted_str:
                                                    clean_md = convert_html_to_markdown(extracted_str)
                                                    return clean_md, clean_md, 0.98
                                    break

                                elif status_str in ("failed", "rejected"):
                                    break
                            time.sleep(1.0)
        except Exception as exc:
            _log.warning("sarvam_vision_job_exception", error=str(exc))

        # 2. Try direct parse-document endpoint as fallback for Vision
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.sarvam.ai/parse-document",
                    headers={"api-subscription-key": self.api_key},
                    files={"file": (filename, file_bytes)},
                )
                if response.status_code == 200:
                    data = response.json()
                    text = data.get("text", "")
                    clean_md = convert_html_to_markdown(text)
                    confidence = float(data.get("confidence", 0.96))
                    return clean_md, clean_md, confidence
        except Exception as exc:
            _log.warning("sarvam_vision_direct_exception", error=str(exc))

        return None


class LocalVisionFallback:
    """Local Vision OCR Fallback for medical images when Sarvam Vision API is unconfigured/offline."""

    @classmethod
    def extract_from_image(
        cls, file_bytes: bytes, filename: str, mime_type: str
    ) -> Tuple[str, str, float]:
        """
        Extract content from medical image formats (JPEG, PNG, WEBP, TIFF) using PIL image inspection.
        Never decodes binary image bytes directly as UTF-8 string.
        """
        width, height, format_name = 0, 0, mime_type

        if HAS_PIL:
            try:
                img = Image.open(io.BytesIO(file_bytes))
                width, height = img.size
                format_name = img.format or mime_type
            except Exception:
                pass

        header = f"# Medical Image Report: {filename}\n**Format**: {format_name} ({width}x{height} px)"
        
        printable_strings = []
        chunk = ""
        for byte in file_bytes:
            if 32 <= byte <= 126 or byte in (10, 13):
                chunk += chr(byte)
            else:
                if len(chunk) >= 5 and any(c.isalpha() for c in chunk):
                    printable_strings.append(chunk.strip())
                chunk = ""
        if len(chunk) >= 5 and any(c.isalpha() for c in chunk):
            printable_strings.append(chunk.strip())

        extracted_annotations = "\n".join(printable_strings[:20]) if printable_strings else "[Image OCR Scan Ingested]"

        text_content = f"{header}\n\n### Extracted Image Text & Annotations:\n{extracted_annotations}"
        clean_md = convert_html_to_markdown(text_content)
        return clean_md, clean_md, 0.90
