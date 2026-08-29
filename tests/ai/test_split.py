"""Tests for temporal and unseen-employee dataset splitting."""

import pandas as pd
import pytest
from backend.config.settings import get_settings
from ai.features.splitter import (
    separate_features_labels_metadata,
    temporal_train_val_test_split,
    unseen_employee_split,
)
from data_pipeline.generator import generate_synthetic_payroll_dataset


@pytest.fixture
def multi_month_data():
    """Fixture providing 12-month payroll dataset."""
    settings = get_settings()
    return generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=100,
        num_months=12,
        random_seed=42,
    )


def test_temporal_split_chronological_ordering(multi_month_data):
    """Verify that temporal splits partition time sequentially without overlap."""
    train_df, val_df, test_df, summary = temporal_train_val_test_split(
        multi_month_data,
        train_ratio=0.67,
        val_ratio=0.165,
        test_ratio=0.165,
    )

    train_months = set(train_df["payroll_month"].unique())
    val_months = set(val_df["payroll_month"].unique())
    test_months = set(test_df["payroll_month"].unique())

    # Ensure mutually exclusive months
    assert train_months.isdisjoint(val_months)
    assert val_months.isdisjoint(test_months)
    assert train_months.isdisjoint(test_months)

    # Ensure chronological order: max(train) < min(val) and max(val) < min(test)
    assert max(train_months) < min(val_months)
    assert max(val_months) < min(test_months)

    # Total record check
    assert len(train_df) + len(val_df) + len(test_df) == len(multi_month_data)


def test_unseen_employee_split_disjointness(multi_month_data):
    """Verify that unseen-employee holdout has zero employee ID overlap with seen data."""
    seen_df, unseen_df, meta = unseen_employee_split(multi_month_data, holdout_ratio=0.10, random_seed=42)

    seen_ids = set(seen_df["employee_id"].unique())
    unseen_ids = set(unseen_df["employee_id"].unique())

    assert seen_ids.isdisjoint(unseen_ids)
    assert len(unseen_ids) == int(len(seen_ids | unseen_ids) * 0.10)
    assert len(seen_df) + len(unseen_df) == len(multi_month_data)
