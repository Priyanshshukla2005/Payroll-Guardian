"""Authority-aware hybrid reranker for AI Payroll Guardian (Phase 5).

Combines dense semantic similarity, exact regulatory keyword matching (BM25-style),
and statutory authority tiering weights to produce grounded evidence rankings.
"""

import re
from typing import List, Tuple
from rag.metadata import AuthorityLevel, ChunkMetadata


class AuthorityAwareReranker:
    """Reranks retrieved candidate chunks prioritizing authoritative law and exact statutory terms."""

    def __init__(
        self,
        dense_weight: float = 0.55,
        lexical_weight: float = 0.30,
        authority_weight: float = 0.15,
    ):
        self.dense_weight = dense_weight
        self.lexical_weight = lexical_weight
        self.authority_weight = authority_weight

    @staticmethod
    def _compute_lexical_overlap(query: str, text: str) -> float:
        """Compute exact keyword term overlap score."""
        q_tokens = set(re.findall(r"\b[A-Za-z0-9_]{2,}\b", query.lower()))
        t_tokens = set(re.findall(r"\b[A-Za-z0-9_]{2,}\b", text.lower()))
        if not q_tokens:
            return 0.0
        overlap = len(q_tokens.intersection(t_tokens))
        return min(overlap / len(q_tokens), 1.0)

    @staticmethod
    def _get_authority_multiplier(level: AuthorityLevel) -> float:
        """Get ranking score multiplier based on statutory authority tier."""
        if level == AuthorityLevel.AUTHORITATIVE:
            return 1.0  # Full authoritative score
        elif level == AuthorityLevel.COMPANY_POLICY:
            return 0.85  # Company policy
        elif level == AuthorityLevel.REFERENCE:
            return 0.60  # Reference documentation
        return 0.40  # Unverified

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[ChunkMetadata, str, float]],
        top_n: int = 3,
    ) -> List[Tuple[ChunkMetadata, str, float, float]]:
        """Rerank candidates returning list of (metadata, text, similarity_score, final_rerank_score)."""
        if not candidates:
            return []

        scored = []
        for meta, text, sim_score in candidates:
            lex_score = self._compute_lexical_overlap(query, text)
            auth_score = self._get_authority_multiplier(meta.authority_level)

            final_score = (
                (self.dense_weight * sim_score)
                + (self.lexical_weight * lex_score)
                + (self.authority_weight * auth_score)
            )
            final_score = round(float(min(max(final_score, 0.0), 1.0)), 4)
            scored.append((meta, text, sim_score, final_score))

        # Sort descending by final rerank score
        scored.sort(key=lambda item: item[3], reverse=True)
        return scored[:top_n]
