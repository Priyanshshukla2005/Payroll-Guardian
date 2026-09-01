from abc import ABC, abstractmethod
from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.database.models import (
    Analysis as DBAnalysis,
    AnomalyRecord as DBAnomalyRecord,
    AuditEvent as DBAuditEvent,
    ComplianceSource as DBComplianceSource,
    PayrollBatch as DBPayrollBatch,
    PayrollRecord as DBPayrollRecord,
    User as DBUser,
)
from backend.database.session import SessionLocal
from backend.schemas.analysis import AnalysisResponse, AnalysisStatus, PipelineTimings
from backend.schemas.anomaly import (
    AnalysisSummary,
    AnomalyRecordResult,
    ComplianceSourceItem,
    ComplianceStatusBlock,
    ExplanationItem,
)
from backend.utils.security import generate_unique_id

logger = logging.getLogger("payroll_guardian.repository")


class AnalysisRepository(ABC):
    """Abstract persistence interface for storing and retrieving analysis reports."""

    @abstractmethod
    def save_analysis(self, analysis_response: AnalysisResponse) -> None:
        """Save a completed analysis response."""
        pass

    @abstractmethod
    def get_analysis(self, analysis_id: str) -> Optional[AnalysisResponse]:
        """Retrieve an analysis response by ID."""
        pass

    @abstractmethod
    def list_analyses(self, limit: int = 20) -> List[AnalysisResponse]:
        """List recent analyses."""
        pass


class DatabaseAnalysisRepository(AnalysisRepository):
    """Production SQL database implementation of AnalysisRepository."""

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def save_analysis(self, analysis_response: AnalysisResponse) -> None:
        """Persist or update an AnalysisResponse and its associated anomaly records."""
        with self.session_factory() as db:
            try:
                # Check if analysis already exists
                existing: Optional[DBAnalysis] = (
                    db.query(DBAnalysis)
                    .filter(DBAnalysis.analysis_id == analysis_response.analysis_id)
                    .first()
                )

                summary_str = json.dumps(analysis_response.summary.model_dump())
                timings_str = json.dumps(analysis_response.timings.model_dump())

                if existing:
                    existing.status = (
                        analysis_response.status.value
                        if hasattr(analysis_response.status, "value")
                        else str(analysis_response.status)
                    )
                    existing.payroll_period = analysis_response.payroll_period
                    existing.summary_json = summary_str
                    existing.timings_json = timings_str
                    existing.duration_ms = analysis_response.duration_ms
                    existing.model_version = analysis_response.model_version
                    existing.updated_at = datetime.utcnow()

                    # Delete existing anomalies to replace with updated list
                    db.query(DBAnomalyRecord).filter(
                        DBAnomalyRecord.analysis_id == analysis_response.analysis_id
                    ).delete()
                else:
                    status_val = (
                        analysis_response.status.value
                        if hasattr(analysis_response.status, "value")
                        else str(analysis_response.status)
                    )
                    db_analysis = DBAnalysis(
                        analysis_id=analysis_response.analysis_id,
                        request_id=analysis_response.request_id,
                        status=status_val,
                        payroll_period=analysis_response.payroll_period,
                        summary_json=summary_str,
                        timings_json=timings_str,
                        duration_ms=analysis_response.duration_ms,
                        model_version=analysis_response.model_version,
                        model_name=getattr(analysis_response, "model_name", "HybridPayrollDetector_v2"),
                        model_threshold=getattr(analysis_response, "model_threshold", 0.45),
                        feature_schema_version=getattr(analysis_response, "feature_schema_version", "features_v1"),
                        rag_knowledge_version=getattr(analysis_response, "rag_knowledge_version", "rag_2024_06"),
                        llm_version=getattr(analysis_response, "llm_version", "grounded_llm_v2"),
                        disclaimer=analysis_response.disclaimer,
                    )
                    db.add(db_analysis)

                # Persist anomalies
                for anomaly in analysis_response.anomalies:
                    db_anomaly = DBAnomalyRecord(
                        analysis_id=analysis_response.analysis_id,
                        employee_id=anomaly.employee_id,
                        payroll_month=anomaly.payroll_month,
                        department=anomaly.department,
                        designation=anomaly.designation,
                        risk_score=anomaly.risk_score,
                        severity=anomaly.severity,
                        anomaly_types_json=json.dumps(anomaly.anomaly_types),
                        rule_violations_json=json.dumps(anomaly.rule_violations),
                        evidence_json=json.dumps(anomaly.evidence),
                        historical_comparison_json=json.dumps(anomaly.historical_comparison),
                        peer_comparison_json=json.dumps(anomaly.peer_comparison),
                        compliance_json=json.dumps(anomaly.compliance.model_dump()),
                        explanation_json=json.dumps(anomaly.explanation.model_dump()),
                        status="FLAGGED",
                    )
                    db.add(db_anomaly)

                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to persist analysis {analysis_response.analysis_id}: {e}", exc_info=True)
                raise

    def get_analysis(self, analysis_id: str) -> Optional[AnalysisResponse]:
        """Retrieve an AnalysisResponse by its unique ID from the database."""
        with self.session_factory() as db:
            db_analysis: Optional[DBAnalysis] = (
                db.query(DBAnalysis)
                .filter(DBAnalysis.analysis_id == analysis_id)
                .first()
            )
            if not db_analysis:
                return None

            # Load anomaly records
            db_anomalies: List[DBAnomalyRecord] = (
                db.query(DBAnomalyRecord)
                .filter(DBAnomalyRecord.analysis_id == analysis_id)
                .all()
            )

            anomalies: List[AnomalyRecordResult] = []
            for a in db_anomalies:
                try:
                    comp_dict = json.loads(a.compliance_json)
                    comp_sources = [
                        ComplianceSourceItem(**src) for src in comp_dict.get("sources", [])
                    ]
                    comp_block = ComplianceStatusBlock(
                        status=comp_dict.get("status", "FOUND"),
                        sources=comp_sources,
                        no_answer_reason=comp_dict.get("no_answer_reason"),
                    )
                    expl_dict = json.loads(a.explanation_json)
                    expl_item = ExplanationItem(**expl_dict)

                    anomalies.append(
                        AnomalyRecordResult(
                            employee_id=a.employee_id,
                            payroll_month=a.payroll_month,
                            department=a.department,
                            designation=a.designation,
                            anomaly_types=json.loads(a.anomaly_types_json),
                            risk_score=a.risk_score,
                            severity=a.severity,
                            evidence=json.loads(a.evidence_json),
                            rule_violations=json.loads(a.rule_violations_json),
                            historical_comparison=json.loads(a.historical_comparison_json or "{}"),
                            peer_comparison=json.loads(a.peer_comparison_json or "{}"),
                            compliance=comp_block,
                            explanation=expl_item,
                        )
                    )
                except Exception as ex:
                    logger.warning(f"Error deserializing anomaly {a.employee_id}: {ex}")

            summary_dict = json.loads(db_analysis.summary_json)
            timings_dict = json.loads(db_analysis.timings_json)

            try:
                status_enum = AnalysisStatus(db_analysis.status)
            except ValueError:
                status_enum = AnalysisStatus.COMPLETED

            return AnalysisResponse(
                request_id=db_analysis.request_id,
                analysis_id=db_analysis.analysis_id,
                status=status_enum,
                payroll_period=db_analysis.payroll_period,
                summary=AnalysisSummary(**summary_dict),
                anomalies=anomalies,
                model_version=db_analysis.model_version,
                disclaimer=db_analysis.disclaimer or "AI-assisted payroll analysis. Not legal advice.",
                created_at=db_analysis.created_at.isoformat() if db_analysis.created_at else datetime.utcnow().isoformat(),
                duration_ms=db_analysis.duration_ms,
                timings=PipelineTimings(**timings_dict),
            )

    def list_analyses(self, limit: int = 20) -> List[AnalysisResponse]:
        """List the most recent analyses."""
        with self.session_factory() as db:
            rows = (
                db.query(DBAnalysis)
                .order_by(DBAnalysis.created_at.desc())
                .limit(limit)
                .all()
            )
            results = []
            for r in rows:
                anl = self.get_analysis(r.analysis_id)
                if anl:
                    results.append(anl)
            return results


class DatabaseUserRepository:
    """User account queries and authentication operations."""

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def get_by_username(self, username: str) -> Optional[DBUser]:
        with self.session_factory() as db:
            return db.query(DBUser).filter(DBUser.username == username).first()

    def get_by_email(self, email: str) -> Optional[DBUser]:
        with self.session_factory() as db:
            return db.query(DBUser).filter(DBUser.email == email).first()

    def create_user(
        self,
        username: str,
        email: str,
        hashed_password: str,
        role: str = "VIEWER",
        full_name: Optional[str] = None,
    ) -> DBUser:
        with self.session_factory() as db:
            user = DBUser(
                username=username,
                email=email,
                hashed_password=hashed_password,
                role=role,
                full_name=full_name,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user


class DatabaseAuditRepository:
    """Persistent audit trail event logging and query service."""

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def log_event(
        self,
        event_type: str,
        analysis_id: Optional[str] = None,
        actor_id: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> DBAuditEvent:
        """Create an immutable audit trail event."""
        with self.session_factory() as db:
            event = DBAuditEvent(
                event_id=generate_unique_id("evt"),
                timestamp=datetime.utcnow(),
                analysis_id=analysis_id,
                actor_id=actor_id,
                event_type=event_type,
                metadata_json=json.dumps(metadata or {}),
                request_id=request_id,
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            return event

    def get_events_for_analysis(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Retrieve chronological audit timeline for a specific analysis batch."""
        with self.session_factory() as db:
            events = (
                db.query(DBAuditEvent)
                .filter(DBAuditEvent.analysis_id == analysis_id)
                .order_by(DBAuditEvent.timestamp.asc())
                .all()
            )
            return [
                {
                    "event_id": e.event_id,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "analysis_id": e.analysis_id,
                    "actor_id": e.actor_id,
                    "event_type": e.event_type,
                    "metadata": json.loads(e.metadata_json or "{}"),
                    "request_id": e.request_id,
                }
                for e in events
            ]

    def list_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent audit events across the platform."""
        with self.session_factory() as db:
            events = (
                db.query(DBAuditEvent)
                .order_by(DBAuditEvent.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "event_id": e.event_id,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "analysis_id": e.analysis_id,
                    "actor_id": e.actor_id,
                    "event_type": e.event_type,
                    "metadata": json.loads(e.metadata_json or "{}"),
                    "request_id": e.request_id,
                }
                for e in events
            ]
