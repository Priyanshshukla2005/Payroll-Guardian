"""Tests for anomaly injection engine, audit metadata, and feature engineering."""

import pandas as pd
import pytest
from backend.config.settings import get_settings
from ai.features.payroll_features import compute_payroll_features
from data_pipeline.injector import PayrollAnomalyInjector
from data_pipeline.generator import generate_synthetic_payroll_dataset


@pytest.fixture
def clean_baseline():
    """Fixture providing clean payroll dataset."""
    settings = get_settings()
    return generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=300,
        num_months=12,
        random_seed=42,
    )


def test_all_13_anomaly_types_generated(clean_baseline):
    """Verify that anomaly injector successfully generates all 13 anomaly types."""
    injector = PayrollAnomalyInjector(random_seed=42)
    df_anom, df_meta = injector.inject_all_anomalies(clean_baseline, anomaly_rate=0.10)

    generated_types = set(df_meta["anomaly_type"].unique())
    expected_types = set(PayrollAnomalyInjector.ANOMALY_TYPES)

    assert expected_types.issubset(generated_types)
    assert len(df_meta) > 0


def test_clean_dataset_remains_uncontaminated(clean_baseline):
    """Verify that anomaly injection does not mutate the clean input dataframe."""
    clean_copy = clean_baseline.copy(deep=True)
    injector = PayrollAnomalyInjector(random_seed=42)
    _, _ = injector.inject_all_anomalies(clean_baseline, anomaly_rate=0.10)

    pd.testing.assert_frame_equal(clean_baseline, clean_copy)


def test_anomaly_labels_and_metadata_consistency(clean_baseline):
    """Verify that is_anomaly is correctly set and metadata audit log is populated."""
    injector = PayrollAnomalyInjector(random_seed=42)
    df_anom, df_meta = injector.inject_all_anomalies(clean_baseline, anomaly_rate=0.08)

    # Check is_anomaly column
    assert "is_anomaly" in df_anom.columns
    assert "anomaly_type" in df_anom.columns
    assert set(df_anom["is_anomaly"].unique()).issubset({0, 1})

    # Total tagged anomaly rows (accounting for dropped rows in MISSING_PAYROLL_RECORD)
    anomaly_rows = df_anom[df_anom["is_anomaly"] == 1]
    assert len(anomaly_rows) > 0

    # Verify metadata fields
    expected_meta_cols = {
        "anomaly_id",
        "employee_id",
        "payroll_month",
        "anomaly_type",
        "severity",
        "original_value",
        "modified_value",
        "description",
    }
    assert expected_meta_cols.issubset(df_meta.columns)
    assert (df_meta["anomaly_id"].str.startswith("ANOM_")).all()


def test_feature_engineering_pipeline(clean_baseline):
    """Verify feature calculation pipeline runs and produces expected derived columns."""
    injector = PayrollAnomalyInjector(random_seed=42)
    df_anom, _ = injector.inject_all_anomalies(clean_baseline, anomaly_rate=0.05)

    df_feats = compute_payroll_features(df_anom)

    expected_features = [
        "attendance_ratio",
        "leave_ratio",
        "overtime_per_present_day",
        "deduction_to_gross_ratio",
        "net_to_gross_ratio",
        "basic_to_gross_ratio",
        "salary_change_percentage",
        "overtime_change_percentage",
        "bonus_change_percentage",
        "deduction_change_percentage",
        "net_salary_change_percentage",
        "historical_salary_mean",
        "historical_salary_std",
        "salary_zscore_vs_history",
        "historical_overtime_mean",
        "historical_overtime_std",
        "overtime_zscore_vs_history",
        "dept_month_gross_mean",
        "gross_vs_dept_ratio",
        "desig_month_gross_mean",
        "gross_vs_desig_ratio",
    ]

    for feat in expected_features:
        assert feat in df_feats.columns, f"Missing expected feature: {feat}"
        assert not df_feats[feat].isna().all(), f"Feature {feat} is completely NaN"
