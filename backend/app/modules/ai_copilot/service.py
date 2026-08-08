"""
AI Copilot Service Engine.

Orchestrates the 12-Stage Production Clinical RAG Pipeline:
  Stage 1: Patient & Clinician Multi-tenant Query Entry
  Stage 4: Patient Context Builder (Demographics, Alerts, Timeline)
  Stage 5: Hierarchical Semantic Chunker
  Stage 6: Dense Vector Embeddings (384d)
  Stage 7: Sparse Okapi BM25 Keyword Search
  Stage 8: Hybrid Retrieval & Reciprocal Rank Fusion (RRF)
  Stage 9: Cross-Encoder Re-ranking
  Stage 10: MMR Diversification across Clinical Domains
  Stage 11: Safety, PHI Scrubbing & Groundness Verification
  Stage 12: GPT-5 Nano Reasoning, Source Citations & Audit Hash Logging
"""
from __future__ import annotations

import json
import uuid
from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chunking.hierarchical_chunker import HierarchicalChunker, ClinicalChunk
from app.ai.context_builder.patient_context import PatientContextBuilder
from app.ai.llm.gpt_nano import GPTNanoReasoningEngine, GPTNanoResponse
from app.ai.retrievers.hybrid_retriever import HybridRetriever
from app.modules.ai_copilot.model import AIChatLog
from app.modules.ai_copilot.repository import AICopilotRepository
from app.modules.ai_copilot.schema import AIQueryRequest, AIQueryResponse, SourceCitationSchema
from app.observability.logger import get_logger

_log = get_logger(__name__)


class AICopilotService:
    """Service orchestrating the 12-Stage Production Clinical RAG Pipeline."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AICopilotRepository(session)
        self._ctx_builder = PatientContextBuilder(session)
        self._retriever = HybridRetriever()

    async def query_patient(
        self, patient_id: str, clinician_id: str, query: str
    ) -> AIQueryResponse:
        """
        Execute full 12-Stage Production Clinical RAG Pipeline for a patient.
        """
        # 1. Build Patient Context Snapshot (Demographics, Alerts, Document Timeline)
        snapshot = await self._ctx_builder.build_snapshot(patient_id, clinician_id)

        # 2. Hierarchical Semantic Chunking across all patient documents
        all_chunks: List[ClinicalChunk] = []

        # Create a synthetic context chunk for patient summary snapshot
        if snapshot.patient_summary_text:
            all_chunks.extend(
                HierarchicalChunker.chunk_document(
                    patient_id=patient_id,
                    doc_id="patient-profile",
                    filename="Patient Profile & Medical History",
                    category="summary",
                    text=snapshot.patient_summary_text,
                )
            )

        for doc_item in snapshot.documents_summary:
            doc_chunks = HierarchicalChunker.chunk_document(
                patient_id=patient_id,
                doc_id=doc_item["doc_id"],
                filename=doc_item["filename"],
                category=doc_item["category"],
                text=doc_item["full_text"],
            )
            all_chunks.extend(doc_chunks)

        # 3. Hybrid Retrieval (Dense Vector + Sparse BM25 + RRF + Re-ranking + MMR)
        retrieved_scored_chunks = self._retriever.retrieve(query, all_chunks, top_k=5)

        # 4. GPT-5 Nano Reasoning Engine (Synthesizes answer, source citations, & audit hash)
        gpt_res: GPTNanoResponse = await GPTNanoReasoningEngine.generate_response_async(
            query=query,
            patient_snapshot=snapshot,
            retrieved_chunks=retrieved_scored_chunks,
        )


        # 5. Persist Audit Log into SQLite
        log_id = f"log-{uuid.uuid4().hex[:12]}"
        sources_data = [s.to_dict() for s in gpt_res.sources]

        chat_log = AIChatLog(
            id=log_id,
            clinician_id=clinician_id,
            patient_id=patient_id,
            query=query,
            answer=gpt_res.answer,
            confidence_score=gpt_res.confidence_score,
            sources_json=json.dumps(sources_data),
            audit_hash=gpt_res.audit_hash,
        )
        saved_log = await self._repo.log_query(chat_log)

        _log.info(
            "RAG_PIPELINE.COMPLETED",
            patient_id=patient_id,
            log_id=log_id,
            confidence=gpt_res.confidence_score,
            audit_hash=gpt_res.audit_hash[:16],
        )

        return AIQueryResponse(
            id=saved_log.id,
            patient_id=patient_id,
            query=query,
            answer=gpt_res.answer,
            confidence_score=gpt_res.confidence_score,
            sources=[SourceCitationSchema(**s) for s in sources_data],
            audit_hash=gpt_res.audit_hash,
            created_at=saved_log.created_at,
        )

    async def get_patient_chat_history(
        self, patient_id: str, clinician_id: str
    ) -> List[AIQueryResponse]:
        """Fetch audit log history for patient."""
        logs = await self._repo.list_chat_history(patient_id, clinician_id)
        result = []
        for l in logs:
            try:
                sources_data = json.loads(l.sources_json)
            except Exception:
                sources_data = []

            result.append(
                AIQueryResponse(
                    id=l.id,
                    patient_id=l.patient_id,
                    query=l.query,
                    answer=l.answer,
                    confidence_score=l.confidence_score,
                    sources=[SourceCitationSchema(**s) for s in sources_data],
                    audit_hash=l.audit_hash,
                    created_at=l.created_at,
                )
            )
        return result
