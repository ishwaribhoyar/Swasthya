"""
AI Copilot Service Engine — Orchestrates the complete 12-Stage Grounded RAG Pipeline.

Stages:
  1. Input Normalization & Input Guard
  2. Patient Resolution & Authorization Scope
  3. Query Intent Classification
  4. Query Decomposition
  5. Retrieval Strategy Selection
  6. Structured / Hybrid Retrieval
  7. Reciprocal Rank Fusion (RRF)
  8. Reranking & Relevance Filtering
  9. Context Grounding & Privacy Isolation
  10. Token-Budgeted Context Construction
  11. GPT-5 Nano Response Generation
  12. Evidence Validation, Safety Firewall & Source Attribution
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm.openai_client import GPT5NanoClient
from app.ai.retrievers.structured_retriever import StructuredRetriever, StructuredEvidence
from app.ai.retrievers.hybrid_retriever import UnstructuredHybridRetriever
from app.ai.guardrails.safety_firewall import SafetyFirewall
from app.ai.copilot.patient_resolver import PatientResolver
from app.ai.copilot.query_router import QueryRouter
from app.ai.copilot.context_builder import ContextBuilder

from app.modules.ai_copilot.schema import (
    AICopilotChatRequest,
    AICopilotChatResponse,
    AmbiguousCandidate,
    RAGAuditTrace,
    SourceAttribution,
)
from app.observability.logger import get_logger

_log = get_logger(__name__)


class AICopilotService:
    """Service orchestrating the 12-stage Grounded RAG pipeline for ClinIQ Copilot."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._gpt_client = GPT5NanoClient()
        self._patient_resolver = PatientResolver(session)
        self._structured_retriever = StructuredRetriever(session)
        self._unstructured_retriever = UnstructuredHybridRetriever(session)

    async def process_chat_message(
        self, req: AICopilotChatRequest, clinician_id: str
    ) -> AICopilotChatResponse:
        """Execute full 12-stage RAG pipeline and return grounded response."""
        
        # STAGE 1: Input Normalization & Input Guard
        clean_message = req.message.strip()
        input_guard_res = SafetyFirewall.validate_input(clean_message)
        if not input_guard_res.passed:
            return AICopilotChatResponse(
                success=False,
                answer=input_guard_res.reason or "Invalid query pattern detected.",
                confidence="INSUFFICIENT",
            )

        # STAGE 2: Patient Resolution & Ownership Check
        resolution = await self._patient_resolver.resolve_patient(
            query_text=clean_message,
            clinician_id=clinician_id,
            explicit_patient_id=req.patient_id,
        )

        if resolution.status == "AMBIGUOUS":
            cands = [
                AmbiguousCandidate(
                    id=c.id,
                    mrn=c.mrn,
                    name=f"{c.first_name} {c.last_name}",
                    date_of_birth=c.date_of_birth.strftime("%Y-%m-%d"),
                    gender=c.gender,
                )
                for c in resolution.candidates
            ]
            return AICopilotChatResponse(
                success=True,
                answer=resolution.message or "Multiple patients matched your query. Please select the correct patient.",
                confidence="INSUFFICIENT",
                intent="AMBIGUOUS_PATIENT",
                ambiguous_candidates=cands,
            )

        # Handle General Medical Knowledge query without patient context
        intent = QueryRouter.classify_query(clean_message)
        if intent.is_general_info:
            return await self._handle_general_medical_info(clean_message, intent.target_medicine)

        # If query requires patient context but patient was not found
        if resolution.status != "RESOLVED" or not resolution.patient:
            return AICopilotChatResponse(
                success=True,
                answer=resolution.message or "I couldn't find a matching patient record. Please specify a patient name or MRN.",
                confidence="INSUFFICIENT",
                intent=intent.intent_type,
            )

        patient = resolution.patient

        # STAGE 3 & 4: Intent Classification & Query Decomposition
        _log.info("RAG.PIPELINE.INTENT", intent=intent.intent_type, pathway=intent.retrieval_pathway, patient_id=patient.id)

        # STAGE 5 & 6: Retrieval Execution (STRUCTURED vs UNSTRUCTURED)
        evidence_text = ""
        sources: List[SourceAttribution] = []
        confidence_level = "HIGH"

        if intent.retrieval_pathway == "STRUCTURED":
            evidence_obj = await self._execute_structured_retrieval(patient.id, clinician_id, intent)
            evidence_text = evidence_obj.evidence_summary
            confidence_level = evidence_obj.confidence_level
            sources = [SourceAttribution(**s) for s in evidence_obj.source_records]

        elif intent.retrieval_pathway == "UNSTRUCTURED":
            # STAGE 7 & 8: BM25 + Vector Search + Reciprocal Rank Fusion (RRF) & Reranking
            unstructured_chunks = await self._unstructured_retriever.retrieve_unstructured_chunks(
                query=clean_message, patient_id=patient.id, clinician_id=clinician_id, top_k=4
            )
            
            if not unstructured_chunks:
                evidence_text = "No relevant clinical notes or document sections found for this patient."
                confidence_level = "INSUFFICIENT"
            else:
                chunk_lines = []
                for chunk, rrf_score in unstructured_chunks:
                    chunk_lines.append(f"Document: {chunk.document_title} ({chunk.event_date})\nContent: {chunk.text_content}")
                    sources.append(
                        SourceAttribution(
                            record_id=chunk.document_id,
                            title=chunk.document_title,
                            event_date=chunk.event_date,
                            document_type=chunk.document_type.upper(),
                        )
                    )
                evidence_text = "\n\n".join(chunk_lines)
                confidence_level = "HIGH" if len(unstructured_chunks) >= 2 else "MEDIUM"

        else:
            # HYBRID PATHWAY
            st_obj = await self._structured_retriever.retrieve_patient_summary(patient.id, clinician_id)
            sources = [SourceAttribution(**s) for s in st_obj.source_records]

            # For short name queries (patient lookups), use only compact structured evidence.
            # Appending raw OCR chunks bloats the prompt and exhausts GPT-5 Nano reasoning budget.
            is_short_query = len(clean_message.strip().split()) <= 3
            if is_short_query:
                evidence_text = st_obj.evidence_summary
            else:
                un_chunks = await self._unstructured_retriever.retrieve_unstructured_chunks(
                    query=clean_message, patient_id=patient.id, clinician_id=clinician_id, top_k=2
                )
                doc_ctx = "\n".join([c[0].text_content for c in un_chunks])
                evidence_text = f"STRUCTURED SUMMARY:\n{st_obj.evidence_summary}\n\nDOCUMENT CONTEXT:\n{doc_ctx}"
                for c, _ in un_chunks:
                    sources.append(SourceAttribution(
                        record_id=c.document_id,
                        title=c.document_title,
                        event_date=c.event_date,
                        document_type=c.document_type.upper()
                    ))


        # STAGE 9 & 10: Context Grounding, Privacy Sanitization & Token-Budgeted Context Construction
        grounding_check = SafetyFirewall.validate_context_grounding(patient.id, [s.model_dump() for s in sources])
        if not grounding_check.passed:
            return AICopilotChatResponse(
                success=False,
                answer="Cross-patient evidence verification failed.",
                confidence="INSUFFICIENT",
            )

        sanitized_evidence = SafetyFirewall.sanitize_context_privacy(evidence_text)
        context_package = ContextBuilder.build_patient_grounded_context(
            patient=patient,
            query_text=clean_message,
            intent_type=intent.intent_type,
            evidence_text=sanitized_evidence,
            sources=[s.model_dump() for s in sources],
            confidence_level=confidence_level,
        )

        # STAGE 11: GPT-5 Nano Generation (or graceful API unavailable response if unconfigured)
        try:
            raw_answer = await self._gpt_client.generate_grounded_response(
                system_prompt=context_package.system_prompt,
                user_context_prompt=context_package.user_prompt,
                max_tokens=8000,
            )
        except Exception as exc:
            _log.error("RAG.PIPELINE.GENERATION_ERROR", error=str(exc))
            return AICopilotChatResponse(
                success=False,
                answer=f"AI Copilot is unavailable because the OpenAI API is not configured or reachable. ({str(exc)})",
                confidence="INSUFFICIENT",
            )

        # STAGE 12: Evidence Validation, Safety Firewall & Source Attribution
        output_check = SafetyFirewall.validate_output_claims(
            generated_text=raw_answer,
            retrieved_evidence_summary=sanitized_evidence,
            sources_count=len(sources),
        )

        final_answer = output_check.sanitized_content or raw_answer
        if not final_answer.strip():
            final_answer = "I couldn't find documentation regarding this topic in the available patient records."

        # Deduplicate sources
        unique_sources: Dict[str, SourceAttribution] = {}
        for s in sources:
            unique_sources[s.record_id] = s

        audit_trace = RAGAuditTrace(
            intent=intent.intent_type,
            retrieval_pathway=intent.retrieval_pathway,
            sources_count=len(unique_sources),
            confidence=confidence_level,
            grounding_passed=True,
            medical_safety_passed=output_check.passed,
        )

        _log.info(
            "RAG.PIPELINE.COMPLETED",
            patient_id=patient.id,
            intent=intent.intent_type,
            sources_count=len(unique_sources),
            confidence=confidence_level,
        )

        return AICopilotChatResponse(
            success=True,
            answer=final_answer,
            patient_id=patient.id,
            patient_name=f"{patient.first_name} {patient.last_name}",
            confidence=confidence_level if len(unique_sources) > 0 else "INSUFFICIENT",
            intent=intent.intent_type,
            sources=list(unique_sources.values()),
            audit_trace=audit_trace,
        )

    async def _execute_structured_retrieval(
        self, patient_id: str, clinician_id: str, intent: QueryRouter.QueryIntent
    ) -> StructuredEvidence:
        """Route to appropriate structured SQLite retrieval method based on query intent."""
        if intent.intent_type == "MEDICINE_FREQUENCY_QUERY" or intent.intent_type == "MEDICINE_QUERY":
            return await self._structured_retriever.retrieve_medicine_history(
                patient_id=patient_id, clinician_id=clinician_id, drug_name=intent.target_medicine
            )
        elif intent.intent_type == "TREND_QUERY":
            return await self._structured_retriever.retrieve_parameter_trend(
                patient_id=patient_id, clinician_id=clinician_id, parameter_name=intent.target_parameter
            )
        elif intent.intent_type == "VITAL_QUERY":
            return await self._structured_retriever.retrieve_vitals_history(
                patient_id=patient_id, clinician_id=clinician_id
            )
        elif intent.intent_type in ["TIMELINE_QUERY", "VISIT_QUERY"]:
            return await self._structured_retriever.retrieve_timeline_events(
                patient_id=patient_id, clinician_id=clinician_id
            )
        else:
            return await self._structured_retriever.retrieve_patient_summary(
                patient_id=patient_id, clinician_id=clinician_id
            )

    async def _handle_general_medical_info(
        self, query_text: str, target_medicine: Optional[str]
    ) -> AICopilotChatResponse:
        """Handle general medical knowledge query clearly separated from patient records."""
        context_pkg = ContextBuilder.build_general_info_context(query_text, target_medicine)
        
        try:
            answer = await self._gpt_client.generate_grounded_response(
                system_prompt=context_pkg.system_prompt,
                user_context_prompt=context_pkg.user_prompt,
            )
            formatted_answer = f"**General Medical Information** (Not specific to any patient's record):\n\n{answer}"
        except Exception as exc:
            formatted_answer = f"**General Medical Information**:\n\n{query_text}\n\n*Note: OpenAI API is currently unconfigured or unreachable.*"

        return AICopilotChatResponse(
            success=True,
            answer=formatted_answer,
            confidence="HIGH",
            intent="GENERAL_MEDICAL_INFORMATION",
            is_general_info=True,
            sources=[],
        )
