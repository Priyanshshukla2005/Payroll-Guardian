"""Backend API routers module (Phase 10)."""

from backend.api.anomalies import router as anomalies_router
from backend.api.assistant import router as assistant_router
from backend.api.audit import router as audit_router
from backend.api.auth import router as auth_router
from backend.api.compliance import router as compliance_router
from backend.api.health import diagnostics_router, router as health_router
from backend.api.monitoring import router as monitoring_router
from backend.api.payroll import router as payroll_router

__all__ = [
    "health_router",
    "diagnostics_router",
    "auth_router",
    "payroll_router",
    "anomalies_router",
    "compliance_router",
    "assistant_router",
    "audit_router",
    "monitoring_router",
]
