"""Schemas for compliance knowledge search endpoints (Phase 7)."""

from typing import List, Optional
from pydantic import BaseModel, Field

from backend.schemas.anomaly import ComplianceSourceItem


class ComplianceSearchRequest(BaseModel):
    """Payload for statutory and organizational knowledge search."""

    query: str = Field(min_length=2, description="Search query string")
    jurisdiction: Optional[str] = Field(default="INDIA", description="Geographic jurisdiction (e.g. MAHARASHTRA, KARNATAKA, INDIA)")
    payroll_date: Optional[str] = Field(default="2024-06-01", description="Date for applicability filter (YYYY-MM-DD)")
    topic: Optional[str] = Field(default=None, description="Topic filter (e.g. PF, ESI, TDS, OVERTIME, LEAVE)")
    top_n: int = Field(default=3, ge=1, le=10, description="Maximum number of authoritative citations to return")


class ComplianceSearchResult(BaseModel):
    """Result schema for compliance knowledge search."""

    query: str
    jurisdiction: str
    payroll_date: str
    topic: Optional[str] = None
    results: List[ComplianceSourceItem] = Field(default_factory=list)
    total_found: int = 0
    status: str = "SUCCESS"
    no_answer_reason: Optional[str] = None
