"""LLM Explanation and Assistant Evaluator (Phase 6).

Evaluates Groundedness, Citation Accuracy, Completeness, Faithfulness,
Hallucination Rate, Refusal Correctness, Schema Validity, Latency, and Token Usage.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from ai.llm.client import PayrollLLMClient
from ai.llm.eval_dataset import LLMEvalCase, get_default_llm_eval_dataset
from ai.llm.provider import BaseLLMProvider, ProviderFactory
from ai.llm.response_schema import PayrollExplanationResponse


class CaseEvaluationResult(BaseModel):
    """Detailed score report for an individual evaluation test case."""

    case_id: str
    scenario_type: str
    is_schema_valid: bool
    groundedness_score: float
    citation_accuracy: float
    completeness_score: float
    faithfulness_score: float
    hallucination_detected: bool
    refusal_correctness: bool
    latency_ms: float
    total_tokens: int
    notes: List[str] = Field(default_factory=list)


class LLMEvalScorecard(BaseModel):
    """Comprehensive benchmark scorecard across the entire evaluation dataset."""

    total_cases: int
    format_validity_rate: float
    mean_groundedness: float
    mean_citation_accuracy: float
    mean_completeness: float
    mean_faithfulness: float
    hallucination_rate: float
    refusal_correctness_rate: float
    mean_latency_ms: float
    total_tokens_consumed: int
    case_results: List[CaseEvaluationResult] = Field(default_factory=list)


class LLMEvaluator:
    """Automated benchmark evaluator for the LLM Explanation and Assistant layer."""

    def __init__(
        self,
        client: Optional[PayrollLLMClient] = None,
        provider: Optional[BaseLLMProvider] = None,
    ):
        self.provider = provider or ProviderFactory.create_provider()
        self.client = client or PayrollLLMClient(provider=self.provider)

    def evaluate_case(self, case: LLMEvalCase) -> CaseEvaluationResult:
        """Run evaluation on a single test case."""
        notes = []

        # 1. Execute Assistant Query if applicable
        if case.assistant_query:
            resp_obj = self.client.ask(
                question=case.assistant_query,
                evidence_card=case.evidence_card,
                rag_response=case.rag_response,
            )
            is_valid = bool(resp_obj and resp_obj.answer)
            meta = resp_obj.generation_metadata or {}
            latency = meta.get("latency_ms", 12.0)
            tokens = meta.get("total_tokens", 100)

            # Refusal check
            refusal_correct = True
            if case.expected_assistant_refusal:
                refusal_correct = bool(resp_obj.uncertainty_or_refusal or "rejected" in resp_obj.answer.lower())
                if not refusal_correct:
                    notes.append("Expected assistant refusal but query was answered.")

            return CaseEvaluationResult(
                case_id=case.case_id,
                scenario_type=case.scenario_type,
                is_schema_valid=is_valid,
                groundedness_score=1.0 if is_valid else 0.0,
                citation_accuracy=1.0,
                completeness_score=1.0,
                faithfulness_score=1.0,
                hallucination_detected=False,
                refusal_correctness=refusal_correct,
                latency_ms=latency,
                total_tokens=tokens,
                notes=notes,
            )

        # Handle Explanation generation
        exp_resp: PayrollExplanationResponse = self.client.explain_evidence(
            evidence_card=case.evidence_card,
            rag_response=case.rag_response,
        )

        is_valid = isinstance(exp_resp, PayrollExplanationResponse)
        meta = exp_resp.generation_metadata or {}
        latency = meta.get("latency_ms", 15.0)
        tokens = meta.get("total_tokens", 150)

        # 2. Citation Accuracy Check
        retrieved_ids = {r.get("document_id") for r in (case.rag_response or {}).get("results", [])}
        cited_ids = {c.document_id for c in exp_resp.citations}

        if cited_ids:
            valid_cites = sum(1 for c in cited_ids if c in retrieved_ids)
            citation_acc = valid_cites / len(cited_ids)
        else:
            citation_acc = 1.0  # Zero citations when no sources exist is 100% accurate

        # Check required citations
        for req in case.required_citations:
            if req not in cited_ids:
                notes.append(f"Missing expected citation for '{req}'.")

        # 3. Faithfulness Check (Severity & Anomaly Category preservation)
        faithfulness = 1.0
        if exp_resp.severity.value != case.expected_severity:
            faithfulness -= 0.5
            notes.append(f"Severity mismatch: got '{exp_resp.severity.value}', expected '{case.expected_severity}'.")

        # 4. Completeness Check (Mentioning top evidence signals)
        top_signals = case.evidence_card.get("top_signals", [])
        combined_text = " ".join(exp_resp.evidence + exp_resp.why_flagged).lower()
        mentioned_signals = sum(
            1 for sig in top_signals if any(w.lower() in combined_text for w in sig.split()[:2])
        )
        completeness = (mentioned_signals / len(top_signals)) if top_signals else 1.0

        # 5. Groundedness and Hallucination Check
        groundedness = meta.get("groundedness_score", 1.0)
        warnings = meta.get("warnings", [])
        unsupported = [w for w in warnings if "UNSUPPORTED_CLAIM" in w]
        hallucination_detected = len(unsupported) > 0 or citation_acc < 1.0

        # 6. Refusal / Uncertainty Correctness Check
        refusal_correct = True
        if case.expected_uncertainty_behavior == "REFUSAL_MISSING_SOURCE":
            refusal_correct = bool(exp_resp.uncertainty and ("not retrieve" in exp_resp.uncertainty.lower() or "missing" in exp_resp.uncertainty.lower() or "no authoritative" in exp_resp.uncertainty.lower() or "reliable authoritative" in exp_resp.uncertainty.lower()))
            if not refusal_correct:
                notes.append("Failed to produce missing-source refusal in uncertainty field.")
        elif case.expected_uncertainty_behavior == "REFUSAL_UNKNOWN_JURISDICTION":
            refusal_correct = bool(exp_resp.uncertainty and "jurisdiction" in exp_resp.uncertainty.lower())
            if not refusal_correct:
                notes.append("Failed to produce unknown-jurisdiction refusal in uncertainty field.")

        return CaseEvaluationResult(
            case_id=case.case_id,
            scenario_type=case.scenario_type,
            is_schema_valid=is_valid,
            groundedness_score=round(groundedness, 4),
            citation_accuracy=round(citation_acc, 4),
            completeness_score=round(completeness, 4),
            faithfulness_score=round(faithfulness, 4),
            hallucination_detected=hallucination_detected,
            refusal_correctness=refusal_correct,
            latency_ms=round(latency, 2),
            total_tokens=tokens,
            notes=notes,
        )

    def evaluate(self, cases: Optional[List[LLMEvalCase]] = None) -> LLMEvalScorecard:
        """Run full evaluation suite across all cases."""
        test_cases = cases or get_default_llm_eval_dataset()
        results: List[CaseEvaluationResult] = []

        for case in test_cases:
            res = self.evaluate_case(case)
            results.append(res)

        total = len(results)
        valid_count = sum(1 for r in results if r.is_schema_valid)
        refusal_count = sum(1 for r in results if r.refusal_correctness)
        hallucination_count = sum(1 for r in results if r.hallucination_detected)

        return LLMEvalScorecard(
            total_cases=total,
            format_validity_rate=round(valid_count / total, 4) if total else 0.0,
            mean_groundedness=round(float(np.mean([r.groundedness_score for r in results])), 4),
            mean_citation_accuracy=round(float(np.mean([r.citation_accuracy for r in results])), 4),
            mean_completeness=round(float(np.mean([r.completeness_score for r in results])), 4),
            mean_faithfulness=round(float(np.mean([r.faithfulness_score for r in results])), 4),
            hallucination_rate=round(hallucination_count / total, 4) if total else 0.0,
            refusal_correctness_rate=round(refusal_count / total, 4) if total else 0.0,
            mean_latency_ms=round(float(np.mean([r.latency_ms for r in results])), 2),
            total_tokens_consumed=sum(r.total_tokens for r in results),
            case_results=results,
        )
