"""Payroll AI Assistant conversational inquiry endpoints (Phase 10)."""

from fastapi import APIRouter, Depends, HTTPException, status

from ai.explainability.explainer_v2 import DetailedEvidenceCard
from backend.auth.rbac import AuthenticatedUser, UserRole, require_roles
from backend.database.repository import DatabaseAuditRepository
from backend.dependencies.services import (
    AnalysisRepository,
    ModelManager,
    get_analysis_repository,
    get_model_manager,
)
from backend.schemas.assistant import (
    AssistantQueryRequest,
    AssistantQueryResponseSchema,
)
from backend.services.explanation_service import ExplanationService

router = APIRouter(prefix="/assistant", tags=["Payroll AI Assistant"])


@router.post("/query", response_model=AssistantQueryResponseSchema, status_code=status.HTTP_200_OK)
def query_assistant(
    payload: AssistantQueryRequest,
    model_mgr: ModelManager = Depends(get_model_manager),
    repo: AnalysisRepository = Depends(get_analysis_repository),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ADMIN, UserRole.PAYROLL_ADMIN, UserRole.AUDITOR)
    ),
):
    """Ask grounded payroll and compliance questions to the AI Assistant."""
    card = None
    if payload.analysis_id:
        analysis = repo.get_analysis(payload.analysis_id)
        if not analysis and payload.analysis_id == "anl_demo_202406":
            from backend.services.demo_service import ensure_demo_analysis
            analysis = ensure_demo_analysis(repo=repo, model_manager=model_mgr)

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis '{payload.analysis_id}' not found.",
            )

        if payload.employee_id:
            # Find specific employee record
            found_anomaly = next((a for a in analysis.anomalies if a.employee_id == payload.employee_id), None)
            if not found_anomaly:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Employee '{payload.employee_id}' not found in analysis '{payload.analysis_id}'.",
                )
            card = DetailedEvidenceCard(
                employee_id=found_anomaly.employee_id,
                payroll_month=found_anomaly.payroll_month,
                risk_score=found_anomaly.risk_score,
                confidence="HIGH" if found_anomaly.risk_score >= 0.65 else "MEDIUM",
                top_signals=found_anomaly.evidence,
                historical_comparison=found_anomaly.historical_comparison,
                peer_comparison=found_anomaly.peer_comparison,
                rule_violations=found_anomaly.rule_violations,
                anomaly_types=found_anomaly.anomaly_types,
                human_readable_summary=found_anomaly.explanation.summary,
            )
        else:
            # Batch-level context for inquiry in the scope of this analysis
            top_sigs = [s for a in analysis.anomalies[:3] for s in a.evidence[:1]] or ["Payroll batch audit analysis"]
            all_types = list({t for a in analysis.anomalies for t in a.anomaly_types}) or ["AUDIT_REVIEW"]
            card = DetailedEvidenceCard(
                employee_id="BATCH_AUDIT",
                payroll_month=analysis.payroll_period,
                risk_score=0.0,
                confidence="HIGH",
                top_signals=top_sigs,
                historical_comparison={},
                peer_comparison={},
                rule_violations=[v for a in analysis.anomalies for v in a.rule_violations][:5],
                anomaly_types=all_types,
                human_readable_summary=f"Analysis {analysis.analysis_id} for period {analysis.payroll_period} ({len(analysis.anomalies)} flagged records).",
            )

    explanation_service = ExplanationService(model_manager=model_mgr)
    response = explanation_service.answer_assistant_query(
        question=payload.question,
        evidence_card=card,
    )
    audit_repo = DatabaseAuditRepository()
    audit_repo.log_event(
        event_type="ASSISTANT_QUERIED",
        analysis_id=payload.analysis_id,
        actor_id=current_user.username,
        metadata={
            "question": payload.question[:100],
            "employee_id": payload.employee_id,
            "citations_count": len(response.citations),
        },
    )
    return response
