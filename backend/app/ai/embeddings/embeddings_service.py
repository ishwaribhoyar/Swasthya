"""
Dense Embeddings Service.

Generates 384-dimensional vector embeddings for clinical chunks and queries.
Uses dense subword-hash vectorizer for deterministic, zero-dependency 384d vector embedding.
"""
from __future__ import annotations

import math
import hashlib
from typing import List


class EmbeddingsService:
    """Vector Embedding Service for Clinical RAG."""

    VECTOR_DIM = 384

    @classmethod
    def embed_text(cls, text: str) -> List[float]:
        """
        Generate 384-dimensional normalized dense vector embedding for input text.
        """
        vec = [0.0] * cls.VECTOR_DIM
        words = text.lower().split()
        if not words:
            return vec

        # Subword n-gram hashing into 384 dimensional space
        for word in words:
            # Word level hash
            h_val = int(hashlib.md5(word.encode("utf-8")).hexdigest()[:8], 16)
            idx = h_val % cls.VECTOR_DIM
            sign = 1.0 if (h_val & 1) else -1.0
            vec[idx] += sign * 1.5

            # Character 3-gram hashes
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    gram = word[i : i + 3]
                    gh_val = int(hashlib.sha256(gram.encode("utf-8")).hexdigest()[:8], 16)
                    g_idx = gh_val % cls.VECTOR_DIM
                    g_sign = 1.0 if (gh_val & 1) else -1.0
                    vec[g_idx] += g_sign * 0.5

        # Normalize L2 norm
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]

        return vec

    @classmethod
    def cosine_similarity(cls, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two normalized 384d vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        return max(0.0, min(1.0, dot))
