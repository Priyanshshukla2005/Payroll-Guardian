"""Schemas for structured anomaly results, compliance evidence, and explanations (Phase 7)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ComplianceSourceItem(BaseModel):
    """Authoritative source chunk referenced in the compliance result."""

    document_id: str
    title: Optional[str] = None
    authority_level: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    citation: str


class ComplianceStatusBlock(BaseModel):
    """Compliance retrieval status and associated citations."""

    status: str = Field(description="Retrieval status: FOUND, NO_RELIABLE_SOURCE_FOUND, JURISDICTION_UNKNOWN")
    sources: List[ComplianceSourceItem] = Field(default_factory=list)
    no_answer_reason: Optional[str] = None


class ExplanationItem(BaseModel):
    """Grounded explanation generated for the anomaly."""

    title: Optional[str] = None
    summary: str
    why_flagged: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    uncertainty: Optional[str] = None
    fallback_mode: bool = False


class AnomalyRecordResult(BaseModel):
    """Complete structured audit result for a flagged employee record."""

    employee_id: str
    payroll_month: str
    department: str
    designation: str
    anomaly_types: List[str]
    risk_score: float
    severity: str
    evidence: List[str] = Field(default_factory=list)
    rule_violations: List[str] = Field(default_factory=list)
    historical_comparison: Dict[str, Any] = Field(default_factory=dict)
    peer_comparison: Dict[str, Any] = Field(default_factory=dict)
    compliance: ComplianceStatusBlock
    explanation: ExplanationItem


class AnalysisSummary(BaseModel):
    """Aggregate statistics for an analyzed payroll batch."""

    records_analyzed: int
    records_flagged: int
    critical_risk: int = 0
    high_risk: int = 0
    medium_risk: int = 0
    low_risk: int = 0
