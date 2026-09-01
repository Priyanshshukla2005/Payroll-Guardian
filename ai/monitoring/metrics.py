"""Model performance, latency, and distribution metrics calculations (Phase 10)."""

from typing import Any, Dict, List, Optional
import numpy as np


class ModelMetricsCalculator:
    """Calculates operational and statistical metrics across anomaly detection inference batches."""

    @staticmethod
    def calculate_batch_metrics(
        risk_scores: List[float],
        severities: List[str],
        latencies_ms: Optional[List[float]] = None,
        threshold: float = 0.45,
    ) -> Dict[str, Any]:
        """Compute statistical summary for a batch of predictions."""
        if not risk_scores:
            return {
                "total_predictions": 0,
                "anomalies_detected": 0,
                "anomaly_rate": 0.0,
                "severity_counts": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
                "score_distribution": {
                    "mean": 0.0,
                    "median": 0.0,
                    "p90": 0.0,
                    "p99": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                },
                "latency_stats": {"mean_ms": 0.0, "p95_ms": 0.0},
            }

        scores_arr = np.array(risk_scores, dtype=float)
        anomalies_flagged = int(np.sum(scores_arr >= threshold))
        anomaly_rate = float(anomalies_flagged / len(scores_arr))

        sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for s in severities:
            s_up = s.upper()
            if s_up in sev_counts:
                sev_counts[s_up] += 1

        latency_dict = {"mean_ms": 0.0, "p95_ms": 0.0}
        if latencies_ms:
            lat_arr = np.array(latencies_ms, dtype=float)
            latency_dict["mean_ms"] = float(np.mean(lat_arr))
            latency_dict["p95_ms"] = float(np.percentile(lat_arr, 95))

        return {
            "total_predictions": len(scores_arr),
            "anomalies_detected": anomalies_flagged,
            "anomaly_rate": round(anomaly_rate, 4),
            "severity_counts": sev_counts,
            "score_distribution": {
                "mean": round(float(np.mean(scores_arr)), 4),
                "median": round(float(np.median(scores_arr)), 4),
                "p90": round(float(np.percentile(scores_arr, 90)), 4),
                "p99": round(float(np.percentile(scores_arr, 99)), 4),
                "min": round(float(np.min(scores_arr)), 4),
                "max": round(float(np.max(scores_arr)), 4),
            },
            "latency_stats": latency_dict,
        }
