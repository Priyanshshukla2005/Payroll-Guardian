"""Model monitoring, latency telemetry, and drift detection API endpoints (Phase 10)."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, status

from ai.monitoring.model_monitor import ModelMonitor
from backend.auth.rbac import AuthenticatedUser, UserRole, require_roles

router = APIRouter(prefix="/monitoring", tags=["Model Monitoring & Drift Telemetry"])


@router.get("/metrics", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_model_metrics(
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN, UserRole.AUDITOR, UserRole.VIEWER)
    ),
):
    """Retrieve runtime operational metrics, score distributions, and model versioning metadata."""
    monitor = ModelMonitor.get_instance()
    return monitor.get_telemetry_metrics()


@router.get("/drift", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_feature_drift(
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN, UserRole.AUDITOR)
    ),
):
    """Retrieve statistical feature drift analysis and warning status for monitored payroll variables."""
    monitor = ModelMonitor.get_instance()
    return monitor.get_latest_drift_report()
