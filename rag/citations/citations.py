"""Traceable citation generator for AI Payroll Guardian RAG (Phase 5).

Constructs audit-ready citations embedding document IDs, section numbers,
versions, jurisdictions, and effective date intervals.
"""

from typing import Optional
from rag.metadata import ChunkMetadata, RetrievedChunk


class CitationFormatter:
    """Formats standardized, auditable citations for retrieved knowledge chunks."""

    @staticmethod
    def format_citation(meta: ChunkMetadata) -> str:
        """Generate standardized citation tag."""
        sec_str = f", Section: {meta.section}" if meta.section else ""
        page_str = f", Page: {meta.page_number}" if meta.page_number else ""
        eff_until = meta.effective_until if meta.effective_until else "CURRENT"
        eff_str = f", Effective: {meta.effective_from} to {eff_until}"

        citation = (
            f"[{meta.document_id}{sec_str}{page_str}, "
            f"Version: {meta.document_version}, "
            f"Jurisdiction: {meta.jurisdiction.value}{eff_str}]"
        )
        return citation

    @staticmethod
    def format_footnote(retrieved: RetrievedChunk) -> str:
        """Generate detailed markdown footnote for human auditor review."""
        eff_until = retrieved.effective_until if retrieved.effective_until else "CURRENT"
        return (
            f"> **Citation**: `{retrieved.citation}`\n"
            f"> **Source**: {retrieved.source_name} ({retrieved.authority_level.value})\n"
            f"> **Applicability**: {retrieved.jurisdiction.value} ({retrieved.effective_from} → {eff_until})\n"
            f"> **Relevance Score**: {retrieved.rerank_score * 100:.1f}%\n"
        )
