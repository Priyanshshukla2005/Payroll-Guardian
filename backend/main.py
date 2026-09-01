"""FastAPI Application Main Entrypoint for AI Payroll Guardian (Phase 10).

Orchestrates CORS, Request-ID tracing, privacy-safe logging, exception handlers,
and registers all API v1 routers with authentication and RBAC.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import (
    anomalies_router,
    assistant_router,
    audit_router,
    auth_router,
    compliance_router,
    diagnostics_router,
    health_router,
    monitoring_router,
    payroll_router,
)
from backend.config.settings import settings
from backend.database.seed import seed_database
from backend.database.session import init_db
from backend.dependencies.services import ModelManager
from backend.middleware import (
    PrivacySafeLoggingMiddleware,
    RequestIDMiddleware,
    register_exception_handlers,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("payroll_guardian.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager: initializes database, loads models, and sets up baseline."""
    logger.info("Starting AI Payroll Guardian Enterprise API Service (Phase 10)...")
    init_db()

    model_mgr = ModelManager.get_instance()
    model_mgr.initialize()

    # Seed default user accounts, compliance sources, and canonical demo analysis
    seed_database()

    logger.info("AI, RAG, LLM, Auth, and Database services successfully initialized.")
    yield
    logger.info("Shutting down AI Payroll Guardian API Service.")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.app_name,
        description=(
            "AI Payroll Guardian Backend REST API — Multi-layered AI anomaly detection, "
            "compliance RAG knowledge retrieval, and grounded audit explanations."
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Custom Middleware
    app.add_middleware(PrivacySafeLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # 3. Global Exception Handlers
    register_exception_handlers(app)

    # 4. Register API v1 Routers
    api_prefix = settings.api_prefix
    app.include_router(health_router, prefix=api_prefix)
    app.include_router(diagnostics_router, prefix=api_prefix)
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(payroll_router, prefix=api_prefix)
    app.include_router(anomalies_router, prefix=api_prefix)
    app.include_router(compliance_router, prefix=api_prefix)
    app.include_router(assistant_router, prefix=api_prefix)
    app.include_router(audit_router, prefix=api_prefix)
    app.include_router(monitoring_router, prefix=api_prefix)

    # Root redirect / status
    @app.get("/", tags=["Root"])
    def root():
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": f"{api_prefix}/health",
        }

    return app


app = create_app()
