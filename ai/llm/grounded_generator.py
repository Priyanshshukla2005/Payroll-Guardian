"""Grounded explanation generator with auto-correction retries and fallback orchestration (Phase 6).

Coordinates ContextBuilder, Provider, Validator, Safety, and Fallback layers.
"""

import time
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

from ai.explainability.explainer_v2 import DetailedEvidenceCard
from ai.llm.context_builder import ContextBuilder, StructuredLLMInput
from ai.llm.prompts import (
    ANOMALY_EXPLANATION_PROMPT,
    CORRECTION_PROMPT,
    SYSTEM_PROMPT_GROUNDED_EXPLAINER,
)
from ai.llm.provider import BaseLLMProvider, ProviderConfig, ProviderFactory
from ai.llm.response_schema import (
    CitationReference,
    ExplanationSeverity,
    GroundedAnomalyItem,
    PayrollExplanationResponse,
)
from ai.llm.safety import RefusalEngine
from ai.llm.validator import PayrollLLMValidator, ValidationResult
from rag.metadata import StructuredRAGResponse


class GroundedExplanationGenerator:
    """End-to-end grounded LLM explanation pipeline with fallback guarantees."""

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        context_builder: Optional[ContextBuilder] = None,
        validator: Optional[PayrollLLMValidator] = None,
        enable_retries: bool = True,
    ):
        self.provider = provider or ProviderFactory.create_provider()
        self.context_builder = context_builder or ContextBuilder()
        self.validator = validator or PayrollLLMValidator()
        self.enable_retries = enable_retries

    def generate_fallback_explanation(
        self,
        structured_input: StructuredLLMInput,
        fallback_reason: str = "Deterministic system fallback",
    ) -> PayrollExplanationResponse:
        """Construct a 100% deterministic, audit-compliant fallback explanation without LLM synthesis."""
        inp = structured_input
        anoms = inp.detection.anomaly_types or ["ANOMALY"]
        emp_id = inp.employee_context.employee_id
        period = inp.employee_context.payroll_period
        severity = inp.determined_severity

        # 1. Summary
        summary = (
            f"Employee {emp_id} ({period}) flagged with {inp.detection.confidence} confidence "
            f"for [{', '.join(anoms)}]. Severity assigned: {severity.value}."
        )

        # 2. Why flagged
        why = [f"Record triggered anomaly detection for {a} based on historical and peer baseline variances." for a in anoms]
        for v in inp.evidence.rule_violations:
            why.append(f"Deterministic Rule Violation: {v}")

        # 3. Evidence
        evidence = inp.evidence.top_signals or ["Analytical variance detected across payroll feature dimensions."]

        # 4. Citations & compliance context
        citations: List[CitationReference] = []
        compliance_context: List[str] = []
        for k in inp.retrieved_knowledge:
            citations.append(
                CitationReference(
                    document_id=k.document_id,
                    page=k.page,
                    section=k.section,
                    citation=k.citation,
                )
            )
            compliance_context.append(f"{k.title} ({k.authority_level}): {k.section or 'General Clause'} applies.")

        # 5. Handle missing RAG sources / unknown jurisdiction
        uncertainty = None
        if inp.rag_status == "JURISDICTION_UNKNOWN":
            uncertainty = RefusalEngine.get_unknown_jurisdiction_refusal()
            compliance_context = ["Jurisdiction is UNKNOWN. Cannot determine applicable statutory regulation."]
        elif inp.rag_status == "NO_RELIABLE_SOURCE_FOUND" or not citations:
            uncertainty = RefusalEngine.get_missing_source_refusal(anoms[0] if anoms else None)
            compliance_context = ["No authoritative compliance source could be retrieved for this anomaly type."]

        # 6. Recommended Actions
        actions = []
        if any("PF" in a for a in anoms):
            actions.append("Verify employee's statutory basic salary wage basis and 12% EPFO deduction calculation.")
        if any("ATTENDANCE" in a or "LEAVE" in a for a in anoms):
            actions.append("Cross-reference biometric attendance records with working days in month.")
        if any("OVERTIME" in a for a in anoms):
            actions.append("Confirm approved overtime hours and manager sign-off against the 1.5x basic wage policy.")
        if not actions:
            actions.append("Perform manual review of the employee payroll calculation worksheet.")

        # 7. Breakdowns
        breakdowns = [
            GroundedAnomalyItem(
                anomaly_type=a,
                severity=severity,
                description=f"Flagged for {a.replace('_', ' ').title()}.",
                evidence_points=evidence[:2],
                applicable_rule_or_policy=citations[0].citation if citations else None,
            )
            for a in anoms
        ]

        return PayrollExplanationResponse(
            title=f"Payroll anomaly detected: {', '.join(anoms)}",
            severity=severity,
            summary=summary,
            why_flagged=why,
            evidence=evidence,
            compliance_context=compliance_context or ["Statistical variance observed."],
            recommended_actions=actions,
            citations=citations,
            anomaly_breakdowns=breakdowns,
            uncertainty=uncertainty,
            disclaimer="AI-assisted payroll analysis. Not legal advice. Must be verified with official statutory regulations and internal policies.",
            generation_metadata={
                "fallback_mode": True,
                "fallback_reason": fallback_reason,
                "provider": "deterministic_fallback",
                "model": "rule_synthesizer_v1",
                "latency_ms": 0.5,
            },
        )

    def explain(
        self,
        evidence_card: Union[DetailedEvidenceCard, Dict[str, Any]],
        rag_response: Optional[Union[StructuredRAGResponse, Dict[str, Any]]] = None,
        raw_record: Optional[Dict[str, Any]] = None,
    ) -> PayrollExplanationResponse:
        """Generate a validated, grounded explanation for a detected anomaly."""
        start_time = time.perf_counter()

        # 1. Build structured input
        structured_input = self.context_builder.build_structured_input(
            evidence_card=evidence_card,
            rag_response=rag_response,
            raw_record=raw_record,
        )

        # 2. Format context and prompt
        context_str = self.context_builder.format_prompt_context(structured_input)
        prompt = ANOMALY_EXPLANATION_PROMPT.format(
            context=context_str,
            severity=structured_input.determined_severity.value,
        )

        # 3. Invoke provider
        try:
            llm_resp = self.provider.generate_structured(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT_GROUNDED_EXPLAINER,
            )
        except Exception as e:
            # Safe fallback on network or provider exception
            return self.generate_fallback_explanation(
                structured_input=structured_input,
                fallback_reason=f"LLM Provider invocation failed: {e}",
            )

        # 4. Validate output
        val_result = self.validator.validate_anomaly_explanation(
            raw_output=llm_resp.structured_data or llm_resp.content,
            structured_input=structured_input,
        )

        # 5. Retry on failure if enabled
        if not val_result.is_valid and self.enable_retries:
            allowed_ids = [k.document_id for k in structured_input.retrieved_knowledge]
            correction_prompt = CORRECTION_PROMPT.format(
                error_message="; ".join(val_result.errors),
                previous_output=llm_resp.content,
                allowed_doc_ids=allowed_ids,
                assigned_severity=structured_input.determined_severity.value,
            )
            try:
                retry_resp = self.provider.generate_structured(
                    prompt=correction_prompt,
                    system_prompt=SYSTEM_PROMPT_GROUNDED_EXPLAINER,
                )
                val_result = self.validator.validate_anomaly_explanation(
                    raw_output=retry_resp.structured_data or retry_resp.content,
                    structured_input=structured_input,
                )
                llm_resp = retry_resp
            except Exception:
                pass  # Fall through to fallback or sanitized result

        # 6. If valid, return model with metadata
        total_latency = (time.perf_counter() - start_time) * 1000.0
        if val_result.is_valid and isinstance(val_result.sanitized_response, PayrollExplanationResponse):
            resp = val_result.sanitized_response
            resp.generation_metadata = {
                "fallback_mode": False,
                "provider": llm_resp.provider,
                "model": llm_resp.model,
                "prompt_tokens": llm_resp.prompt_tokens,
                "completion_tokens": llm_resp.completion_tokens,
                "total_tokens": llm_resp.total_tokens,
                "latency_ms": round(total_latency, 2),
                "citation_validity_rate": val_result.citation_validity_rate,
                "groundedness_score": val_result.groundedness_score,
                "warnings": val_result.warnings,
            }
            return resp

        # 7. Fallback if validation still failed
        return self.generate_fallback_explanation(
            structured_input=structured_input,
            fallback_reason=f"Validation failed: {'; '.join(val_result.errors)}",
        )
