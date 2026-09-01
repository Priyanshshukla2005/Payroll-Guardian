"""Standardized response schemas for grounded LLM explanations and assistant responses (Phase 6).

Enforces strict structural validation on LLM outputs using Pydantic.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExplanationSeverity(str, Enum):
    """Standardized human-readable severity level derived from detector/rules."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CitationReference(BaseModel):
    """Specific citation linking an explanation claim to a retrieved authoritative document."""

    document_id: str = Field(description="Unique document ID matching retrieved source")
    page: Optional[int] = Field(default=None, description="Page number if available")
    section: Optional[str] = Field(default=None, description="Section heading or clause ID")
    citation: str = Field(description="Standardized legal or policy citation string")


class GroundedAnomalyItem(BaseModel):
    """Independent explanation item for multi-anomaly records."""

    anomaly_type: str = Field(description="Specific anomaly category name")
    severity: ExplanationSeverity = Field(default=ExplanationSeverity.MEDIUM, description="Mapped severity")
    description: str = Field(description="Concise description of the specific anomaly")
    evidence_points: List[str] = Field(default_factory=list, description="Specific metrics and signals supporting this flag")
    applicable_rule_or_policy: Optional[str] = Field(default=None, description="Applicable statutory section or company policy clause")


class PayrollExplanationResponse(BaseModel):
    """Grounded anomaly explanation generated for payroll administrators."""

    title: str = Field(description="Clear, descriptive title of the anomaly assessment")
    severity: ExplanationSeverity = Field(description="Deterministic severity rating")
    summary: str = Field(description="Executive summary of the flagged situation")
    why_flagged: List[str] = Field(default_factory=list, description="Logical reasons why the record triggered detection")
    evidence: List[str] = Field(default_factory=list, description="Structured numerical and historical evidence points")
    compliance_context: List[str] = Field(default_factory=list, description="Relevant statutory regulations and company policies")
    recommended_actions: List[str] = Field(default_factory=list, description="Cautious, non-autonomous verification steps for administrator")
    citations: List[CitationReference] = Field(default_factory=list, description="Verified citations from retrieved knowledge context")
    anomaly_breakdowns: List[GroundedAnomalyItem] = Field(default_factory=list, description="Independent breakdowns for compound multi-anomalies")
    uncertainty: Optional[str] = Field(default=None, description="Statement of missing information, date ambiguities, or confidence limitations")
    disclaimer: str = Field(
        default="AI-assisted payroll analysis. Not legal advice. Must be verified with official statutory regulations and internal policies.",
        description="Mandatory compliance disclaimer",
    )
    generation_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Metrics including token usage, latency (ms), provider, and model"
    )


class AssistantQueryResponse(BaseModel):
    """Grounded response schema for payroll administrator Q&A queries."""

    question: str = Field(description="Original user query asked by the payroll administrator")
    answer: str = Field(description="Grounded, direct answer based strictly on evidence and retrieved knowledge")
    grounded_facts: List[str] = Field(default_factory=list, description="Factual statements derived from evidence")
    evidence_sources: List[str] = Field(default_factory=list, description="Titles of documents and evidence sources referenced")
    citations: List[CitationReference] = Field(default_factory=list, description="Verified citations matching retrieved sources")
    category_distinction: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "statutory_requirements": [],
            "company_policies": [],
            "analytical_observations": [],
        },
        description="Explicit breakdown distinguishing statutory law from company SOPs and ML observations",
    )
    suggested_next_steps: List[str] = Field(default_factory=list, description="Verification actions the administrator can take")
    uncertainty_or_refusal: Optional[str] = Field(default=None, description="Explicit statement of refusal or missing context")
    disclaimer: str = Field(
        default="AI-assisted payroll analysis. Must be verified with official statutory regulations and internal policies.",
        description="Mandatory compliance disclaimer",
    )
    generation_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Metrics including token usage, latency (ms), provider, and model"
    )
