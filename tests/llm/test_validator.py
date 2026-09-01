"""Unit tests for PayrollLLMValidator (Phase 6)."""

import json
import pytest
from ai.llm.context_builder import (
    ContextBuilder,
    DetectionContext,
    EmployeeContext,
    EvidenceContext,
    RetrievedKnowledgeItem,
    StructuredLLMInput,
)
from ai.llm.response_schema import ExplanationSeverity, PayrollExplanationResponse
from ai.llm.validator import PayrollLLMValidator


@pytest.fixture
def mock_structured_input():
    return StructuredLLMInput(
        employee_context=EmployeeContext(
            employee_id="EMP_101",
            department="Engineering",
            designation="Developer",
            payroll_period="2024-06",
            location="INDIA",
        ),
        detection=DetectionContext(
            risk_score=0.90,
            confidence="VERY_HIGH",
            anomaly_types=["INCORRECT_PF"],
        ),
        evidence=EvidenceContext(
            top_signals=["PF deduction mismatch: observed ₹2,000 vs expected ₹4,000"],
            historical_comparison={"observed_basic": 33333.33},
            peer_comparison={"department": "Engineering"},
            rule_violations=["RULE_PF_MISMATCH"],
        ),
        retrieved_knowledge=[
            RetrievedKnowledgeItem(
                document_id="EPFO_ACT_1952",
                title="EPFO Act 1952",
                authority_level="AUTHORITATIVE",
                jurisdiction="INDIA",
                effective_from="1952-11-01",
                page=1,
                section="Section 6",
                text="12% statutory rate applies.",
                citation="EPFO Act, 1952, Section 6",
            )
        ],
        determined_severity=ExplanationSeverity.CRITICAL,
        rag_status="SUCCESS",
    )


def test_validator_valid_json_string(mock_structured_input):
    valid_payload = {
        "title": "PF Mismatch Detected",
        "severity": "CRITICAL",
        "summary": "Employee basic salary PF deduction was calculated incorrectly.",
        "why_flagged": ["PF deduction was ₹2,000 instead of 12% statutory rate."],
        "evidence": ["Observed PF ₹2,000 vs expected ₹4,000"],
        "compliance_context": ["EPFO Act 1952 Section 6 requires 12% contribution."],
        "recommended_actions": ["Verify PF deduction formula"],
        "citations": [
            {
                "document_id": "EPFO_ACT_1952",
                "page": 1,
                "section": "Section 6",
                "citation": "EPFO Act, 1952, Section 6",
            }
        ],
        "anomaly_breakdowns": [],
        "uncertainty": None,
        "disclaimer": "AI-assisted payroll analysis. Not legal advice.",
    }

    raw_json = json.dumps(valid_payload)
    result = PayrollLLMValidator.validate_anomaly_explanation(raw_json, mock_structured_input)

    assert result.is_valid is True
    assert isinstance(result.sanitized_response, PayrollExplanationResponse)
    assert result.sanitized_response.severity == ExplanationSeverity.CRITICAL
    assert len(result.sanitized_response.citations) == 1


def test_validator_malformed_json(mock_structured_input):
    malformed_json = '{"title": "Unclosed JSON string...'
    result = PayrollLLMValidator.validate_anomaly_explanation(malformed_json, mock_structured_input)

    assert result.is_valid is False
    assert any("MALFORMED_JSON" in e for e in result.errors)


def test_validator_severity_override(mock_structured_input):
    # LLM tries to change assigned CRITICAL to LOW
    payload = {
        "title": "PF Mismatch",
        "severity": "LOW",
        "summary": "Discrepancy observed.",
        "why_flagged": ["Reason"],
        "evidence": ["Signal"],
        "compliance_context": ["Context"],
        "recommended_actions": ["Action"],
        "citations": [],
        "anomaly_breakdowns": [],
        "uncertainty": None,
        "disclaimer": "AI-assisted payroll analysis.",
    }

    result = PayrollLLMValidator.validate_anomaly_explanation(payload, mock_structured_input)
    assert result.is_valid is True
    # Validator should force severity back to assigned CRITICAL
    assert result.sanitized_response.severity == ExplanationSeverity.CRITICAL
    assert any("SEVERITY_OVERRIDE" in w for w in result.warnings)
