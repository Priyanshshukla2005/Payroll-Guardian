"""Tests for deterministic baseline anomaly detector and evaluation reporting."""

import numpy as np
import pandas as pd
import pytest
from backend.config.settings import get_settings
from ai.features.payroll_features import compute_payroll_features
from ai.detection.baseline_rules import DeterministicBaselineDetector
from data_pipeline.injector import PayrollAnomalyInjector
from data_pipeline.generator import generate_synthetic_payroll_dataset


@pytest.fixture
def anomalous_dataset():
    """Fixture providing clean and injected anomalous dataset."""
    settings = get_settings()
    df_clean = generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=200,
        num_months=6,
        random_seed=42,
    )
    injector = PayrollAnomalyInjector(random_seed=42)
    df_anom, _ = injector.inject_all_anomalies(df_clean, anomaly_rate=0.08)
    return compute_payroll_features(df_anom)


def test_deterministic_baseline_detector_predictions(anomalous_dataset):
    """Verify that baseline detector makes valid binary predictions."""
    detector = DeterministicBaselineDetector()
    preds = detector.predict(anomalous_dataset)

    assert len(preds) == len(anomalous_dataset)
    assert set(np.unique(preds)).issubset({0, 1})
    assert np.sum(preds == 1) > 0  # Should detect anomalies


def test_baseline_evaluation_metrics_reporting(anomalous_dataset):
    """Verify that baseline evaluate produces valid evaluation report."""
    detector = DeterministicBaselineDetector()
    report = detector.evaluate(anomalous_dataset)

    assert report.total_samples == len(anomalous_dataset)
    assert 0.0 <= report.precision <= 1.0
    assert 0.0 <= report.recall <= 1.0
    assert 0.0 <= report.f1_score <= 1.0
    assert report.recall > 0.85  # High recall expected for deterministic rules

    # Verify per-type metric entries
    assert len(report.per_type_metrics) == len(DeterministicBaselineDetector.RULE_NAMES)
