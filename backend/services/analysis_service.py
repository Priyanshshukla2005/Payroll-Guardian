import logging
import time
from typing import Any, Dict, List, Optional
import pandas as pd

from ai.explainability.explainer_v2 import DetailedEvidenceCard
from ai.monitoring.model_monitor import ModelMonitor
from backend.config.settings import settings
from backend.dependencies.services import AnalysisRepository, ModelManager
from backend.schemas.analysis import AnalysisResponse, AnalysisStatus, PipelineTimings
from backend.schemas.anomaly import (
    AnalysisSummary,
    AnomalyRecordResult,
    ComplianceSourceItem,
    ComplianceStatusBlock,
)
from backend.services.compliance_service import ComplianceService
from backend.services.detection_service import DetectionService
from backend.services.explanation_service import ExplanationService
from backend.utils.security import generate_unique_id
from rag.metadata import StructuredRAGResponse

logger = logging.getLogger("payroll_guardian.analysis")


class AnalysisService:
    """Master orchestrator executing the complete Payroll Guardian intelligence pipeline."""

    def __init__(
        self,
        model_manager: ModelManager,
        repository: AnalysisRepository,
    ):
        self.model_manager = model_manager
        self.repository = repository
        self.detection_service = DetectionService(model_manager)
        self.compliance_service = ComplianceService(model_manager)
        self.explanation_service = ExplanationService(model_manager)

    def analyze_payroll(
        self,
        df_records: pd.DataFrame,
        payroll_period: Optional[str] = None,
        jurisdiction: Optional[str] = "INDIA",
        decision_threshold: float = 0.45,
        request_id: Optional[str] = None,
    ) -> AnalysisResponse:
        """Run complete end-to-end analysis pipeline across payroll DataFrame."""
        start_time = time.perf_counter()
        req_id = request_id or generate_unique_id("req")
        analysis_id = generate_unique_id("anl")

        # 1. Determine payroll period from records if not specified
        period = payroll_period
        if not period and "payroll_month" in df_records.columns and len(df_records) > 0:
            period = str(df_records["payroll_month"].iloc[0])
        period = period or "2024-06"

        # 2. Run Hybrid Detection Service
        t_detect_start = time.perf_counter()
        detection_results = self.detection_service.detect_anomalies(
            df_raw=df_records,
            decision_threshold=decision_threshold,
        )
        feature_gen_ms = getattr(self.detection_service, "last_feature_time_ms", 0.0)
        detect_ms = getattr(self.detection_service, "last_detection_time_ms", 0.0)

        total_analyzed = len(df_records)
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        anomaly_results: List[AnomalyRecordResult] = []
        all_risk_scores: List[float] = []
        all_severities: List[str] = []
        total_rag_ms = 0.0
        total_llm_ms = 0.0

        # 3. Process each record and build compliance + explanations for flagged items
        for raw_row, risk_score, anomaly_types, rule_violations, card in detection_results:
            all_risk_scores.append(risk_score)

            # Map Severity Label
            if risk_score >= 0.85 or len(rule_violations) >= 2:
                sev_label = "CRITICAL"
                critical_count += 1
            elif risk_score >= 0.65 or len(rule_violations) >= 1:
                sev_label = "HIGH"
                high_count += 1
            elif risk_score >= 0.45:
                sev_label = "MEDIUM"
                medium_count += 1
            else:
                sev_label = "LOW"
                low_count += 1

            all_severities.append(sev_label)

            # Check if record is flagged for investigation
            is_flagged = (risk_score >= decision_threshold) or (len(rule_violations) > 0)

            if is_flagged:
                # 4. RAG Compliance Knowledge Retrieval
                t_rag_start = time.perf_counter()
                row_jurisdiction = raw_row.get("location", jurisdiction or "INDIA")
                rag_resp: StructuredRAGResponse = self.compliance_service.retrieve_for_evidence_card(
                    evidence_card=card,
                    jurisdiction_override=row_jurisdiction,
                    top_n=2,
                )
                total_rag_ms += (time.perf_counter() - t_rag_start) * 1000.0

                compliance_sources = [
                    ComplianceSourceItem(
                        document_id=r.document_id,
                        title=r.title,
                        authority_level=r.authority_level.value,
                        section=r.section,
                        page=r.page,
                        citation=r.citation,
                    )
                    for r in rag_resp.results
                ]

                # Map status: "SUCCESS" with results -> "FOUND"
                comp_status = rag_resp.status
                if comp_status == "SUCCESS" and len(compliance_sources) > 0:
                    comp_status = "FOUND"

                compliance_block = ComplianceStatusBlock(
                    status=comp_status,
                    sources=compliance_sources,
                    no_answer_reason=rag_resp.no_answer_reason,
                )

                # 5. Grounded LLM Explanation Generation (with Fallback)
                t_llm_start = time.perf_counter()
                explanation_item = self.explanation_service.explain_anomaly(
                    evidence_card=card,
                    rag_response=rag_resp,
                    raw_record=raw_row.to_dict(),
                )
                total_llm_ms += (time.perf_counter() - t_llm_start) * 1000.0

                rec_result = AnomalyRecordResult(
                    employee_id=card.employee_id,
                    payroll_month=card.payroll_month,
                    department=str(raw_row.get("department", "General")),
                    designation=str(raw_row.get("designation", "Staff")),
                    anomaly_types=card.anomaly_types,
                    risk_score=card.risk_score,
                    severity=sev_label,
                    evidence=card.top_signals,
                    rule_violations=card.rule_violations,
                    historical_comparison=card.historical_comparison,
                    peer_comparison=card.peer_comparison,
                    compliance=compliance_block,
                    explanation=explanation_item,
                )
                anomaly_results.append(rec_result)

        # 6. Summary Metrics
        summary = AnalysisSummary(
            records_analyzed=total_analyzed,
            records_flagged=len(anomaly_results),
            critical_risk=critical_count,
            high_risk=high_count,
            medium_risk=medium_count,
            low_risk=low_count,
        )

        total_duration_ms = (time.perf_counter() - start_time) * 1000.0

        timings = PipelineTimings(
            feature_generation_ms=round(feature_gen_ms, 2),
            detection_ms=round(detect_ms, 2),
            rag_ms=round(total_rag_ms, 2),
            llm_ms=round(total_llm_ms, 2),
            total_ms=round(total_duration_ms, 2),
        )

        model_ver = self.model_manager.detector.name if self.model_manager.detector else "v2"

        # 7. Create Response
        response = AnalysisResponse(
            request_id=req_id,
            analysis_id=analysis_id,
            status=AnalysisStatus.COMPLETED,
            payroll_period=period,
            summary=summary,
            anomalies=anomaly_results,
            model_name=settings.model_name,
            model_version=model_ver,
            model_threshold=settings.model_threshold,
            feature_schema_version=settings.feature_schema_version,
            rag_knowledge_version=settings.rag_knowledge_version,
            llm_version=settings.llm_version,
            disclaimer="AI-assisted payroll analysis. Not legal advice.",
            duration_ms=round(total_duration_ms, 2),
            timings=timings,
        )

        # 8. Record telemetry in ModelMonitor
        try:
            monitor = ModelMonitor.get_instance()
            monitor.record_analysis_telemetry(
                df_records=df_records,
                risk_scores=all_risk_scores,
                severities=all_severities,
                duration_ms=total_duration_ms,
            )
        except Exception as ex:
            logger.warning(f"Failed to record model telemetry: {ex}")

        # 9. Structured observability log (zero PII)
        logger.info(
            f"analysis_completed request_id={req_id} analysis_id={analysis_id} "
            f"records={total_analyzed} flagged={len(anomaly_results)} "
            f"duration_ms={total_duration_ms:.2f} model_version={model_ver}"
        )

        # 10. Save in Persistence Repository
        self.repository.save_analysis(response)
        return response
