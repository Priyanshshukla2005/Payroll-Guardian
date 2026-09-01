"""Compliance knowledge retrieval service (Phase 7)."""

from typing import Any, Dict, List, Optional
from ai.explainability.explainer_v2 import DetailedEvidenceCard
from backend.dependencies.services import ModelManager
from backend.schemas.anomaly import ComplianceSourceItem, ComplianceStatusBlock
from backend.schemas.compliance import ComplianceSearchResult
from rag.metadata import AuthorityLevel, Jurisdiction, StructuredRAGResponse, Topic


class ComplianceService:
    """Provides date- and jurisdiction-aware compliance retrieval bridging anomalies with statutes."""

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager

    def retrieve_for_evidence_card(
        self,
        evidence_card: DetailedEvidenceCard,
        jurisdiction_override: Optional[str] = None,
        top_n: int = 3,
    ) -> StructuredRAGResponse:
        """Retrieve authoritative sources corresponding to an evidence card."""
        retriever = self.model_manager.retriever
        if retriever is None:
            return StructuredRAGResponse(
                query=evidence_card.human_readable_summary or "Compliance check",
                results=[],
                jurisdiction=jurisdiction_override or "INDIA",
                payroll_date="2024-06-01",
                status="RAG_UNAVAILABLE",
                no_answer_reason="RAG knowledge retrieval index is currently unavailable.",
            )

        jur_enum = None
        if jurisdiction_override:
            try:
                jur_enum = Jurisdiction(jurisdiction_override.upper())
            except ValueError:
                jur_enum = Jurisdiction.INDIA

        return retriever.retrieve_for_evidence_card(
            evidence_card=evidence_card,
            jurisdiction_override=jur_enum,
            top_n=top_n,
        )

    def search_compliance(
        self,
        query: str,
        jurisdiction: str = "INDIA",
        payroll_date: str = "2024-06-01",
        topic: Optional[str] = None,
        top_n: int = 3,
    ) -> ComplianceSearchResult:
        """Perform direct knowledge search across the compliance corpus."""
        retriever = self.model_manager.retriever
        if retriever is None:
            return ComplianceSearchResult(
                query=query,
                jurisdiction=jurisdiction,
                payroll_date=payroll_date,
                topic=topic,
                results=[],
                total_found=0,
                status="RAG_UNAVAILABLE",
                no_answer_reason="RAG knowledge retrieval index is currently unavailable.",
            )

        # Parse jurisdiction
        try:
            jur_enum = Jurisdiction(jurisdiction.upper())
        except ValueError:
            jur_enum = Jurisdiction.INDIA

        # Parse topic
        topic_enum = None
        if topic:
            try:
                topic_enum = Topic(topic.upper())
            except ValueError:
                topic_enum = None

        rag_resp: StructuredRAGResponse = retriever.retrieve(
            query=query,
            jurisdiction=jur_enum,
            payroll_date=payroll_date,
            topic=topic_enum,
            top_n=top_n,
        )

        source_items = [
            ComplianceSourceItem(
                document_id=res.document_id,
                title=res.title,
                authority_level=res.authority_level.value,
                section=res.section,
                page=res.page,
                citation=res.citation,
            )
            for res in rag_resp.results
        ]

        return ComplianceSearchResult(
            query=query,
            jurisdiction=jur_enum.value,
            payroll_date=payroll_date,
            topic=topic,
            results=source_items,
            total_found=len(source_items),
            status=rag_resp.status,
            no_answer_reason=rag_resp.no_answer_reason,
        )
