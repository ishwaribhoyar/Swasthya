"""
Sarvam AI Document Parse Client.

Invokes Sarvam AI Doc-AI v1 Digitise & Parse APIs for digital and scanned PDF OCR & layout parsing
when API key is configured.
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


class SarvamParseClient:
    """Client for Sarvam AI Document Parsing APIs."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    async def parse_document(self, file_bytes: bytes, filename: str) -> Tuple[str, str, float] | None:
        """
        Send document to Sarvam Parse API.
        Tries Doc-AI v1 Digitise endpoint first, then direct parse-document endpoint.
        Returns (extracted_text, extracted_html, confidence) or None if unconfigured/failed.
        """
        if not self.api_key:
            return None

        # 1. Try Sarvam Doc-AI v1 Job Digitise endpoint with output_format="md"
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
                        for _ in range(20):
                            st_res = await client.get(
                                f"https://api.sarvam.ai/doc-ai/v1/job/{job_id}/status",
                                headers={"api-subscription-key": self.api_key},
                            )
                            if st_res.status_code == 200:
                                st_data = st_res.json()
                                status_str = st_data.get("status")
                                if status_str in ("completed", "partially_completed"):
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
                                                    return clean_md, clean_md, 0.99
                                    break

                                elif status_str in ("failed", "rejected"):
                                    break
                            time.sleep(1.0)
        except Exception as exc:
            _log.warning("sarvam_parse_job_exception", error=str(exc))

        # 2. Direct parse-document fallback
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
                    confidence = float(data.get("confidence", 0.98))
                    return clean_md, clean_md, confidence
                else:
                    _log.warning("sarvam_parse_failed", status_code=response.status_code)
                    return None
        except Exception as e:
            _log.warning("sarvam_parse_exception", error=str(e))
            return None
