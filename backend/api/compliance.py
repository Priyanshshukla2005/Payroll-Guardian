"""Compliance knowledge search and source provenance endpoints (Phase 10)."""

import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status

from backend.auth.rbac import AuthenticatedUser, UserRole, require_roles
from backend.config.settings import settings
from backend.database.repository import DatabaseAuditRepository
from backend.dependencies.services import ModelManager, get_model_manager
from backend.schemas.compliance import (
    ComplianceSearchRequest,
    ComplianceSearchResult,
)
from backend.services.compliance_service import ComplianceService

router = APIRouter(prefix="/compliance", tags=["Compliance Knowledge RAG"])


@router.post("/search", response_model=ComplianceSearchResult, status_code=status.HTTP_200_OK)
def search_compliance_knowledge(
    payload: ComplianceSearchRequest,
    model_mgr: ModelManager = Depends(get_model_manager),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN, UserRole.AUDITOR, UserRole.VIEWER)
    ),
):
    """Search authoritative compliance acts, circulars, and internal policies."""
    compliance_service = ComplianceService(model_manager=model_mgr)
    result = compliance_service.search_compliance(
        query=payload.query,
        jurisdiction=payload.jurisdiction or "INDIA",
        payroll_date=payload.payroll_date or "2024-06-01",
        topic=payload.topic,
        top_n=payload.top_n,
    )
    audit_repo = DatabaseAuditRepository()
    audit_repo.log_event(
        event_type="COMPLIANCE_SEARCHED",
        actor_id=current_user.username,
        metadata={"query": payload.query[:100], "jurisdiction": payload.jurisdiction or "INDIA", "results_count": len(result.results)},
    )
    return result


@router.get("/sources", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
def list_compliance_sources(
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN, UserRole.AUDITOR, UserRole.VIEWER)
    ),
):
    """Retrieve all verified statutory acts and policy documents with SHA-256 provenance hashes."""
    registry_file = settings.raw_knowledge_dir.parent / "metadata" / "registry.json"
    if not registry_file.exists():
        return []

    try:
        with open(registry_file, "r", encoding="utf-8") as f:
            registry = json.load(f)
        return list(registry.values())
    except Exception:
        return []
