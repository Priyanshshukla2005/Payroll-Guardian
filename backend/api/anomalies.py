"""Anomaly investigation, drilldown, and resolution endpoints (Phase 10)."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.auth.rbac import AuthenticatedUser, UserRole, require_roles
from backend.database.models import AnomalyRecord as DBAnomalyRecord
from backend.database.repository import DatabaseAuditRepository
from backend.database.session import SessionLocal
from backend.dependencies.services import (
    AnalysisRepository,
    ModelManager,
    get_analysis_repository,
    get_model_manager,
)
from backend.schemas.anomaly import AnomalyRecordResult

router = APIRouter(prefix="/anomalies", tags=["Anomaly Investigation"])


class AnomalyResolutionRequest(BaseModel):
    """Payload for resolving or updating the status of an anomaly record."""

    status: str = Field(default="RESOLVED", description="Status: RESOLVED, FALSE_POSITIVE, UNDER_REVIEW")
    resolution_notes: str = Field(min_length=3, description="Audit justification for resolution")


class AnomalyResolutionResponse(BaseModel):
    """Response envelope for anomaly resolution."""

    analysis_id: str
    employee_id: str
    status: str
    resolution_notes: str
    resolved_by: str
    resolved_at: str


@router.get("/{analysis_id}", response_model=List[AnomalyRecordResult], status_code=status.HTTP_200_OK)
def list_anomalies_for_analysis(
    analysis_id: str,
    severity: Optional[str] = Query(None, description="Optional severity filter (CRITICAL, HIGH, MEDIUM, LOW)"),
    anomaly_type: Optional[str] = Query(None, description="Optional anomaly type filter (e.g., INCORRECT_PF)"),
    repo: AnalysisRepository = Depends(get_analysis_repository),
    model_mgr: ModelManager = Depends(get_model_manager),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN, UserRole.AUDITOR, UserRole.VIEWER)
    ),
):
    """List flagged anomaly records for an analysis batch with optional filters."""
    analysis = repo.get_analysis(analysis_id)
    if not analysis and analysis_id == "anl_demo_202406":
        from backend.services.demo_service import ensure_demo_analysis
        analysis = ensure_demo_analysis(repo=repo, model_manager=model_mgr)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis '{analysis_id}' not found.",
        )

    results = analysis.anomalies
    if severity:
        results = [a for a in results if a.severity.upper() == severity.upper()]
    if anomaly_type:
        results = [a for a in results if any(anomaly_type.upper() in t.upper() for t in a.anomaly_types)]

    return results


@router.get("/{analysis_id}/{employee_id}", response_model=AnomalyRecordResult, status_code=status.HTTP_200_OK)
def get_employee_anomaly_detail(
    analysis_id: str,
    employee_id: str,
    repo: AnalysisRepository = Depends(get_analysis_repository),
    model_mgr: ModelManager = Depends(get_model_manager),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN, UserRole.AUDITOR, UserRole.VIEWER)
    ),
):
    """Retrieve detailed anomaly evidence, RAG sources, and explanation for a specific employee."""
    analysis = repo.get_analysis(analysis_id)
    if not analysis and analysis_id == "anl_demo_202406":
        from backend.services.demo_service import ensure_demo_analysis
        analysis = ensure_demo_analysis(repo=repo, model_manager=model_mgr)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis '{analysis_id}' not found.",
        )

    for anomaly in analysis.anomalies:
        if anomaly.employee_id == employee_id:
            audit_repo = DatabaseAuditRepository()
            audit_repo.log_event(
                event_type="ANOMALY_INVESTIGATED",
                analysis_id=analysis_id,
                actor_id=current_user.username,
                metadata={"employee_id": employee_id, "risk_score": anomaly.risk_score, "severity": anomaly.severity},
            )
            return anomaly

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Employee '{employee_id}' was not flagged as anomalous in analysis '{analysis_id}'.",
    )


@router.post("/{analysis_id}/{employee_id}/resolve", response_model=AnomalyResolutionResponse, status_code=status.HTTP_200_OK)
def resolve_anomaly(
    analysis_id: str,
    employee_id: str,
    payload: AnomalyResolutionRequest,
    repo: AnalysisRepository = Depends(get_analysis_repository),
    model_mgr: ModelManager = Depends(get_model_manager),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN, UserRole.AUDITOR)
    ),
):
    """Resolve an anomaly record with audit justification (Admin, Payroll Admin, or Auditor)."""
    analysis = repo.get_analysis(analysis_id)
    if not analysis and analysis_id == "anl_demo_202406":
        from backend.services.demo_service import ensure_demo_analysis
        analysis = ensure_demo_analysis(repo=repo, model_manager=model_mgr)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis '{analysis_id}' not found.",
        )

    now = datetime.utcnow()
    with SessionLocal() as db:
        record = (
            db.query(DBAnomalyRecord)
            .filter(
                DBAnomalyRecord.analysis_id == analysis_id,
                DBAnomalyRecord.employee_id == employee_id,
            )
            .first()
        )
        if record:
            record.status = payload.status
            record.resolution_notes = payload.resolution_notes
            record.resolved_by = current_user.username
            record.resolved_at = now
            db.commit()

    # Log ANOMALY_RESOLVED in audit trail
    audit_repo = DatabaseAuditRepository()
    audit_repo.log_event(
        event_type="ANOMALY_RESOLVED",
        analysis_id=analysis_id,
        actor_id=current_user.username,
        metadata={
            "employee_id": employee_id,
            "status": payload.status,
            "notes": payload.resolution_notes,
        },
    )

    return AnomalyResolutionResponse(
        analysis_id=analysis_id,
        employee_id=employee_id,
        status=payload.status,
        resolution_notes=payload.resolution_notes,
        resolved_by=current_user.username,
        resolved_at=now.isoformat(),
    )
