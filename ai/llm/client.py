"""High-level Client Facade for the AI Payroll Guardian LLM & Assistant Layer (Phase 6).

Provides an integrated, production-ready interface bridging Anomaly Evidence,
RAG Knowledge Retrieval, Grounded Explanations, and Conversational Q&A.
"""

from typing import Any, Dict, List, Optional, Union
import pandas as pd

from ai.explainability.explainer_v2 import DetailedEvidenceCard, PayrollExplainerV2
from ai.llm.assistant import PayrollAIAssistant
from ai.llm.context_builder import ContextBuilder
from ai.llm.grounded_generator import GroundedExplanationGenerator
from ai.llm.provider import BaseLLMProvider, ProviderConfig, ProviderFactory
from ai.llm.response_schema import (
    AssistantQueryResponse,
    PayrollExplanationResponse,
)
from ai.llm.validator import PayrollLLMValidator
from rag.metadata import Jurisdiction, StructuredRAGResponse
from rag.retrieval.retriever import PayrollRAGRetriever


class PayrollLLMClient:
    """Unified client for generating grounded compliance explanations and interactive Q&A."""

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        retriever: Optional[PayrollRAGRetriever] = None,
        explainer: Optional[PayrollExplainerV2] = None,
    ):
        self.provider = provider or ProviderFactory.create_provider()
        self.retriever = retriever
        self.explainer = explainer or PayrollExplainerV2()
        self.context_builder = ContextBuilder()
        self.validator = PayrollLLMValidator()
        self.generator = GroundedExplanationGenerator(
            provider=self.provider,
            context_builder=self.context_builder,
            validator=self.validator,
        )
        self.assistant = PayrollAIAssistant(
            provider=self.provider,
            context_builder=self.context_builder,
            validator=self.validator,
        )

    def explain_evidence(
        self,
        evidence_card: Union[DetailedEvidenceCard, Dict[str, Any]],
        rag_response: Optional[Union[StructuredRAGResponse, Dict[str, Any]]] = None,
        jurisdiction_override: Optional[Jurisdiction] = None,
        raw_record: Optional[Dict[str, Any]] = None,
    ) -> PayrollExplanationResponse:
        """Generate a complete grounded explanation for a Phase 4 evidence card."""
        # Auto-retrieve RAG knowledge if retriever is available and no RAG response provided
        final_rag = rag_response
        if final_rag is None and self.retriever is not None:
            final_rag = self.retriever.retrieve_for_evidence_card(
                evidence_card=evidence_card,
                jurisdiction_override=jurisdiction_override,
            )

        return self.generator.explain(
            evidence_card=evidence_card,
            rag_response=final_rag,
            raw_record=raw_record,
        )

    def explain_record(
        self,
        record: Union[pd.Series, Dict[str, Any]],
        risk_score: float,
        predicted_anomaly_types: Optional[List[str]] = None,
        rule_violations: Optional[List[str]] = None,
        jurisdiction_override: Optional[Jurisdiction] = None,
    ) -> PayrollExplanationResponse:
        """End-to-end convenience method: raw record -> evidence card -> RAG -> LLM explanation."""
        evidence_card = self.explainer.explain(
            record=record,
            risk_score=risk_score,
            predicted_anomaly_types=predicted_anomaly_types,
            rule_violations=rule_violations,
        )
        raw_dict = record.to_dict() if isinstance(record, pd.Series) else dict(record)
        return self.explain_evidence(
            evidence_card=evidence_card,
            jurisdiction_override=jurisdiction_override,
            raw_record=raw_dict,
        )

    def ask(
        self,
        question: str,
        evidence_card: Union[DetailedEvidenceCard, Dict[str, Any]],
        rag_response: Optional[Union[StructuredRAGResponse, Dict[str, Any]]] = None,
        raw_record: Optional[Dict[str, Any]] = None,
    ) -> AssistantQueryResponse:
        """Query the grounded payroll assistant regarding an evidence card."""
        final_rag = rag_response
        if final_rag is None and self.retriever is not None:
            # Query-first retrieval for statutory/compliance terms in question
            q_rag = self.retriever.retrieve(query=question, top_n=3)
            card_rag = self.retriever.retrieve_for_evidence_card(evidence_card=evidence_card)

            if q_rag and q_rag.total_found > 0:
                # Merge or prioritize question-targeted statutory chunks
                if card_rag and card_rag.total_found > 0:
                    combined_results = list(q_rag.results)
                    seen_docs = {r.document_id for r in combined_results}
                    for cr in card_rag.results:
                        if cr.document_id not in seen_docs:
                            combined_results.append(cr)
                            seen_docs.add(cr.document_id)
                    q_rag.results = combined_results[:4]
                    q_rag.total_found = len(q_rag.results)
                final_rag = q_rag
            else:
                final_rag = card_rag

        return self.assistant.ask(
            question=question,
            evidence_card=evidence_card,
            rag_response=final_rag,
            raw_record=raw_record,
        )

    def get_fallback_explanation(
        self,
        evidence_card: Union[DetailedEvidenceCard, Dict[str, Any]],
        rag_response: Optional[Union[StructuredRAGResponse, Dict[str, Any]]] = None,
    ) -> PayrollExplanationResponse:
        """Direct deterministic fallback explanation without LLM synthesis."""
        structured_input = self.context_builder.build_structured_input(
            evidence_card=evidence_card,
            rag_response=rag_response,
        )
        return self.generator.generate_fallback_explanation(
            structured_input=structured_input,
            fallback_reason="User requested direct deterministic fallback",
        )
