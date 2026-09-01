"""Unit tests for Citation Integrity and Zero Fabrication Guarantee (Phase 6)."""

import pytest
from ai.llm.context_builder import (
    DetectionContext,
    EmployeeContext,
    EvidenceContext,
    RetrievedKnowledgeItem,
    StructuredLLMInput,
)
from ai.llm.response_schema import ExplanationSeverity
from ai.llm.validator import PayrollLLMValidator


@pytest.fixture
def structured_input_with_epfo():
    return StructuredLLMInput(
        employee_context=EmployeeContext(
            employee_id="EMP_500",
            department="Operations",
            designation="Specialist",
            payroll_period="2024-06",
            location="INDIA",
        ),
        detection=DetectionContext(
            risk_score=0.85,
            confidence="VERY_HIGH",
            anomaly_types=["INCORRECT_PF"],
        ),
        evidence=EvidenceContext(
            top_signals=["PF deduction mismatch"],
            historical_comparison={},
            peer_comparison={},
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


def test_valid_citation_accepted(structured_input_with_epfo):
    payload = {
        "title": "Valid Citation Test",
        "severity": "CRITICAL",
        "summary": "Valid explanation.",
        "why_flagged": ["Reason"],
        "evidence": ["Evidence"],
        "compliance_context": ["EPFO Act 1952 applies."],
        "recommended_actions": ["Verify"],
        "citations": [
            {
                "document_id": "EPFO_ACT_1952",
                "page": 1,
                "section": "Section 6",
                "citation": "EPFO Act, 1952, Section 6",
            }
        ],
        "disclaimer": "Disclaimer",
    }

    result = PayrollLLMValidator.validate_anomaly_explanation(payload, structured_input_with_epfo)
    assert result.is_valid is True
    assert len(result.sanitized_response.citations) == 1
    assert result.sanitized_response.citations[0].document_id == "EPFO_ACT_1952"
    assert result.citation_validity_rate == 1.0


def test_fabricated_citation_rejected_and_removed(structured_input_with_epfo):
    # LLM hallucinates an unretrieved document ID 'FABRICATED_LABOUR_LAW_2099'
    payload = {
        "title": "Fabricated Citation Test",
        "severity": "CRITICAL",
        "summary": "Explanation citing hallucinated statute.",
        "why_flagged": ["Reason"],
        "evidence": ["Evidence"],
        "compliance_context": ["Hallucinated regulation."],
        "recommended_actions": ["Verify"],
        "citations": [
            {
                "document_id": "FABRICATED_LABOUR_LAW_2099",
                "page": 99,
                "section": "Section 999",
                "citation": "Fabricated Act 2099 Section 999",
            },
            {
                "document_id": "EPFO_ACT_1952",
                "page": 1,
                "section": "Section 6",
                "citation": "EPFO Act, 1952, Section 6",
            },
        ],
        "disclaimer": "Disclaimer",
    }

    result = PayrollLLMValidator.validate_anomaly_explanation(payload, structured_input_with_epfo)
    assert result.is_valid is True
    # The fabricated citation must be purged
    assert len(result.sanitized_response.citations) == 1
    assert result.sanitized_response.citations[0].document_id == "EPFO_ACT_1952"
    assert result.citation_validity_rate == 0.5
    assert any("FABRICATED_CITATION_REMOVED" in w for w in result.warnings)
