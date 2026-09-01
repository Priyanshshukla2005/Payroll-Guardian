"""Unit tests for Pydantic Response Schemas (Phase 6)."""

import pytest
from pydantic import ValidationError
from ai.llm.response_schema import (
    AssistantQueryResponse,
    CitationReference,
    ExplanationSeverity,
    GroundedAnomalyItem,
    PayrollExplanationResponse,
)


def test_payroll_explanation_response_valid():
    cite = CitationReference(
        document_id="EPFO_ACT_1952",
        page=1,
        section="Section 6",
        citation="EPFO Act, 1952, Section 6",
    )
    breakdown = GroundedAnomalyItem(
        anomaly_type="INCORRECT_PF",
        severity=ExplanationSeverity.HIGH,
        description="PF deduction calculated at 6% instead of 12%",
        evidence_points=["Calculated: ₹2,100, Expected: ₹4,200"],
        applicable_rule_or_policy="EPFO Act 1952 Section 6",
    )

    resp = PayrollExplanationResponse(
        title="PF Mismatch Detected",
        severity=ExplanationSeverity.HIGH,
        summary="Employee basic wage PF deduction was under-calculated.",
        why_flagged=["Triggered RULE_PF_MISMATCH"],
        evidence=["Observed PF ₹2,100 vs expected ₹4,200"],
        compliance_context=["EPFO Section 6 mandates 12% contribution."],
        recommended_actions=["Verify payroll deduction formula for PF"],
        citations=[cite],
        anomaly_breakdowns=[breakdown],
        uncertainty=None,
    )

    assert resp.severity == ExplanationSeverity.HIGH
    assert len(resp.citations) == 1
    assert resp.citations[0].document_id == "EPFO_ACT_1952"
    assert len(resp.anomaly_breakdowns) == 1
    assert "Not legal advice" in resp.disclaimer


def test_payroll_explanation_response_validation_failure():
    # Missing required field 'summary'
    with pytest.raises(ValidationError):
        PayrollExplanationResponse(
            title="PF Mismatch",
            severity=ExplanationSeverity.HIGH,
            why_flagged=["Reason"],
            evidence=["Evidence"],
            recommended_actions=["Action"],
        )


def test_assistant_query_response_valid():
    resp = AssistantQueryResponse(
        question="Why was this employee flagged?",
        answer="Flagged for overtime exceeding 60h cap.",
        grounded_facts=["Overtime logged: 72 hours"],
        evidence_sources=["Company Overtime Policy 2024"],
        citations=[],
        category_distinction={
            "statutory_requirements": [],
            "company_policies": ["Company Overtime Policy 2024: 60h monthly cap"],
            "analytical_observations": ["72 hours logged"],
        },
        suggested_next_steps=["Verify manager overtime approval"],
    )

    assert resp.question == "Why was this employee flagged?"
    assert len(resp.category_distinction["company_policies"]) == 1
    assert "Must be verified" in resp.disclaimer
