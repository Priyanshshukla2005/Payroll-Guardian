"""Unit and integration tests for Database persistence layer (Phase 10)."""

import pytest
from backend.database.models import Analysis as DBAnalysis, User as DBUser
from backend.database.repository import (
    DatabaseAnalysisRepository,
    DatabaseAuditRepository,
    DatabaseUserRepository,
)
from backend.database.session import SessionLocal, init_db
from backend.schemas.analysis import AnalysisResponse, AnalysisStatus, PipelineTimings
from backend.schemas.anomaly import AnalysisSummary, AnomalyRecordResult


def test_database_initialization_and_models():
    """Verify database schema creation and table initialization."""
    init_db()
    with SessionLocal() as db:
        # Check users table
        admin_user = db.query(DBUser).filter(DBUser.username == "admin").first()
        assert admin_user is not None
        assert admin_user.role == "ADMIN"
        assert admin_user.hashed_password.startswith("$2b$")


def test_database_analysis_repository_save_and_retrieve():
    """Verify saving and retrieving AnalysisResponse from persistent database."""
    repo = DatabaseAnalysisRepository()

    test_analysis = AnalysisResponse(
        request_id="req_test_persistence_001",
        analysis_id="anl_test_persistence_001",
        status=AnalysisStatus.COMPLETED,
        payroll_period="2024-06",
        summary=AnalysisSummary(
            records_analyzed=100,
            records_flagged=2,
            critical_risk=1,
            high_risk=1,
            medium_risk=0,
            low_risk=0,
        ),
        anomalies=[],
        model_version="v2",
        disclaimer="Test disclaimer",
        duration_ms=45.2,
        timings=PipelineTimings(
            feature_generation_ms=10.0,
            detection_ms=20.0,
            rag_ms=5.0,
            llm_ms=10.0,
            total_ms=45.2,
        ),
    )

    repo.save_analysis(test_analysis)

    # Retrieve from DB
    retrieved = repo.get_analysis("anl_test_persistence_001")
    assert retrieved is not None
    assert retrieved.analysis_id == "anl_test_persistence_001"
    assert retrieved.status == AnalysisStatus.COMPLETED
    assert retrieved.summary.records_analyzed == 100
    assert retrieved.summary.records_flagged == 2
    assert retrieved.duration_ms == 45.2


def test_database_list_analyses():
    """Verify listing recent analyses from persistent database."""
    repo = DatabaseAnalysisRepository()
    analyses = repo.list_analyses(limit=10)
    assert isinstance(analyses, list)
    assert len(analyses) >= 1
