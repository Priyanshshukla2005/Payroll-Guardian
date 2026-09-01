"""Payroll ingestion, async processing, and batch analysis endpoints (Phase 10)."""

from pathlib import Path
from typing import Optional, Union
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status

from backend.auth.rbac import AuthenticatedUser, UserRole, require_roles
from backend.config.settings import settings
from backend.database.repository import DatabaseAuditRepository
from backend.dependencies.services import (
    AnalysisRepository,
    ModelManager,
    get_analysis_repository,
    get_model_manager,
)
from backend.schemas.analysis import AnalysisJobResponse, AnalysisResponse, AnalysisStatus
from backend.schemas.payroll import PayrollBatchAnalyzeRequest
from backend.services.analysis_service import AnalysisService
from backend.services.job_manager import JobManager
from backend.services.payroll_service import PayrollService
from backend.utils.security import sanitize_filename, validate_uploaded_file

router = APIRouter(prefix="/payroll", tags=["Payroll Analysis"])


@router.post(
    "/analyze",
    response_model=Union[AnalysisResponse, AnalysisJobResponse],
    status_code=status.HTTP_200_OK,
)
def analyze_payroll_json(
    payload: PayrollBatchAnalyzeRequest,
    request: Request,
    async_mode: bool = Query(False, description="Queue as asynchronous background job"),
    model_mgr: ModelManager = Depends(get_model_manager),
    repo: AnalysisRepository = Depends(get_analysis_repository),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN)
    ),
):
    """Analyze a JSON batch of payroll records through the complete intelligence stack."""
    request_id = getattr(request.state, "request_id", None)
    df_records = PayrollService.records_to_dataframe(payload.records)

    if async_mode:
        job_mgr = JobManager.get_instance()
        job_id = job_mgr.submit_job(
            df_records=df_records,
            payroll_period=payload.payroll_period,
            jurisdiction=payload.jurisdiction,
            request_id=request_id,
            actor_id=current_user.username,
        )
        return AnalysisJobResponse(
            analysis_id=job_id,
            status=AnalysisStatus.QUEUED,
            message=f"Payroll analysis job successfully queued with {len(df_records)} records.",
        )

    analysis_service = AnalysisService(model_manager=model_mgr, repository=repo)
    audit_repo = DatabaseAuditRepository()
    audit_repo.log_event(
        event_type="PAYROLL_UPLOADED",
        actor_id=current_user.username,
        metadata={"record_count": len(df_records), "jurisdiction": payload.jurisdiction or "INDIA", "mode": "synchronous"},
        request_id=request_id,
    )
    result = analysis_service.analyze_payroll(
        df_records=df_records,
        payroll_period=payload.payroll_period,
        jurisdiction=payload.jurisdiction,
        request_id=request_id,
    )
    audit_repo.log_event(
        event_type="ANALYSIS_COMPLETED",
        analysis_id=result.analysis_id,
        actor_id=current_user.username,
        metadata={"status": "SUCCESS", "flagged_count": len(result.anomalies), "duration_ms": result.duration_ms},
        request_id=request_id,
    )
    return result


@router.post(
    "/upload",
    response_model=Union[AnalysisResponse, AnalysisJobResponse],
    status_code=status.HTTP_200_OK,
)
async def analyze_payroll_file_upload(
    request: Request,
    file: UploadFile = File(..., description="Payroll file (CSV, JSON, or Parquet)"),
    payroll_period: Optional[str] = None,
    jurisdiction: Optional[str] = "INDIA",
    async_mode: bool = Query(False, description="Queue as asynchronous background job"),
    model_mgr: ModelManager = Depends(get_model_manager),
    repo: AnalysisRepository = Depends(get_analysis_repository),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN)
    ),
):
    """Upload and analyze a payroll file (CSV, JSON, Parquet) with strict security validation."""
    request_id = getattr(request.state, "request_id", None)
    raw_bytes = await file.read()

    # 1. Security & File Validation
    is_valid, err_msg = validate_uploaded_file(
        filename=file.filename,
        content_bytes=raw_bytes,
        content_type=file.content_type,
        max_size_mb=settings.max_upload_size_mb,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg or "Invalid uploaded file.",
        )

    # 2. Parse file into DataFrame
    safe_name = sanitize_filename(file.filename or "payroll.csv")
    ext = Path(safe_name).suffix.lower()

    try:
        if ext == ".csv":
            df_records = PayrollService.parse_csv(raw_bytes)
        elif ext == ".json":
            df_records = PayrollService.parse_json_bytes(raw_bytes)
        elif ext == ".parquet":
            df_records = PayrollService.parse_parquet(raw_bytes)
        else:
            raise ValueError(f"Unsupported format: {ext}")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # 3. Asynchronous vs Synchronous Execution
    if async_mode:
        job_mgr = JobManager.get_instance()
        job_id = job_mgr.submit_job(
            df_records=df_records,
            payroll_period=payroll_period,
            jurisdiction=jurisdiction,
            request_id=request_id,
            actor_id=current_user.username,
        )
        return AnalysisJobResponse(
            analysis_id=job_id,
            status=AnalysisStatus.QUEUED,
            message=f"Payroll file '{safe_name}' queued for background processing.",
        )

    analysis_service = AnalysisService(model_manager=model_mgr, repository=repo)
    audit_repo = DatabaseAuditRepository()
    audit_repo.log_event(
        event_type="PAYROLL_UPLOADED",
        actor_id=current_user.username,
        metadata={"filename": safe_name, "record_count": len(df_records), "jurisdiction": jurisdiction, "mode": "synchronous"},
        request_id=request_id,
    )
    result = analysis_service.analyze_payroll(
        df_records=df_records,
        payroll_period=payroll_period,
        jurisdiction=jurisdiction,
        request_id=request_id,
    )
    audit_repo.log_event(
        event_type="ANALYSIS_COMPLETED",
        analysis_id=result.analysis_id,
        actor_id=current_user.username,
        metadata={"status": "SUCCESS", "flagged_count": len(result.anomalies), "duration_ms": result.duration_ms},
        request_id=request_id,
    )
    return result


@router.get("/analysis/{analysis_id}", response_model=Union[AnalysisResponse, AnalysisJobResponse], status_code=status.HTTP_200_OK)
def get_analysis_by_id(
    analysis_id: str,
    repo: AnalysisRepository = Depends(get_analysis_repository),
    model_mgr: ModelManager = Depends(get_model_manager),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN, UserRole.AUDITOR, UserRole.VIEWER)
    ),
):
    """Retrieve an existing analysis report or status by its unique analysis ID."""
    result = repo.get_analysis(analysis_id)
    if not result and analysis_id == "anl_demo_202406":
        from backend.services.demo_service import ensure_demo_analysis
        result = ensure_demo_analysis(repo=repo, model_manager=model_mgr)

    if not result:
        # Check if job is currently queued / running in JobManager
        job_mgr = JobManager.get_instance()
        job_status = job_mgr.get_job_status(analysis_id)
        if job_status.get("status") in (AnalysisStatus.QUEUED, AnalysisStatus.RUNNING):
            return AnalysisJobResponse(
                analysis_id=analysis_id,
                status=job_status["status"],
                message=f"Analysis is currently {job_status['status'].value}.",
            )
        elif job_status.get("status") == AnalysisStatus.FAILED:
            return AnalysisJobResponse(
                analysis_id=analysis_id,
                status=AnalysisStatus.FAILED,
                message=f"Analysis failed: {job_status.get('error')}",
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis '{analysis_id}' not found.",
        )
    return result
