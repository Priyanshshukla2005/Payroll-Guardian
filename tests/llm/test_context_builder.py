"""Unit tests for ContextBuilder and StructuredLLMInput (Phase 6)."""

import pytest
from ai.explainability.explainer_v2 import DetailedEvidenceCard
from ai.llm.context_builder import ContextBuilder, StructuredLLMInput
from ai.llm.response_schema import ExplanationSeverity
from rag.metadata import AuthorityLevel, Jurisdiction, RetrievedChunk, StructuredRAGResponse


def test_context_builder_from_evidence_card():
    builder = ContextBuilder()
    card = DetailedEvidenceCard(
        employee_id="EMP001",
        payroll_month="2024-06",
        risk_score=0.92,
        confidence="VERY_HIGH",
        top_signals=["PF deduction mismatch observed"],
        historical_comparison={"observed_basic": 40000.0},
        peer_comparison={"department": "Engineering", "designation": "Developer", "location": "KARNATAKA"},
        rule_violations=["RULE_PF_MISMATCH"],
        anomaly_types=["INCORRECT_PF"],
        human_readable_summary="Flagged for PF mismatch",
    )

    rag_resp = StructuredRAGResponse(
        query="EPFO statutory 12 percent",
        jurisdiction=Jurisdiction.KARNATAKA,
        payroll_date="2024-06-01",
        status="SUCCESS",
        results=[
            RetrievedChunk(
                chunk_id="EPFO_CHUNK_01",
                document_id="EPFO_ACT_1952",
                title="Employees Provident Funds Act 1952",
                source_name="EPFO",
                authority_level=AuthorityLevel.AUTHORITATIVE,
                jurisdiction=Jurisdiction.INDIA,
                effective_from="1952-11-01",
                page=1,
                section="Section 6",
                similarity_score=0.91,
                rerank_score=0.88,
                text="Mandatory 12% contribution on basic wage.",
                citation="EPFO Act, 1952, Section 6",
            )
        ],
    )

    inp = builder.build_structured_input(card, rag_resp)

    assert isinstance(inp, StructuredLLMInput)
    assert inp.employee_context.employee_id == "EMP001"
    assert inp.employee_context.department == "Engineering"
    assert inp.detection.risk_score == 0.92
    assert inp.detection.anomaly_types == ["INCORRECT_PF"]
    assert inp.determined_severity == ExplanationSeverity.CRITICAL
    assert len(inp.retrieved_knowledge) == 1
    assert inp.retrieved_knowledge[0].document_id == "EPFO_ACT_1952"

    prompt_ctx = builder.format_prompt_context(inp)
    assert "EMP001" in prompt_ctx
    assert "CRITICAL" in prompt_ctx
    assert "EPFO_ACT_1952" in prompt_ctx
    assert "STATUTORY REQUIREMENT (Tier 1)" in prompt_ctx


def test_context_builder_severity_mapping():
    builder = ContextBuilder()

    # Critical
    assert builder.map_severity(0.90, [], []) == ExplanationSeverity.CRITICAL
    assert builder.map_severity(0.50, ["RULE_A", "RULE_B"], []) == ExplanationSeverity.CRITICAL
    assert builder.map_severity(0.30, [], ["IMPOSSIBLE_ATTENDANCE"]) == ExplanationSeverity.CRITICAL

    # High
    assert builder.map_severity(0.70, [], []) == ExplanationSeverity.HIGH
    assert builder.map_severity(0.30, ["RULE_X"], []) == ExplanationSeverity.HIGH
    assert builder.map_severity(0.30, [], ["INCORRECT_PF"]) == ExplanationSeverity.HIGH

    # Medium
    assert builder.map_severity(0.50, [], []) == ExplanationSeverity.MEDIUM

    # Low
    assert builder.map_severity(0.20, [], []) == ExplanationSeverity.LOW
