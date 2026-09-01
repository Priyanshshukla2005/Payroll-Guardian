"""Common response models and health check schemas (Phase 10)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Standardized error body format."""

    code: str
    message: str
    request_id: str
    status_code: int
    details: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    """Wrapper for all API error responses."""

    error: ErrorDetail


class ServiceStatus(BaseModel):
    """Component readiness status."""

    ai: str = "available"
    rag: str = "available"
    llm: str = "available"
    database: str = "available"


class HealthResponse(BaseModel):
    """Response schema for GET /api/v1/health."""

    status: str = "healthy"
    version: str = "1.0.0"
    environment: str = "development"
    services: ServiceStatus = Field(default_factory=ServiceStatus)


class LivenessResponse(BaseModel):
    """Response schema for GET /api/v1/health/liveness."""

    status: str = "live"


class ReadinessResponse(BaseModel):
    """Response schema for GET /api/v1/health/readiness."""

    status: str = "ready"
    model_version: str = "v2"
    rag_indexed_chunks: int
    llm_provider: str
    database: str = "connected"
