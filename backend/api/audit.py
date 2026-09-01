"""Audit trail inspection and compliance event history endpoints (Phase 10)."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, status

from backend.auth.rbac import AuthenticatedUser, UserRole, require_roles
from backend.database.repository import DatabaseAuditRepository

router = APIRouter(prefix="/audit", tags=["Audit Trail & History"])


@router.get("/events", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
def list_audit_events(
    limit: int = Query(50, ge=1, le=500),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN, UserRole.AUDITOR, UserRole.VIEWER)
    ),
):
    """Retrieve immutable platform audit events with privacy-safe metadata."""
    repo = DatabaseAuditRepository()
    return repo.list_events(limit=limit)


@router.get("/analysis/{analysis_id}", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
def get_analysis_audit_timeline(
    analysis_id: str,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN, UserRole.AUDITOR, UserRole.VIEWER)
    ),
):
    """Retrieve the chronological audit timeline for a specific payroll analysis batch."""
    repo = DatabaseAuditRepository()
    return repo.get_events_for_analysis(analysis_id=analysis_id)
