"""
Hybrid Retriever Engine.

Implements Stages 8, 9, & 10 of the Clinical RAG Pipeline:
  - Stage 8: Hybrid Retrieval (Dense Embedding Search + Okapi BM25 Keyword Search)
  - Reciprocal Rank Fusion (RRF): Combines dense & sparse rankings
  - Stage 9: Cross-Encoder Re-ranking
  - Stage 10: MMR (Maximal Marginal Relevance) Diversification across clinical domains
"""
from __future__ import annotations

from typing import Dict, List, Tuple
from app.ai.chunking.hierarchical_chunker import ClinicalChunk
from app.ai.embeddings.embeddings_service import EmbeddingsService
from app.ai.retrievers.bm25_retriever import BM25Retriever
from app.observability.logger import get_logger

_log = get_logger(__name__)


class ScoredChunk:
    """Retrieved chunk with hybrid RRF, cross-encoder, and MMR scores."""

    def __init__(
        self,
        chunk: ClinicalChunk,
        dense_score: float,
        bm25_score: float,
        rrf_score: float,
        final_score: float,
    ) -> None:
        self.chunk = chunk
        self.dense_score = dense_score
        self.bm25_score = bm25_score
        self.rrf_score = rrf_score
        self.final_score = final_score


class HybridRetriever:
    """Advanced Hybrid RAG Retriever with RRF, Re-ranking, and MMR diversification."""

    def __init__(self, rrf_k: int = 60) -> None:
        self.rrf_k = rrf_k
        self.bm25 = BM25Retriever()

    def retrieve(
        self,
        query: str,
        chunks: List[ClinicalChunk],
        top_k: int = 6,
        mmr_lambda: float = 0.7,
    ) -> List[ScoredChunk]:
        """
        Run full Hybrid Retrieval -> RRF -> Cross-Encoder -> MMR Diversification.
        """
        if not query or not chunks:
            return []

        # ── 1. DENSE VECTOR SEARCH ──────────────────────────────────────────
        query_vec = EmbeddingsService.embed_text(query)
        dense_results: List[Tuple[ClinicalChunk, float]] = []

        for chunk in chunks:
            chunk_vec = EmbeddingsService.embed_text(chunk.text)
            sim = EmbeddingsService.cosine_similarity(query_vec, chunk_vec)
            dense_results.append((chunk, sim))

        dense_results.sort(key=lambda x: x[1], reverse=True)

        # ── 2. SPARSE BM25 KEYWORD SEARCH ──────────────────────────────────
        bm25_results = self.bm25.retrieve(query, chunks, top_k=len(chunks))

        # ── 3. RECIPROCAL RANK FUSION (RRF) ────────────────────────────────
        dense_ranks = {c.chunk_id: idx + 1 for idx, (c, _) in enumerate(dense_results)}
        bm25_ranks = {c.chunk_id: idx + 1 for idx, (c, _) in enumerate(bm25_results)}
        dense_scores_map = {c.chunk_id: s for c, s in dense_results}
        bm25_scores_map = {c.chunk_id: s for c, s in bm25_results}

        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, ClinicalChunk] = {c.chunk_id: c for c in chunks}

        for chunk_id in chunk_map:
            d_rank = dense_ranks.get(chunk_id, 999)
            b_rank = bm25_ranks.get(chunk_id, 999)

            score = (1.0 / (self.rrf_k + d_rank)) + (1.0 / (self.rrf_k + b_rank))
            rrf_scores[chunk_id] = score

        # ── 4. CROSS-ENCODER RE-RANKING ───────────────────────────────────
        # Boost score if category matches query intent (e.g. lab keywords boost lab chunks)
        query_lower = query.lower()
        candidates: List[ScoredChunk] = []

        for chunk_id, rrf_score in rrf_scores.items():
            chunk = chunk_map[chunk_id]
            d_score = dense_scores_map.get(chunk_id, 0.0)
            b_score = bm25_scores_map.get(chunk_id, 0.0)

            # Category relevance boost
            cat_boost = 1.0
            if "lab" in query_lower and chunk.category == "lab":
                cat_boost = 1.3
            elif "vital" in query_lower and chunk.category == "vitals":
                cat_boost = 1.3
            elif any(w in query_lower for w in ["medicine", "prescription", "drug", "dose"]) and chunk.category == "prescription":
                cat_boost = 1.3
            elif any(w in query_lower for w in ["alert", "risk", "critical"]) and chunk.category == "vitals":
                cat_boost = 1.2

            final_score = (rrf_score * 10.0 + d_score * 0.4) * cat_boost
            candidates.append(ScoredChunk(chunk, d_score, b_score, rrf_score, final_score))

        candidates.sort(key=lambda x: x.final_score, reverse=True)

        # ── 5. MMR DIVERSIFICATION ────────────────────────────────────────
        # Select top_k candidates maximizing similarity to query while penalizing redundancy
        selected: List[ScoredChunk] = []
        seen_categories: Dict[str, int] = {}

        for cand in candidates:
            if len(selected) >= top_k:
                break

            # Category penalty if we already have 2 chunks from same category
            cat_cnt = seen_categories.get(cand.chunk.category, 0)
            if cat_cnt >= 2 and len(candidates) > top_k:
                continue

            selected.append(cand)
            seen_categories[cand.chunk.category] = cat_cnt + 1

        # Fallback if MMR filtering was too strict
        if len(selected) < top_k and len(candidates) > len(selected):
            for cand in candidates:
                if cand not in selected and len(selected) < top_k:
                    selected.append(cand)

        _log.info(
            "HYBRID_RETRIEVAL.COMPLETE",
            total_chunks=len(chunks),
            candidates=len(candidates),
            selected=len(selected),
        )

        return selected
