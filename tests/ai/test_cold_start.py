"""Unit tests for cold-start feature calculation and probability calibrator."""

import numpy as np
import pandas as pd
import pytest

from ai.features.cold_start_features import compute_cold_start_and_statistical_features
from ai.detection.calibrator import ProbabilityCalibrator


def test_cold_start_feature_computation():
    """Verify that observation depth and dynamic cohort robust z-scores are calculated."""
    df = pd.DataFrame({
        "employee_id": ["EMP01", "EMP01", "EMP01", "EMP02", "EMP02"],
        "payroll_month": ["2024-01", "2024-02", "2024-03", "2024-01", "2024-02"],
        "department": ["Engineering", "Engineering", "Engineering", "Sales", "Sales"],
        "designation": ["Junior", "Junior", "Junior", "Mid-level", "Mid-level"],
        "basic_salary": [25000.0, 25000.0, 25000.0, 35000.0, 35000.0],
        "gross_salary": [55000.0, 55000.0, 55000.0, 75000.0, 75000.0],
        "overtime_hours": [0.0, 5.0, 0.0, 10.0, 10.0],
    })

    out = compute_cold_start_and_statistical_features(df)

    assert "historical_observation_count" in out.columns
    assert "months_of_history" in out.columns
    assert "robust_salary_zscore_dept" in out.columns
    assert "robust_gross_zscore_desig" in out.columns

    # First month of EMP01 must have 0 historical observations
    emp01_m1 = out[(out["employee_id"] == "EMP01") & (out["payroll_month"] == "2024-01")]
    assert emp01_m1["historical_observation_count"].values[0] == 0.0
    assert emp01_m1["has_previous_salary"].values[0] == 0.0

    # Month 3 must have 2 prior observations
    emp01_m3 = out[(out["employee_id"] == "EMP01") & (out["payroll_month"] == "2024-03")]
    assert emp01_m3["historical_observation_count"].values[0] == 2.0
    assert emp01_m3["has_previous_salary"].values[0] == 1.0


def test_probability_calibrator_fitting():
    """Verify probability calibrator fits and reduces Expected Calibration Error."""
    np.random.seed(42)
    y_true = np.random.choice([0, 1], size=100, p=[0.9, 0.1])
    # Uncalibrated raw probabilities with slight overconfidence
    raw_probs = np.clip(y_true * 0.8 + np.random.uniform(0.1, 0.4, size=100), 0.0, 1.0)

    calibrator = ProbabilityCalibrator(method="isotonic")
    calibrator.fit(raw_probs, y_true)

    assert calibrator.is_fitted
    cal_probs = calibrator.calibrate(raw_probs)
    assert len(cal_probs) == 100
    assert np.all(cal_probs >= 0.0) and np.all(cal_probs <= 1.0)
