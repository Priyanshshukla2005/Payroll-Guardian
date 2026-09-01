"""Unit tests for GroundednessChecker and claim verification (Phase 6)."""

import pytest
from ai.llm.context_builder import (
    DetectionContext,
    EmployeeContext,
    EvidenceContext,
    RetrievedKnowledgeItem,
    StructuredLLMInput,
)
from ai.llm.response_schema import ExplanationSeverity
from ai.llm.validator import GroundednessChecker


@pytest.fixture
def sample_structured_input():
    return StructuredLLMInput(
        employee_context=EmployeeContext(
            employee_id="EMP_303",
            department="Logistics",
            designation="Driver",
            payroll_period="2024-06",
            location="DELHI",
        ),
        detection=DetectionContext(
            risk_score=0.88,
            confidence="VERY_HIGH",
            anomaly_types=["EXCESSIVE_OVERTIME"],
        ),
        evidence=EvidenceContext(
            top_signals=["Logged 75.0 hours overtime (exceeds 60.0 hours monthly cap)"],
            historical_comparison={"observed_basic": 25000.0},
            peer_comparison={"department": "Logistics"},
            rule_violations=["RULE_OVERTIME_EXCEEDS_CAP"],
        ),
        retrieved_knowledge=[
            RetrievedKnowledgeItem(
                document_id="COMPANY_OVERTIME_BONUS_POLICY_2024",
                title="Company Overtime & Bonus Policy 2024",
                authority_level="COMPANY_POLICY",
                jurisdiction="INDIA",
                effective_from="2024-01-01",
                page=1,
                section="Section 1",
                text="Overtime capped at 60 hours per month for non-exempt staff.",
                citation="Company Policy 2024, Section 1",
            )
        ],
        determined_severity=ExplanationSeverity.CRITICAL,
        rag_status="SUCCESS",
    )


def test_groundedness_checker_high_score_for_aligned_claims(sample_structured_input):
    grounded_response = {
        "why_flagged": ["Employee logged 75.0 hours overtime, exceeding the 60.0 hours monthly cap."],
        "evidence": ["Logged 75.0 hours overtime vs 60.0 hours limit."],
        "compliance_context": ["Company Overtime & Bonus Policy 2024 Section 1 establishes a 60 hour maximum."],
    }

    score, unsupported = GroundednessChecker.check_groundedness(grounded_response, sample_structured_input)
    assert score >= 0.85
    assert len(unsupported) == 0


def test_groundedness_checker_flags_unsupported_external_claims(sample_structured_input):
    unsupported_response = {
        "why_flagged": ["Employee violated Brazilian Maritime Union Decree 99812 with 450 bonus units."],
        "evidence": ["Unrelated offshore vessel allowance of $89,000 USD was detected."],
        "compliance_context": ["International Maritime Labour Convention Article 77."],
    }

    score, unsupported = GroundednessChecker.check_groundedness(unsupported_response, sample_structured_input)
    assert score < 0.50
    assert len(unsupported) > 0
    assert any("UNSUPPORTED_CLAIM" in u for u in unsupported)
