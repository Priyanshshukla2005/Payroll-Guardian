"""Tests for data validation and reconciliation logic."""

import pandas as pd
import pytest
from backend.config.settings import get_settings
from data_pipeline.cleaner import validate_payroll_dataset, validate_payroll_dataset_stream
from data_pipeline.generator import generate_synthetic_payroll_chunks, generate_synthetic_payroll_dataset


@pytest.fixture
def clean_sample_df():
    """Fixture providing clean sample payroll dataframe."""
    settings = get_settings()
    return generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=100,
        num_months=6,
        random_seed=42,
    )


def test_clean_dataset_validation_passes(clean_sample_df):
    """Verify that clean generated dataset passes all validation rules with 0 violations."""
    report = validate_payroll_dataset(clean_sample_df)
    assert report.is_valid is True
    assert report.violation_count == 0
    assert len(report.violations) == 0


def test_streaming_validation_passes():
    """Verify that streaming validation works across multiple chunks."""
    settings = get_settings()
    chunks = generate_synthetic_payroll_chunks(
        settings=settings,
        num_employees=150,
        num_months=6,
        chunk_size_employees=50,
        random_seed=42,
    )
    report = validate_payroll_dataset_stream(chunks)
    assert report.is_valid is True
    assert report.total_records == 150 * 6
    assert report.violation_count == 0


def test_attendance_bounds_violation_detection(clean_sample_df):
    """Verify detection of impossible attendance (present > working days)."""
    corrupted_df = clean_sample_df.copy()
    corrupted_df.at[0, "present_days"] = 35  # impossible in 26-day month
    report = validate_payroll_dataset(corrupted_df)

    assert report.is_valid is False
    rule_names = [v.rule_name for v in report.violations]
    assert "ATTENDANCE_BOUNDS_VALID" in rule_names


def test_gross_salary_reconciliation_violation(clean_sample_df):
    """Verify detection of corrupted gross salary."""
    corrupted_df = clean_sample_df.copy()
    corrupted_df.at[5, "gross_salary"] += 50000.0  # discrepancy
    report = validate_payroll_dataset(corrupted_df)

    assert report.is_valid is False
    rule_names = [v.rule_name for v in report.violations]
    assert "GROSS_SALARY_RECONCILIATION" in rule_names


def test_deductions_reconciliation_violation(clean_sample_df):
    """Verify detection of corrupted total deductions."""
    corrupted_df = clean_sample_df.copy()
    corrupted_df.at[10, "total_deductions"] += 10000.0
    report = validate_payroll_dataset(corrupted_df)

    assert report.is_valid is False
    rule_names = [v.rule_name for v in report.violations]
    assert "DEDUCTIONS_RECONCILIATION" in rule_names


def test_net_salary_reconciliation_violation(clean_sample_df):
    """Verify detection of net salary mismatch."""
    corrupted_df = clean_sample_df.copy()
    corrupted_df.at[15, "net_salary"] -= 5000.0
    report = validate_payroll_dataset(corrupted_df)

    assert report.is_valid is False
    rule_names = [v.rule_name for v in report.violations]
    assert "NET_SALARY_RECONCILIATION" in rule_names


def test_duplicate_record_detection(clean_sample_df):
    """Verify detection of duplicate employee-month records."""
    corrupted_df = pd.concat([clean_sample_df, clean_sample_df.iloc[0:1]], ignore_index=True)
    report = validate_payroll_dataset(corrupted_df)

    assert report.is_valid is False
    rule_names = [v.rule_name for v in report.violations]
    assert "NO_DUPLICATE_EMPLOYEE_MONTH" in rule_names
