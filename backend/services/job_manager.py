"""Asynchronous job management and background batch processing (Phase 10)."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
from typing import Any, Dict, Optional
import pandas as pd

from backend.database.models import Analysis as DBAnalysis
from backend.database.repository import DatabaseAnalysisRepository, DatabaseAuditRepository
from backend.database.session import SessionLocal
from backend.dependencies.services import ModelManager
from backend.schemas.analysis import AnalysisResponse, AnalysisStatus
from backend.services.analysis_service import AnalysisService
from backend.utils.security import generate_unique_id

logger = logging.getLogger("payroll_guardian.jobs")


class JobManager:
    """Thread-safe background job manager for asynchronous large payroll analysis batches."""

    _instance: Optional["JobManager"] = None

    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="payroll_job_worker")
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self.audit_repo = DatabaseAuditRepository()

    @classmethod
    def get_instance(cls) -> "JobManager":
        if cls._instance is None:
            cls._instance = JobManager()
        return cls._instance

    def submit_job(
        self,
        df_records: pd.DataFrame,
        payroll_period: Optional[str] = None,
        jurisdiction: Optional[str] = "INDIA",
        decision_threshold: float = 0.45,
        request_id: Optional[str] = None,
        actor_id: str = "system",
    ) -> str:
        """Queue a background analysis task and return the unique analysis_id."""
        analysis_id = generate_unique_id("anl")
        req_id = request_id or generate_unique_id("req")

        self._jobs[analysis_id] = {
            "analysis_id": analysis_id,
            "request_id": req_id,
            "status": AnalysisStatus.QUEUED,
            "submitted_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "total_records": len(df_records),
            "error": None,
        }

        # Log audit events
        self.audit_repo.log_event(
            event_type="PAYROLL_UPLOADED",
            analysis_id=analysis_id,
            actor_id=actor_id,
            metadata={"record_count": len(df_records), "jurisdiction": jurisdiction},
            request_id=req_id,
        )
        self.audit_repo.log_event(
            event_type="VALIDATION_STARTED",
            analysis_id=analysis_id,
            actor_id=actor_id,
            request_id=req_id,
        )
        self.audit_repo.log_event(
            event_type="VALIDATION_COMPLETED",
            analysis_id=analysis_id,
            actor_id=actor_id,
            metadata={"status": "VALID", "valid_records": len(df_records)},
            request_id=req_id,
        )

        # Submit to thread pool
        self.executor.submit(
            self._execute_analysis_task,
            analysis_id=analysis_id,
            df_records=df_records,
            payroll_period=payroll_period,
            jurisdiction=jurisdiction,
            decision_threshold=decision_threshold,
            request_id=req_id,
            actor_id=actor_id,
        )

        logger.info(f"Queued background analysis job '{analysis_id}' with {len(df_records)} records.")
        return analysis_id

    def _execute_analysis_task(
        self,
        analysis_id: str,
        df_records: pd.DataFrame,
        payroll_period: Optional[str],
        jurisdiction: Optional[str],
        decision_threshold: float,
        request_id: str,
        actor_id: str,
    ) -> None:
        """Worker thread processing ML, Evidence, RAG, and LLM steps."""
        self._jobs[analysis_id]["status"] = AnalysisStatus.RUNNING

        self.audit_repo.log_event(
            event_type="ANALYSIS_STARTED",
            analysis_id=analysis_id,
            actor_id=actor_id,
            request_id=request_id,
        )

        try:
            model_mgr = ModelManager.get_instance()
            repo = DatabaseAnalysisRepository()
            analysis_service = AnalysisService(model_manager=model_mgr, repository=repo)

            result: AnalysisResponse = analysis_service.analyze_payroll(
                df_records=df_records,
                payroll_period=payroll_period,
                jurisdiction=jurisdiction,
                decision_threshold=decision_threshold,
                request_id=request_id,
            )

            # Override the generated analysis_id to match the queued job ID
            result.analysis_id = analysis_id
            repo.save_analysis(result)

            # Audit events for completed stages
            self.audit_repo.log_event(
                event_type="ANOMALY_DETECTED",
                analysis_id=analysis_id,
                actor_id=actor_id,
                metadata={"flagged_count": len(result.anomalies)},
                request_id=request_id,
            )
            self.audit_repo.log_event(
                event_type="EVIDENCE_GENERATED",
                analysis_id=analysis_id,
                actor_id=actor_id,
                metadata={"evidence_cards_count": len(result.anomalies)},
                request_id=request_id,
            )
            self.audit_repo.log_event(
                event_type="COMPLIANCE_RETRIEVED",
                analysis_id=analysis_id,
                actor_id=actor_id,
                request_id=request_id,
            )
            self.audit_repo.log_event(
                event_type="LLM_EXPLANATION_GENERATED",
                analysis_id=analysis_id,
                actor_id=actor_id,
                request_id=request_id,
            )
            self.audit_repo.log_event(
                event_type="ANALYSIS_COMPLETED",
                analysis_id=analysis_id,
                actor_id=actor_id,
                metadata={"status": "SUCCESS", "duration_ms": result.duration_ms},
                request_id=request_id,
            )

            self._jobs[analysis_id]["status"] = AnalysisStatus.COMPLETED
            self._jobs[analysis_id]["completed_at"] = datetime.utcnow().isoformat()
            logger.info(f"Background analysis job '{analysis_id}' completed successfully in {result.duration_ms:.2f}ms.")
        except Exception as e:
            logger.error(f"Background analysis job '{analysis_id}' failed: {e}", exc_info=True)
            self._jobs[analysis_id]["status"] = AnalysisStatus.FAILED
            self._jobs[analysis_id]["error"] = str(e)
            self._jobs[analysis_id]["completed_at"] = datetime.utcnow().isoformat()

            self.audit_repo.log_event(
                event_type="ANALYSIS_FAILED",
                analysis_id=analysis_id,
                actor_id=actor_id,
                metadata={"error": str(e)},
                request_id=request_id,
            )

    def get_job_status(self, analysis_id: str) -> Dict[str, Any]:
        """Check status of a job."""
        if analysis_id in self._jobs:
            return self._jobs[analysis_id]

        # Check database if analysis already exists
        repo = DatabaseAnalysisRepository()
        existing = repo.get_analysis(analysis_id)
        if existing:
            return {
                "analysis_id": analysis_id,
                "request_id": existing.request_id,
                "status": existing.status,
                "submitted_at": existing.created_at,
                "completed_at": existing.created_at,
                "total_records": existing.summary.records_analyzed,
                "error": None,
            }

        return {
            "analysis_id": analysis_id,
            "status": "NOT_FOUND",
            "error": f"Analysis job '{analysis_id}' not found.",
        }
