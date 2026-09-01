"""Schemas for analysis batches, asynchronous jobs, and response envelopes (Phase 10)."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.schemas.anomaly import AnalysisSummary, AnomalyRecordResult


class AnalysisStatus(str, Enum):
    """Lifecycle status of a payroll analysis job."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PipelineTimings(BaseModel):
    """Execution latency breakdown across pipeline stages in milliseconds."""

    feature_generation_ms: float = 0.0
    detection_ms: float = 0.0
    rag_ms: float = 0.0
    llm_ms: float = 0.0
    total_ms: float = 0.0


class AnalysisResponse(BaseModel):
    """Unified API response for completed payroll analysis."""

    request_id: str
    analysis_id: str
    status: AnalysisStatus = AnalysisStatus.COMPLETED
    payroll_period: str
    summary: AnalysisSummary
    anomalies: List[AnomalyRecordResult] = Field(default_factory=list)
    model_name: str = "HybridPayrollDetector_v2"
    model_version: str = "v2"
    model_threshold: float = 0.45
    feature_schema_version: str = "features_v1"
    rag_knowledge_version: str = "rag_2024_06"
    llm_version: str = "grounded_llm_v2"
    disclaimer: str = "AI-assisted payroll analysis. Not legal advice."
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    duration_ms: float = 0.0
    timings: PipelineTimings = Field(default_factory=PipelineTimings)


class AnalysisJobResponse(BaseModel):
    """Initial lightweight response for queued or ongoing analysis jobs."""

    analysis_id: str
    status: AnalysisStatus
    message: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
