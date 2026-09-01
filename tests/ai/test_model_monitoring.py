"""Unit tests for ML Drift Detector and Metrics Calculator (Phase 10)."""

import numpy as np
import pandas as pd
import pytest

from ai.monitoring.drift_detector import FeatureDriftDetector
from ai.monitoring.metrics import ModelMetricsCalculator


def test_metrics_calculator():
    """Verify batch metrics computation."""
    scores = [0.1, 0.2, 0.8, 0.9, 0.5]
    sevs = ["LOW", "LOW", "CRITICAL", "CRITICAL", "MEDIUM"]
    lats = [12.0, 15.0, 14.0, 18.0, 20.0]

    metrics = ModelMetricsCalculator.calculate_batch_metrics(scores, sevs, lats, threshold=0.45)
    assert metrics["total_predictions"] == 5
    assert metrics["anomalies_detected"] == 3
    assert metrics["anomaly_rate"] == 0.6
    assert metrics["severity_counts"]["CRITICAL"] == 2
    assert metrics["severity_counts"]["LOW"] == 2
    assert metrics["score_distribution"]["max"] == 0.9
    assert metrics["latency_stats"]["mean_ms"] == 15.8


def test_drift_detector_stable_distribution():
    """Verify no drift flagged on standard reference distribution."""
    detector = FeatureDriftDetector()
    np.random.seed(42)
    df_normal = pd.DataFrame({
        "basic_salary": np.random.normal(55000.0, 10000.0, 50),
        "gross_salary": np.random.normal(75000.0, 15000.0, 50),
        "net_salary": np.random.normal(67000.0, 12000.0, 50),
        "pf_deduction": np.random.normal(6600.0, 1200.0, 50),
        "overtime_hours": np.random.normal(4.0, 2.0, 50),
    })
    report = detector.assess_dataframe_drift(df_normal)
    assert isinstance(report, dict)
    assert "drift_detected" in report
    assert report["drift_severity"] == "STABLE"
    assert len(report["feature_metrics"]) >= 3


def test_drift_detector_moderate_shift_warning():
    """Verify moderate distribution shift flags WARNING drift severity."""
    detector = FeatureDriftDetector()
    np.random.seed(42)
    # Shift basic_salary mean from 55,000 to ~72,000 (+31% shift -> warning threshold >= 25%)
    df_moderate = pd.DataFrame({
        "basic_salary": np.random.normal(72000.0, 10000.0, 50),
        "gross_salary": np.random.normal(75000.0, 15000.0, 50),
        "net_salary": np.random.normal(67000.0, 12000.0, 50),
        "pf_deduction": np.random.normal(6600.0, 1200.0, 50),
        "overtime_hours": np.random.normal(4.0, 2.0, 50),
    })
    report = detector.assess_dataframe_drift(df_moderate)
    assert report["drift_detected"] is True
    assert report["drift_severity"] == "WARNING"
    assert len(report["drift_warnings"]) >= 1


def test_drift_detector_severe_drift():
    """Verify severe distribution shift flags SEVERE drift severity."""
    detector = FeatureDriftDetector()
    df_shifted = pd.DataFrame({
        "basic_salary": [350000.0] * 50,  # Huge shift vs 55,000 baseline (>500%)
        "gross_salary": [450000.0] * 50,
        "net_salary": [400000.0] * 50,
        "pf_deduction": [42000.0] * 50,
        "overtime_hours": [65.0] * 50,
    })
    report = detector.assess_dataframe_drift(df_shifted)
    assert report["drift_detected"] is True
    assert report["drift_severity"] == "SEVERE"
    assert len(report["drift_warnings"]) >= 1
