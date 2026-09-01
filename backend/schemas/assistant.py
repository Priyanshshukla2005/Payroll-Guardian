"""Schemas for payroll administrator conversational assistant endpoints (Phase 7)."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.schemas.anomaly import ComplianceSourceItem


class AssistantQueryRequest(BaseModel):
    """Payload for asking grounded questions to the Payroll AI Assistant."""

    question: str = Field(min_length=2, description="Inquiry question from payroll administrator")
    analysis_id: Optional[str] = Field(default=None, description="Optional analysis ID to provide grounded context")
    employee_id: Optional[str] = Field(default=None, description="Optional employee ID within the analysis")


class AssistantQueryResponseSchema(BaseModel):
    """Grounded answer from the Payroll AI Assistant."""

    question: str
    answer: str
    grounded_facts: List[str] = Field(default_factory=list)
    evidence_sources: List[str] = Field(default_factory=list)
    citations: List[ComplianceSourceItem] = Field(default_factory=list)
    category_distinction: Dict[str, List[str]] = Field(default_factory=dict)
    suggested_next_steps: List[str] = Field(default_factory=list)
    uncertainty_or_refusal: Optional[str] = None
    disclaimer: str = "AI-assisted payroll analysis. Must be verified with official statutory regulations and internal policies."
