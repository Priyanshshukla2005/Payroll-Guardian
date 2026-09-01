"""Model monitor orchestrator and telemetry provider (Phase 10)."""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
import pandas as pd

from ai.monitoring.drift_detector import FeatureDriftDetector
from ai.monitoring.metrics import ModelMetricsCalculator
from backend.config.settings import settings

logger = logging.getLogger("payroll_guardian.monitoring")


class ModelMonitor:
    """Singleton model telemetry and monitoring service."""

    _instance: Optional["ModelMonitor"] = None

    def __init__(self):
        self.drift_detector = FeatureDriftDetector()
        self.metrics_calc = ModelMetricsCalculator()
        self.total_analyses_monitored: int = 0
        self.total_records_scored: int = 0
        self.total_anomalies_flagged: int = 0
        self.history_scores: List[float] = []
        self.history_severities: List[str] = []
        self.history_latencies_ms: List[float] = []
        self.recent_drift_reports: List[Dict[str, Any]] = []

    @classmethod
    def get_instance(cls) -> "ModelMonitor":
        if cls._instance is None:
            cls._instance = ModelMonitor()
        return cls._instance

    def record_analysis_telemetry(
        self,
        df_records: pd.DataFrame,
        risk_scores: List[float],
        severities: List[str],
        duration_ms: float,
    ) -> Dict[str, Any]:
        """Record batch telemetry and run drift evaluation."""
        self.total_analyses_monitored += 1
        self.total_records_scored += len(df_records)
        flagged = sum(1 for s in risk_scores if s >= settings.model_threshold)
        self.total_anomalies_flagged += flagged

        self.history_scores.extend(risk_scores[-500:])  # keep bounded sliding window
        self.history_severities.extend(severities[-500:])
        self.history_latencies_ms.append(duration_ms)

        # Evaluate drift
        drift_report = self.drift_detector.assess_dataframe_drift(df_records)
        drift_report["timestamp"] = datetime.utcnow().isoformat()
        self.recent_drift_reports.append(drift_report)
        if len(self.recent_drift_reports) > 20:
            self.recent_drift_reports.pop(0)

        if drift_report["drift_detected"]:
            for warn in drift_report["drift_warnings"]:
                logger.warning(f"[MONITORING WARNING] {warn}")

        return drift_report

    def get_telemetry_metrics(self) -> Dict[str, Any]:
        """Return operational and accuracy metrics summary."""
        stats = self.metrics_calc.calculate_batch_metrics(
            risk_scores=self.history_scores[-1000:] if self.history_scores else [0.1],
            severities=self.history_severities[-1000:] if self.history_severities else ["LOW"],
            latencies_ms=self.history_latencies_ms[-100:] if self.history_latencies_ms else [10.0],
            threshold=settings.model_threshold,
        )

        return {
            "model_name": settings.model_name,
            "model_version": settings.ai_model_version,
            "model_threshold": settings.model_threshold,
            "feature_schema_version": settings.feature_schema_version,
            "rag_knowledge_version": settings.rag_knowledge_version,
            "llm_version": settings.llm_version,
            "total_analyses_monitored": self.total_analyses_monitored,
            "total_records_scored": self.total_records_scored,
            "total_anomalies_flagged": self.total_anomalies_flagged,
            "metrics": stats,
            "last_updated": datetime.utcnow().isoformat(),
        }

    def get_latest_drift_report(self) -> Dict[str, Any]:
        """Return latest drift evaluation."""
        if self.recent_drift_reports:
            return self.recent_drift_reports[-1]
        return {
            "drift_detected": False,
            "drift_severity": "STABLE",
            "monitored_features_count": 0,
            "drift_warnings": [],
            "feature_metrics": {},
            "status": "NO_LIVE_BATCHES_EVALUATED_YET",
        }
