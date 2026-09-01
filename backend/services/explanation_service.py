"""Grounded LLM explanation and assistant service (Phase 7)."""

from typing import Any, Dict, Optional
from ai.explainability.explainer_v2 import DetailedEvidenceCard
from ai.llm.client import PayrollLLMClient
from ai.llm.response_schema import AssistantQueryResponse, PayrollExplanationResponse
from backend.dependencies.services import ModelManager
from backend.schemas.anomaly import ExplanationItem
from backend.schemas.assistant import AssistantQueryResponseSchema, ComplianceSourceItem
from rag.metadata import StructuredRAGResponse


class ExplanationService:
    """Orchestrates grounded explanation generation and conversational Q&A."""

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager

    def explain_anomaly(
        self,
        evidence_card: DetailedEvidenceCard,
        rag_response: Optional[StructuredRAGResponse] = None,
        raw_record: Optional[Dict[str, Any]] = None,
    ) -> ExplanationItem:
        """Generate a validated, grounded explanation for a detected anomaly."""
        llm_client: Optional[PayrollLLMClient] = self.model_manager.llm_client
        if llm_client is None:
            # Deterministic fallback when LLM service is offline
            actions = ["Verify attendance logs", "Audit statutory deductions with finance"]
            return ExplanationItem(
                title=f"Anomaly in {', '.join(evidence_card.anomaly_types)}",
                summary=f"Record flagged with risk score {evidence_card.risk_score:.2f}. (Deterministic rule fallback - LLM offline).",
                why_flagged=evidence_card.top_signals or ["Statistical anomaly detected in payroll variables."],
                recommended_actions=actions,
                uncertainty="LLM offline; explanation generated via deterministic fallback logic.",
                fallback_mode=True,
            )

        try:
            exp_resp: PayrollExplanationResponse = llm_client.explain_evidence(
                evidence_card=evidence_card,
                rag_response=rag_response,
                raw_record=raw_record,
            )

            is_fallback = bool(exp_resp.generation_metadata and exp_resp.generation_metadata.get("fallback_mode"))

            return ExplanationItem(
                title=exp_resp.title,
                summary=exp_resp.summary,
                why_flagged=exp_resp.why_flagged,
                recommended_actions=exp_resp.recommended_actions,
                uncertainty=exp_resp.uncertainty,
                fallback_mode=is_fallback,
            )
        except Exception as e:
            return ExplanationItem(
                title=f"Anomaly: {', '.join(evidence_card.anomaly_types)}",
                summary=f"Automated explanation fallback activated due to LLM provider exception: {str(e)}",
                why_flagged=evidence_card.top_signals or ["Anomaly detected."],
                recommended_actions=["Manual payroll verification required"],
                uncertainty="LLM processing exception; deterministic fallback applied.",
                fallback_mode=True,
            )

    def answer_assistant_query(
        self,
        question: str,
        evidence_card: Optional[DetailedEvidenceCard] = None,
        rag_response: Optional[StructuredRAGResponse] = None,
        raw_record: Optional[Dict[str, Any]] = None,
    ) -> AssistantQueryResponseSchema:
        """Answer an administrator's query using grounded knowledge."""
        llm_client: PayrollLLMClient = self.model_manager.llm_client

        # If no specific evidence card is provided, create a general context card
        card = evidence_card
        if card is None:
            card = DetailedEvidenceCard(
                employee_id="GENERAL_INQUIRY",
                payroll_month="2024-06",
                risk_score=0.0,
                confidence="LOW",
                top_signals=["General compliance policy inquiry"],
                historical_comparison={},
                peer_comparison={},
                rule_violations=[],
                anomaly_types=["INQUIRY"],
                human_readable_summary="General policy inquiry",
            )

        resp: AssistantQueryResponse = llm_client.ask(
            question=question,
            evidence_card=card,
            rag_response=rag_response,
            raw_record=raw_record,
        )

        citations = [
            ComplianceSourceItem(
                document_id=c.document_id,
                section=c.section,
                page=c.page,
                citation=c.citation,
            )
            for c in resp.citations
        ]

        return AssistantQueryResponseSchema(
            question=resp.question,
            answer=resp.answer,
            grounded_facts=resp.grounded_facts,
            evidence_sources=resp.evidence_sources,
            citations=citations,
            category_distinction=resp.category_distinction,
            suggested_next_steps=resp.suggested_next_steps,
            uncertainty_or_refusal=resp.uncertainty_or_refusal,
            disclaimer=resp.disclaimer,
        )
