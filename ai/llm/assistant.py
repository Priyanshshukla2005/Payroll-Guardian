"""Payroll Administrator AI Assistant for grounded interactive inquiry (Phase 6).

Provides an interactive Q&A interface for payroll administrators strictly grounded
in structured anomaly evidence, retrieved RAG knowledge, and organizational policies.
"""

import time
from typing import Any, Dict, List, Optional, Union

from ai.explainability.explainer_v2 import DetailedEvidenceCard
from ai.llm.context_builder import ContextBuilder, StructuredLLMInput
from ai.llm.prompts import (
    PAYROLL_ADMIN_QA_PROMPT,
    SYSTEM_PROMPT_GROUNDED_EXPLAINER,
)
from ai.llm.provider import BaseLLMProvider, ProviderFactory
from ai.llm.response_schema import AssistantQueryResponse, CitationReference
from ai.llm.safety import PromptInjectionDefense, RefusalEngine
from ai.llm.validator import PayrollLLMValidator
from rag.metadata import StructuredRAGResponse


class PayrollAIAssistant:
    """Conversational assistant for payroll administrators grounded in anomaly and compliance evidence."""

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        context_builder: Optional[ContextBuilder] = None,
        validator: Optional[PayrollLLMValidator] = None,
    ):
        self.provider = provider or ProviderFactory.create_provider()
        self.context_builder = context_builder or ContextBuilder()
        self.validator = validator or PayrollLLMValidator()

    def ask(
        self,
        question: str,
        evidence_card: Union[DetailedEvidenceCard, Dict[str, Any]],
        rag_response: Optional[Union[StructuredRAGResponse, Dict[str, Any]]] = None,
        raw_record: Optional[Dict[str, Any]] = None,
    ) -> AssistantQueryResponse:
        """Answer a grounded question from a payroll administrator."""
        start_time = time.perf_counter()

        # 1. Prompt Injection Defense
        is_injection, injection_msg = PromptInjectionDefense.detect_injection(question)
        if is_injection:
            return AssistantQueryResponse(
                question=question,
                answer="Request rejected: Input contains prohibited system instruction overrides or autonomous action commands.",
                grounded_facts=[],
                evidence_sources=[],
                citations=[],
                category_distinction={
                    "statutory_requirements": [],
                    "company_policies": [],
                    "analytical_observations": [],
                },
                suggested_next_steps=["Please submit inquiries strictly regarding payroll verification."],
                uncertainty_or_refusal=injection_msg,
                generation_metadata={"safety_refusal": True, "latency_ms": 0.1},
            )

        # 2. Build structured input context
        structured_input = self.context_builder.build_structured_input(
            evidence_card=evidence_card,
            rag_response=rag_response,
            raw_record=raw_record,
        )

        context_str = self.context_builder.format_prompt_context(structured_input)
        prompt = PAYROLL_ADMIN_QA_PROMPT.format(
            context=context_str,
            question=question,
            query_tag="ADMIN_QUERY",
        )

        # 3. Call LLM provider
        try:
            llm_resp = self.provider.generate_structured(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT_GROUNDED_EXPLAINER,
            )
        except Exception as e:
            # Fallback response
            return self._generate_fallback_answer(question, structured_input, str(e))

        # 4. Validate output
        val_result = self.validator.validate_assistant_response(
            raw_output=llm_resp.structured_data or llm_resp.content,
            structured_input=structured_input,
        )

        total_latency = (time.perf_counter() - start_time) * 1000.0
        if val_result.is_valid and isinstance(val_result.sanitized_response, AssistantQueryResponse):
            resp = val_result.sanitized_response
            resp.generation_metadata = {
                "provider": llm_resp.provider,
                "model": llm_resp.model,
                "prompt_tokens": llm_resp.prompt_tokens,
                "completion_tokens": llm_resp.completion_tokens,
                "total_tokens": llm_resp.total_tokens,
                "latency_ms": round(total_latency, 2),
            }
            return resp

        return self._generate_fallback_answer(
            question, structured_input, f"Validation failed: {'; '.join(val_result.errors)}"
        )

    def _generate_fallback_answer(
        self,
        question: str,
        structured_input: StructuredLLMInput,
        reason: str,
    ) -> AssistantQueryResponse:
        """Generate a deterministic fallback answer when LLM is unavailable or invalid."""
        signals = structured_input.evidence.top_signals or ["Variance detected in payroll calculation."]
        anoms = structured_input.detection.anomaly_types or ["ANOMALY"]
        citations = [
            CitationReference(
                document_id=k.document_id,
                page=k.page,
                section=k.section,
                citation=k.citation,
            )
            for k in structured_input.retrieved_knowledge
        ]

        stat_reqs = [
            f"{k.title}: {k.section or 'Statutory Section'}"
            for k in structured_input.retrieved_knowledge
            if "AUTHORITATIVE" in k.authority_level
        ]
        comp_pols = [
            f"{k.title}: {k.section or 'Internal SOP'}"
            for k in structured_input.retrieved_knowledge
            if "COMPANY_POLICY" in k.authority_level
        ]

        answer = (
            f"Employee {structured_input.employee_context.employee_id} was flagged for [{', '.join(anoms)}] "
            f"with {structured_input.detection.confidence} confidence. "
            f"Key observations: {'; '.join(signals[:2])}."
        )

        return AssistantQueryResponse(
            question=question,
            answer=answer,
            grounded_facts=signals[:3],
            evidence_sources=[k.title for k in structured_input.retrieved_knowledge],
            citations=citations,
            category_distinction={
                "statutory_requirements": stat_reqs,
                "company_policies": comp_pols,
                "analytical_observations": signals,
            },
            suggested_next_steps=[
                "Review employee timesheet and biometric attendance records",
                "Verify salary register against applicable deduction ceilings",
            ],
            uncertainty_or_refusal=f"Deterministic fallback applied ({reason})",
            generation_metadata={"fallback_mode": True, "latency_ms": 0.5},
        )
