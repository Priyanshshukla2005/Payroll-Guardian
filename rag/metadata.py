"""Metadata schemas and taxonomy models for AI Payroll Guardian RAG system (Phase 5).

Defines authoritative tiering, source types, topics, jurisdictions,
document metadata, chunk metadata, and structured retrieval outputs.
"""

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuthorityLevel(str, Enum):
    """Hierarchical authority tier for compliance claims."""

    AUTHORITATIVE = "AUTHORITATIVE"  # Tier 1: Official government regulations, statutory acts, circulars
    COMPANY_POLICY = "COMPANY_POLICY"  # Tier 2: Internal organizational policies (leave, overtime, bonus)
    REFERENCE = "REFERENCE"  # Tier 3: Explanatory documentation, software guides, general HR literature
    UNVERIFIED = "UNVERIFIED"  # Unverified sources (never used for compliance claims)


class SourceType(str, Enum):
    """Classification of the original knowledge source."""

    GOVERNMENT_ACT = "GOVERNMENT_ACT"
    STATUTORY_NOTIFICATION = "STATUTORY_NOTIFICATION"
    OFFICIAL_CIRCULAR = "OFFICIAL_CIRCULAR"
    COMPANY_POLICY = "COMPANY_POLICY"
    REFERENCE_GUIDE = "REFERENCE_GUIDE"


class Topic(str, Enum):
    """Controlled vocabulary for payroll and compliance subject areas."""

    PF = "PF"
    ESI = "ESI"
    TDS = "TDS"
    PROFESSIONAL_TAX = "PROFESSIONAL_TAX"
    OVERTIME = "OVERTIME"
    WAGES = "WAGES"
    LEAVE = "LEAVE"
    BONUS = "BONUS"
    DEDUCTIONS = "DEDUCTIONS"
    PAYROLL_PROCESSING = "PAYROLL_PROCESSING"
    LABOUR_COMPLIANCE = "LABOUR_COMPLIANCE"
    EMPLOYEE_CLASSIFICATION = "EMPLOYEE_CLASSIFICATION"


class Jurisdiction(str, Enum):
    """Geographic and legal jurisdiction."""

    INDIA = "INDIA"
    MAHARASHTRA = "MAHARASHTRA"
    KARNATAKA = "KARNATAKA"
    DELHI = "DELHI"
    UTTAR_PRADESH = "UTTAR_PRADESH"
    TAMIL_NADU = "TAMIL_NADU"
    TELANGANA = "TELANGANA"
    ALL = "ALL"
    UNKNOWN = "UNKNOWN"


class DocumentMetadata(BaseModel):
    """Complete traceability metadata for an ingested compliance document."""

    document_id: str
    title: str
    source_name: str
    source_type: SourceType
    authority_level: AuthorityLevel
    jurisdiction: Jurisdiction
    topic: Topic
    publication_date: Optional[str] = None  # YYYY-MM-DD
    effective_from: str  # YYYY-MM-DD
    effective_until: Optional[str] = None  # YYYY-MM-DD or None for current/active
    document_version: str = "v1.0"
    language: str = "en"
    source_url: Optional[str] = None
    retrieval_date: Optional[str] = None
    file_hash: str
    content_hash: str
    status: str = "ACTIVE"  # ACTIVE, SUPERSEDED, ARCHIVED
    description: Optional[str] = None


class ChunkMetadata(BaseModel):
    """Metadata bound to an individual semantic chunk."""

    chunk_id: str
    document_id: str
    chunk_index: int
    title: str
    source_name: str
    authority_level: AuthorityLevel
    jurisdiction: Jurisdiction
    topic: Topic
    effective_from: str
    effective_until: Optional[str] = None
    document_version: str
    section: Optional[str] = None
    heading: Optional[str] = None
    page_number: Optional[int] = None
    char_count: int
    token_count: int


class RetrievedChunk(BaseModel):
    """Structured evidence chunk returned by the RAG retriever."""

    chunk_id: str
    document_id: str
    title: str
    source_name: str
    authority_level: AuthorityLevel
    jurisdiction: Jurisdiction
    effective_from: str
    effective_until: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    similarity_score: float
    rerank_score: float
    text: str
    citation: str
    applicability_status: str = "VERIFIED"  # VERIFIED, HISTORICAL, UNKNOWN


class StructuredRAGResponse(BaseModel):
    """Standardized output schema for knowledge retrieval requests."""

    query: str
    jurisdiction: Jurisdiction
    payroll_date: str
    topic: Optional[Topic] = None
    results: List[RetrievedChunk] = Field(default_factory=list)
    total_found: int = 0
    status: str = "SUCCESS"  # SUCCESS, NO_RELIABLE_SOURCE_FOUND, JURISDICTION_UNKNOWN
    no_answer_reason: Optional[str] = None
