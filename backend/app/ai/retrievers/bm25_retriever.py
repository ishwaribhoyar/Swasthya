"""
Sparse BM25 Keyword Retriever Engine.

Provides Okapi BM25 sparse retrieval for exact medical term, lab name, and drug dosage matching.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple
from app.ai.chunking.hierarchical_chunker import ClinicalChunk


class BM25Retriever:
    """Okapi BM25 Sparse Keyword Retriever for clinical text chunks."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b

    def retrieve(self, query: str, chunks: List[ClinicalChunk], top_k: int = 15) -> List[Tuple[ClinicalChunk, float]]:
        """
        Score and rank chunks against query using Okapi BM25 algorithm.
        Returns list of (ClinicalChunk, bm25_score) tuples sorted by score descending.
        """
        if not query or not chunks:
            return []

        query_tokens = [t.lower() for t in query.split() if len(t) >= 2]
        if not query_tokens:
            return []

        N = len(chunks)
        doc_tokens_list = [[t.lower() for t in c.text.split() if len(t) >= 2] for c in chunks]
        doc_lens = [len(dt) for dt in doc_tokens_list]
        avgdl = sum(doc_lens) / max(1, N)

        # Document Frequency (DF) per query term
        df: Dict[str, int] = {}
        for q_term in query_tokens:
            df[q_term] = sum(1 for dt in doc_tokens_list if q_term in dt)

        # Inverse Document Frequency (IDF)
        idf: Dict[str, float] = {}
        for q_term, doc_freq in df.items():
            idf[q_term] = math.log((N - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)

        # Compute BM25 score per chunk
        scored_chunks: List[Tuple[ClinicalChunk, float]] = []

        for idx, chunk in enumerate(chunks):
            doc_tokens = doc_tokens_list[idx]
            doc_len = doc_lens[idx]
            score = 0.0

            # Term frequencies
            tf_map: Dict[str, int] = {}
            for t in doc_tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            for q_term in query_tokens:
                tf = tf_map.get(q_term, 0)
                if tf > 0:
                    num = tf * (self.k1 + 1.0)
                    den = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avgdl))
                    score += idf[q_term] * (num / den)

            if score > 0:
                scored_chunks.append((chunk, score))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]
