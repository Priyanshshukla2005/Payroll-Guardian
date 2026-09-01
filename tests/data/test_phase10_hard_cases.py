"""Unit and evaluation tests for curated benchmark hard cases (Phase 10)."""

import pandas as pd
import pytest

from backend.dependencies.services import ModelManager
from backend.services.detection_service import DetectionService
from data.benchmarks.hard_cases import (
    get_curated_benchmark_cases,
    get_curated_benchmark_dataframe,
)


def test_curated_hard_cases_dataset_integrity():
    """Verify curated dataset contains both positive anomalies and negative control edge cases."""
    cases = get_curated_benchmark_cases()
    assert len(cases) >= 10

    anomalies = [c for c in cases if c["is_anomaly"]]
    legitimate = [c for c in cases if not c["is_anomaly"]]

    assert len(anomalies) >= 6
    assert len(legitimate) >= 4


def test_hybrid_detector_evaluation_on_hard_cases():
    """Evaluate precision, recall, and false positive rates on curated hard cases."""
    df_cases, true_labels = get_curated_benchmark_dataframe()

    model_mgr = ModelManager.get_instance()
    model_mgr.initialize()

    detection_service = DetectionService(model_mgr)
    detection_results = detection_service.detect_anomalies(df_cases, decision_threshold=0.45)

    predicted_anomalies = []
    for row, risk_score, anomaly_types, rule_violations, card in detection_results:
        is_flagged = (risk_score >= 0.45) or (len(rule_violations) > 0)
        predicted_anomalies.append(is_flagged)

    # Calculate metrics
    tp = sum(1 for p, t in zip(predicted_anomalies, true_labels) if p and t)
    fp = sum(1 for p, t in zip(predicted_anomalies, true_labels) if p and not t)
    fn = sum(1 for p, t in zip(predicted_anomalies, true_labels) if not p and t)
    tn = sum(1 for p, t in zip(predicted_anomalies, true_labels) if not p and not t)

    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    # True anomalies should have high recall
    assert recall >= 0.80, f"Expected recall >= 80%, got {recall:.2%}"
