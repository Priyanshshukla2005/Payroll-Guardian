"""Unit tests for Phase 3 evaluation metrics, threshold sweeper, and unique-employee FP/1k."""

import numpy as np
import pandas as pd
import pytest

from ai.training.evaluator import (
    compute_unique_employee_fp_per_1000,
    evaluate_binary_model,
    sweep_thresholds,
)


def test_unique_employee_fp_per_1000_calculation():
    """Verify unique-employee FP per 1,000 employees formula."""
    # 10 employees, 2 records each = 20 records
    emp_ids = [f"EMP{i:02d}" for i in range(10) for _ in range(2)]
    y_true = np.zeros(20, dtype=int)
    y_pred = np.zeros(20, dtype=int)

    # Make EMP00 have 2 false alarms, EMP01 have 1 false alarm -> 2 unique false positive employees
    y_pred[0] = 1
    y_pred[1] = 1
    y_pred[2] = 1

    u_count, u_rate = compute_unique_employee_fp_per_1000(y_true, y_pred, emp_ids)

    # 2 unique employees out of 10 = 200 per 1,000
    assert u_count == 2
    assert u_rate == 200.0


def test_evaluate_binary_model_metrics():
    """Verify evaluation metric structure and score ranges."""
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y_proba = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])
    emp_ids = [f"EMP{i}" for i in range(8)]

    report = evaluate_binary_model(
        model_name="TestModel",
        y_true=y_true,
        y_proba=y_proba,
        threshold=0.5,
        employee_ids=emp_ids,
    )

    assert report.total_records == 8
    assert report.true_positives == 4
    assert report.false_positives == 0
    assert report.true_negatives == 4
    assert report.false_negatives == 0
    assert report.precision == 1.0
    assert report.recall == 1.0
    assert report.f1_score == 1.0
    assert report.roc_auc == 1.0
    assert report.unique_employee_fp_count == 0


def test_sweep_thresholds():
    """Verify threshold sweep produces results for all thresholds."""
    y_true = np.array([0, 0, 1, 1])
    y_proba = np.array([0.2, 0.4, 0.6, 0.8])
    sweep_df = sweep_thresholds(y_true, y_proba, thresholds=[0.3, 0.5, 0.7])

    assert len(sweep_df) == 3
    assert "precision" in sweep_df.columns
    assert "recall" in sweep_df.columns
    assert "f1_score" in sweep_df.columns
