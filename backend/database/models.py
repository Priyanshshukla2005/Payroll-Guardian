"""SQLAlchemy ORM database models for AI Payroll Guardian (Phase 10)."""

from datetime import datetime
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database.session import Base


class User(Base):
    """User account entity for authentication and role-based access control."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), default="VIEWER", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    full_name = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PayrollBatch(Base):
    """Uploaded payroll dataset batch metadata."""

    __tablename__ = "payroll_batches"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(String(64), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_format = Column(String(16), nullable=False)  # csv, json, parquet
    row_count = Column(Integer, default=0, nullable=False)
    uploaded_by = Column(String(64), nullable=True)
    status = Column(String(32), default="READY", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PayrollRecord(Base):
    """Individual normalized employee payroll row in a batch."""

    __tablename__ = "payroll_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(String(64), index=True, nullable=False)
    employee_id = Column(String(64), index=True, nullable=False)
    payroll_month = Column(String(16), index=True, nullable=False)
    department = Column(String(64), nullable=False, default="General")
    designation = Column(String(64), nullable=False, default="Staff")
    location = Column(String(64), nullable=False, default="INDIA")
    basic_salary = Column(Float, nullable=False, default=0.0)
    gross_salary = Column(Float, nullable=False, default=0.0)
    net_salary = Column(Float, nullable=False, default=0.0)
    allowances = Column(Float, default=0.0)
    bonus = Column(Float, default=0.0)
    total_deductions = Column(Float, default=0.0)
    pf_deduction = Column(Float, default=0.0)
    esi = Column(Float, default=0.0)
    professional_tax = Column(Float, default=0.0)
    working_days = Column(Integer, default=26)
    present_days = Column(Integer, default=26)
    leave_days = Column(Integer, default=0)
    overtime_hours = Column(Float, default=0.0)
    raw_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Analysis(Base):
    """Persistent payroll audit analysis report."""

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_id = Column(String(64), unique=True, index=True, nullable=False)
    batch_id = Column(String(64), index=True, nullable=True)
    request_id = Column(String(64), index=True, nullable=False)
    status = Column(String(32), default="COMPLETED", nullable=False)
    payroll_period = Column(String(16), nullable=False)
    model_name = Column(String(64), default="HybridPayrollDetector_v2", nullable=False)
    model_version = Column(String(32), default="v2", nullable=False)
    model_threshold = Column(Float, default=0.45, nullable=False)
    feature_schema_version = Column(String(32), default="features_v1", nullable=False)
    rag_knowledge_version = Column(String(32), default="rag_2024_06", nullable=False)
    llm_version = Column(String(32), default="grounded_llm_v2", nullable=False)
    disclaimer = Column(String(255), default="AI-assisted payroll analysis. Not legal advice.")
    duration_ms = Column(Float, default=0.0)
    summary_json = Column(Text, nullable=False)  # JSON-serialized AnalysisSummary
    timings_json = Column(Text, nullable=False)  # JSON-serialized PipelineTimings
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    anomalies = relationship("AnomalyRecord", back_populates="analysis", cascade="all, delete-orphan")


class AnomalyRecord(Base):
    """Individual flagged anomaly record with evidence, compliance, and explanation."""

    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_id = Column(String(64), ForeignKey("analyses.analysis_id"), index=True, nullable=False)
    employee_id = Column(String(64), index=True, nullable=False)
    payroll_month = Column(String(16), nullable=False)
    department = Column(String(64), nullable=False)
    designation = Column(String(64), nullable=False)
    risk_score = Column(Float, nullable=False)
    severity = Column(String(16), nullable=False)
    anomaly_types_json = Column(Text, nullable=False)
    rule_violations_json = Column(Text, nullable=False)
    evidence_json = Column(Text, nullable=False)
    historical_comparison_json = Column(Text, nullable=True)
    peer_comparison_json = Column(Text, nullable=True)
    compliance_json = Column(Text, nullable=False)
    explanation_json = Column(Text, nullable=False)
    status = Column(String(32), default="FLAGGED", nullable=False)  # FLAGGED, UNDER_REVIEW, RESOLVED, FALSE_POSITIVE
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(64), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    analysis = relationship("Analysis", back_populates="anomalies")


class AuditEvent(Base):
    """Append-only audit trail event for enterprise compliance tracking."""

    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    analysis_id = Column(String(64), index=True, nullable=True)
    actor_id = Column(String(64), default="system", nullable=False)
    event_type = Column(String(64), index=True, nullable=False)
    metadata_json = Column(Text, nullable=False, default="{}")
    request_id = Column(String(64), index=True, nullable=True)


class ComplianceSource(Base):
    """Authoritative legal and compliance statutory document registry."""

    __tablename__ = "compliance_sources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    source_name = Column(String(255), nullable=True)
    source_type = Column(String(64), nullable=False)
    authority_level = Column(String(32), nullable=False)  # AUTHORITATIVE, COMPANY_POLICY, REFERENCE
    jurisdiction = Column(String(64), nullable=False)
    topic = Column(String(64), nullable=True)
    effective_from = Column(String(32), nullable=True)
    effective_until = Column(String(32), nullable=True)
    document_version = Column(String(32), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256 hash
    content_hash = Column(String(64), nullable=False)
    source_url = Column(String(512), nullable=True)
    status = Column(String(32), default="ACTIVE", nullable=False)
