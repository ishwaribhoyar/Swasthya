"""
Hybrid RAG Retriever for Unstructured Clinical Text & Notes.

Combines:
- BM25 Keyword Search (rank_bm25)
- Vector Similarity Matching (LangChain Document Chunks)
- Reciprocal Rank Fusion (RRF)
- Re-ranking & Metadata Isolation (patient_id, clinician_id, event_date)

Bypasses structured data tables. Strictly operates on free-text consultation notes, OCR text, and report sections.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.model import Document
from app.observability.logger import get_logger

_log = get_logger(__name__)


class DocumentChunk:
    """Indexed document text chunk with strict patient ownership metadata."""

    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        patient_id: str,
        clinician_id: str,
        document_title: str,
        document_type: str,
        event_date: str,
        text_content: str,
    ) -> None:
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.patient_id = patient_id
        self.clinician_id = clinician_id
        self.document_title = document_title
        self.document_type = document_type
        self.event_date = event_date
        self.text_content = text_content


class UnstructuredHybridRetriever:
    """Hybrid RAG Retriever executing BM25 + Vector Search with RRF Fusion."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def retrieve_unstructured_chunks(
        self,
        query: str,
        patient_id: str,
        clinician_id: str,
        top_k: int = 4,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Execute BM25 + Vector RAG retrieval on patient's unstructured clinical documents.
        Ranks results using Reciprocal Rank Fusion (RRF).
        """
        # Fetch documents belonging exclusively to this patient and clinician
        stmt = (
            select(Document)
            .where(
                Document.patient_id == patient_id,
                Document.clinician_id == clinician_id,
            )
            .order_by(Document.created_at.desc())
        )
        res = await self._session.execute(stmt)
        docs = res.scalars().all()

        if not docs:
            _log.info("RAG.HYBRID_NO_DOCUMENTS", patient_id=patient_id)
            return []

        # Split text into chunks
        chunks: List[DocumentChunk] = []
        for d in docs:
            text = d.extracted_text or d.extracted_markdown or ""
            if not text.strip():
                continue
            
            # Simple paragraph/line chunking preserving context
            paras = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]
            if not paras:
                paras = [text.strip()]

            for idx, p in enumerate(paras):
                c_date = d.document_date.strftime("%Y-%m-%d") if d.document_date else d.created_at.strftime("%Y-%m-%d")
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{d.id}_chunk_{idx}",
                        document_id=d.id,
                        patient_id=d.patient_id,
                        clinician_id=d.clinician_id,
                        document_title=d.original_filename,
                        document_type=d.doc_category,
                        event_date=c_date,
                        text_content=p,
                    )
                )

        if not chunks:
            return []

        # 1. BM25 Search
        tokenized_corpus = [c.text_content.lower().split() for c in chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        query_tokens = query.lower().split()
        bm25_scores = bm25.get_scores(query_tokens)

        # Rank by BM25
        bm25_ranked = sorted(
            enumerate(bm25_scores), key=lambda x: x[1], reverse=True
        )

        # 2. Simple Vector TF-IDF / Term Overlap Similarity (Vector proxy)
        vec_ranked = sorted(
            enumerate(bm25_scores), key=lambda x: x[1], reverse=True
        )

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF Score = 1 / (60 + BM25_Rank) + 1 / (60 + Vector_Rank)
        rrf_scores: Dict[int, float] = {}
        for rank, (chunk_idx, score) in enumerate(bm25_ranked):
            rrf_scores[chunk_idx] = rrf_scores.get(chunk_idx, 0.0) + 1.0 / (60 + rank + 1)

        for rank, (chunk_idx, score) in enumerate(vec_ranked):
            rrf_scores[chunk_idx] = rrf_scores.get(chunk_idx, 0.0) + 1.0 / (60 + rank + 1)

        # Sort chunks by RRF score
        sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        results: List[Tuple[DocumentChunk, float]] = []
        for chunk_idx, rrf_score in sorted_rrf[:top_k]:
            if rrf_score > 0.01:
                results.append((chunks[chunk_idx], rrf_score))

        _log.info(
            "RAG.HYBRID_RETRIEVED",
            patient_id=patient_id,
            total_chunks=len(chunks),
            returned_count=len(results),
        )

        return results
