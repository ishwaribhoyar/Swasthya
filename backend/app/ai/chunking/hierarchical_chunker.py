"""
Hierarchical Semantic Chunker.

Splits medical documents and clinical patient records by semantic domain
(Lab Sections, Prescriptions, Clinical Notes, Vitals, Summaries) instead of naive character counts.
Attaches rich metadata to each chunk for hybrid retrieval and citation tracking.
"""
from __future__ import annotations

import re
import uuid
from typing import Dict, List, Optional


class ClinicalChunk:
    """Semantic clinical document chunk with rich metadata."""

    def __init__(
        self,
        chunk_id: str,
        patient_id: str,
        doc_id: str,
        filename: str,
        category: str,
        header: str,
        text: str,
        token_count: int,
    ) -> None:
        self.chunk_id = chunk_id
        self.patient_id = patient_id
        self.doc_id = doc_id
        self.filename = filename
        self.category = category
        self.header = header
        self.text = text
        self.token_count = token_count

    def to_dict(self) -> Dict:
        return {
            "chunk_id": self.chunk_id,
            "patient_id": self.patient_id,
            "doc_id": self.doc_id,
            "filename": self.filename,
            "category": self.category,
            "header": self.header,
            "text": self.text,
            "token_count": self.token_count,
        }


class HierarchicalChunker:
    """Semantic chunker breaking medical text by clinical section headers & paragraphs."""

    @classmethod
    def chunk_document(
        cls,
        patient_id: str,
        doc_id: str,
        filename: str,
        category: str,
        text: str,
        max_chunk_size: int = 500,
    ) -> List[ClinicalChunk]:
        """
        Partition medical text into semantic domain chunks.
        """
        if not text or not text.strip():
            return []

        # Split by explicit headers or page boundaries
        sections = re.split(r"(?:\n--- Page \d+ ---|\n[A-Z\s]{3,30}:|\n#+\s)", text)
        headers = re.findall(r"(?:--- Page \d+ ---|[A-Z\s]{3,30}:|#+\s[^\n]+)", text)

        chunks: List[ClinicalChunk] = []

        if not sections or len(sections) <= 1:
            # Fallback to paragraph splitting
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            current_chunk = ""
            current_header = f"{category.upper()} Section"

            for p in paragraphs:
                if len(current_chunk) + len(p) <= max_chunk_size:
                    current_chunk += ("\n\n" if current_chunk else "") + p
                else:
                    if current_chunk:
                        chunk_id = f"chk-{uuid.uuid4().hex[:8]}"
                        chunks.append(
                            ClinicalChunk(
                                chunk_id=chunk_id,
                                patient_id=patient_id,
                                doc_id=doc_id,
                                filename=filename,
                                category=category,
                                header=current_header,
                                text=current_chunk,
                                token_count=len(current_chunk.split()),
                            )
                        )
                    current_chunk = p

            if current_chunk:
                chunk_id = f"chk-{uuid.uuid4().hex[:8]}"
                chunks.append(
                    ClinicalChunk(
                        chunk_id=chunk_id,
                        patient_id=patient_id,
                        doc_id=doc_id,
                        filename=filename,
                        category=category,
                        header=current_header,
                        text=current_chunk,
                        token_count=len(current_chunk.split()),
                    )
                )
        else:
            header_idx = 0
            for sec in sections:
                sec_str = sec.strip()
                if not sec_str:
                    continue
                header_text = headers[header_idx].strip() if header_idx < len(headers) else f"{category.upper()} Section"
                header_idx += 1

                chunk_id = f"chk-{uuid.uuid4().hex[:8]}"
                chunks.append(
                    ClinicalChunk(
                        chunk_id=chunk_id,
                        patient_id=patient_id,
                        doc_id=doc_id,
                        filename=filename,
                        category=category,
                        header=header_text,
                        text=sec_str,
                        token_count=len(sec_str.split()),
                    )
                )

        return chunks
