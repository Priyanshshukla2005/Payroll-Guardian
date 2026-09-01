"""Comprehensive tests for Database Persistence, SQLAlchemy ORM, and Repository Abstractions (Phase 10)."""

from datetime import datetime
import pytest

from backend.database.models import (
    Analysis as DBAnalysis,
    AnomalyRecord as DBAnomalyRecord,
    AuditEvent as DBAuditEvent,
    PayrollBatch as DBPayrollBatch,
    PayrollRecord as DBPayrollRecord,
    User as DBUser,
)
from backend.database.repository import (
    DatabaseAnalysisRepository,
    DatabaseAuditRepository,
    DatabaseUserRepository,
)
from backend.database.session import SessionLocal, init_db
from backend.schemas.analysis import AnalysisResponse, AnalysisStatus, PipelineTimings
from backend.schemas.anomaly import (
    AnalysisSummary,
    AnomalyRecordResult,
    ComplianceSourceItem,
    ComplianceStatusBlock,
    ExplanationItem,
)
from backend.utils.security import generate_unique_id


def test_database_initialization_tables():
    """Verify schema initialization creates all tables without error."""
    init_db()
    with SessionLocal() as db:
        # Check users table
        admin = db.query(DBUser).filter(DBUser.username == "admin").first()
        assert admin is not None
        assert admin.role == "ADMIN"
        assert admin.hashed_password.startswith("$2b$") or admin.hashed_password.startswith("$2a$")
        assert not admin.hashed_password.startswith("AdminPassword")  # Never plaintext


def test_user_repository_create_and_query():
    """Verify DatabaseUserRepository creates and fetches users correctly."""
    repo = DatabaseUserRepository()
    unique_user = f"test_user_{generate_unique_id('u')}"
    unique_email = f"{unique_user}@test.internal"

    created = repo.create_user(
        username=unique_user,
        email=unique_email,
        hashed_password="$2b$12$dummyhashforpersistencetestingpurposeonly000000000000000",
        role="AUDITOR",
        full_name="Persistent Test Auditor",
    )
    assert created.id is not None
    assert created.username == unique_user

    # Fetch by username
    fetched_by_user = repo.get_by_username(unique_user)
    assert fetched_by_user is not None
    assert fetched_by_user.email == unique_email
    assert fetched_by_user.role == "AUDITOR"

    # Fetch by email
    fetched_by_email = repo.get_by_email(unique_email)
    assert fetched_by_email is not None
    assert fetched_by_email.username == unique_user


def test_audit_repository_logging_and_retrieval():
    """Verify audit events are written and queried chronologically."""
    audit_repo = DatabaseAuditRepository()
    test_analysis_id = generate_unique_id("anl_persist_audit")

    # Log 3 events
    evt1 = audit_repo.log_event(
        event_type="PAYROLL_UPLOADED",
        analysis_id=test_analysis_id,
        actor_id="test_officer",
        metadata={"records": 50, "mode": "sync"},
    )
    assert evt1.event_id is not None

    evt2 = audit_repo.log_event(
        event_type="ANALYSIS_STARTED",
        analysis_id=test_analysis_id,
        actor_id="test_officer",
    )
    assert evt2.event_id is not None

    evt3 = audit_repo.log_event(
        event_type="ANALYSIS_COMPLETED",
        analysis_id=test_analysis_id,
        actor_id="test_officer",
        metadata={"status": "SUCCESS"},
    )
    assert evt3.event_id is not None

    # Retrieve events for analysis
    timeline = audit_repo.get_events_for_analysis(test_analysis_id)
    assert len(timeline) == 3
    assert timeline[0]["event_type"] == "PAYROLL_UPLOADED"
    assert timeline[1]["event_type"] == "ANALYSIS_STARTED"
    assert timeline[2]["event_type"] == "ANALYSIS_COMPLETED"
    assert timeline[0]["actor_id"] == "test_officer"


def test_analysis_and_anomaly_persistence_across_sessions():
    """Verify AnalysisResponse and nested AnomalyRecords persist across new sessions."""
    repo = DatabaseAnalysisRepository()
    analysis_id = generate_unique_id("anl_persist_full")

    comp_src = ComplianceSourceItem(
        document_id="epfo_act_1952",
        title="Employees' Provident Funds and Miscellaneous Provisions Act, 1952",
        source_type="STATUTE",
        authority_level="AUTHORITATIVE",
        jurisdiction="INDIA",
        relevance_score=0.92,
        citation="Section 6 - Contributions",
        excerpt="The contribution shall be 12% of basic wage.",
    )
    comp_block = ComplianceStatusBlock(status="FOUND", sources=[comp_src])

    expl_item = ExplanationItem(
        summary="Statutory under-deduction of PF.",
        root_cause="Calculated PF was 5% instead of 12%.",
        recommended_action="Adjust employee deductions and remit difference.",
        confidence_level="HIGH",
        groundedness_score=0.95,
    )

    anomaly = AnomalyRecordResult(
        employee_id="EMP_PERSIST_001",
        payroll_month="2024-06",
        department="Engineering",
        designation="Software Engineer",
        anomaly_types=["INCORRECT_PF_RATE"],
        risk_score=0.88,
        severity="CRITICAL",
        evidence=["PF rate deducted was 5.0% vs mandatory 12.0%"],
        rule_violations=["EPFO Section 6 Violation"],
        historical_comparison={},
        peer_comparison={},
        compliance=comp_block,
        explanation=expl_item,
    )

    analysis_res = AnalysisResponse(
        request_id=generate_unique_id("req_persist"),
        analysis_id=analysis_id,
        status=AnalysisStatus.COMPLETED,
        payroll_period="2024-06",
        summary=AnalysisSummary(
            records_analyzed=1,
            records_flagged=1,
            critical_risk=1,
            high_risk=0,
            medium_risk=0,
            low_risk=0,
        ),
        anomalies=[anomaly],
        duration_ms=55.0,
        timings=PipelineTimings(total_ms=55.0),
    )

    # Save to database
    repo.save_analysis(analysis_res)

    # Re-instantiate repository (simulating new request / session)
    new_repo = DatabaseAnalysisRepository()
    retrieved = new_repo.get_analysis(analysis_id)

    assert retrieved is not None
    assert retrieved.analysis_id == analysis_id
    assert retrieved.status == AnalysisStatus.COMPLETED
    assert retrieved.summary.records_analyzed == 1
    assert retrieved.summary.records_flagged == 1
    assert len(retrieved.anomalies) == 1
    retrieved_anom = retrieved.anomalies[0]
    assert retrieved_anom.employee_id == "EMP_PERSIST_001"
    assert retrieved_anom.severity == "CRITICAL"
    assert retrieved_anom.risk_score == 0.88
    assert retrieved_anom.compliance.status == "FOUND"
    assert len(retrieved_anom.compliance.sources) == 1
    assert retrieved_anom.compliance.sources[0].document_id == "epfo_act_1952"


def test_payroll_batch_and_record_orm_persistence():
    """Verify PayrollBatch and PayrollRecord entities persist properly in ORM."""
    batch_id = generate_unique_id("batch_test")
    with SessionLocal() as db:
        batch = DBPayrollBatch(
            batch_id=batch_id,
            filename="june_2024_payroll.csv",
            file_format="csv",
            row_count=1,
            uploaded_by="payroll_officer_test",
            status="READY",
        )
        db.add(batch)

        record = DBPayrollRecord(
            batch_id=batch_id,
            employee_id="EMP_ROW_001",
            payroll_month="2024-06",
            department="Finance",
            designation="Analyst",
            location="INDIA",
            basic_salary=60000.0,
            gross_salary=85000.0,
            net_salary=77000.0,
            pf_deduction=7200.0,
        )
        db.add(record)
        db.commit()

    # Reopen and query
    with SessionLocal() as db:
        queried_batch = db.query(DBPayrollBatch).filter(DBPayrollBatch.batch_id == batch_id).first()
        assert queried_batch is not None
        assert queried_batch.filename == "june_2024_payroll.csv"
        assert queried_batch.row_count == 1

        queried_record = db.query(DBPayrollRecord).filter(DBPayrollRecord.batch_id == batch_id).first()
        assert queried_record is not None
        assert queried_record.employee_id == "EMP_ROW_001"
        assert queried_record.basic_salary == 60000.0
