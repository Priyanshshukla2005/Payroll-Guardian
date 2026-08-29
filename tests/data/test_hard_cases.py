"""Unit tests for Phase 4 hard-case generation and challenge scenario evaluations."""

import pandas as pd
import pytest

from backend.config.settings import get_settings
from data_pipeline.company_shift import generate_shifted_company_dataset
from data_pipeline.hard_cases import HardCaseGenerator


def test_hard_case_generator_scenarios():
    """Verify that HardCaseGenerator creates all challenge categories."""
    generator = HardCaseGenerator(random_seed=42)
    hard_df, audit_df = generator.generate_hard_case_suite(num_employees=100, num_months=6)

    assert len(hard_df) > 0
    assert len(audit_df) > 0

    expected_categories = {
        "NORMAL_BASELINE",
        "SUBTLE_STATUTORY",
        "COLD_START",
        "LEGITIMATE_LARGE_BONUS",
        "COMPOUND_ANOMALY",
        "CAMOUFLAGED_ADVERSARIAL",
    }
    actual_categories = set(hard_df["challenge_category"].unique())
    assert expected_categories.issubset(actual_categories)

    # Verify subtle PF magnitudes
    subtle_pf_records = hard_df[hard_df["anomaly_type"] == "SUBTLE_PF_MISMATCH"]
    assert len(subtle_pf_records) > 0
    assert (subtle_pf_records["is_anomaly"] == 1).all()


def test_company_shift_generator():
    """Verify that company shift dataset generates valid shifted payroll structure."""
    df_shift, meta_shift = generate_shifted_company_dataset(num_employees=50, num_months=4, random_seed=99)

    assert len(df_shift) > 0
    assert len(meta_shift) > 0
    assert "basic_salary" in df_shift.columns
    assert "gross_salary" in df_shift.columns
    assert (df_shift["gross_salary"] > 0).all()
