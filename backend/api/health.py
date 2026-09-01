"""Health check and readiness diagnostic endpoints (Phase 10)."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text

from backend.config.settings import settings
from backend.database.session import SessionLocal
from backend.dependencies.services import ModelManager, get_model_manager
from backend.schemas.common import (
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
    ServiceStatus,
)

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])
diagnostics_router = APIRouter(tags=["Health & Diagnostics"])


def check_db_health() -> str:
    """Lightweight ping verifying database connectivity."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return "available"
    except Exception:
        return "unavailable"


@router.get("", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def get_health(model_mgr: ModelManager = Depends(get_model_manager)):
    """General health check verifying operational status across all intelligence services and database."""
    service_status = model_mgr.check_health()
    service_status["database"] = check_db_health()

    if all(s == "available" for s in service_status.values()):
        overall_status = "healthy"
    elif service_status.get("ai") == "available":
        overall_status = "degraded"
    else:
        overall_status = "unavailable"

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.app_env,
        services=ServiceStatus(**service_status),
    )


@router.get("/live", response_model=LivenessResponse, status_code=status.HTTP_200_OK)
@router.get("/liveness", response_model=LivenessResponse, status_code=status.HTTP_200_OK)
def get_liveness():
    """Lightweight liveness probe for Kubernetes / container monitoring."""
    return LivenessResponse(status="live")


@router.get("/ready", response_model=ReadinessResponse, status_code=status.HTTP_200_OK)
@router.get("/readiness", response_model=ReadinessResponse, status_code=status.HTTP_200_OK)
def get_readiness(response: Response, model_mgr: ModelManager = Depends(get_model_manager)):
    """Readiness probe checking that models, vector store indices, and database are actively loaded."""
    if not model_mgr.is_loaded:
        try:
            model_mgr.initialize()
        except Exception:
            pass

    chunk_count = len(model_mgr.retriever.vector_store.chunks_metadata) if (model_mgr.retriever and model_mgr.retriever.vector_store) else 0
    db_status = check_db_health()
    is_ready = model_mgr.is_loaded and db_status == "available"

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "unready",
        model_version=settings.ai_model_version,
        rag_indexed_chunks=chunk_count,
        llm_provider=settings.llm_provider,
        database="connected" if db_status == "available" else "disconnected",
    )


# Direct /live and /ready routes on diagnostics_router for /api/v1/live and /api/v1/ready
diagnostics_router.add_api_route(
    "/live",
    get_liveness,
    methods=["GET"],
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Direct Kubernetes liveness probe",
)
diagnostics_router.add_api_route(
    "/ready",
    get_readiness,
    methods=["GET"],
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Direct Kubernetes readiness probe",
)
