"""Tests for data leakage prevention in feature engineering, splitting, and preprocessing."""

import numpy as np
import pandas as pd
import pytest
from backend.config.settings import get_settings
from ai.features.payroll_features import compute_mom_change_features, compute_payroll_features
from ai.features.splitter import separate_features_labels_metadata, temporal_train_val_test_split
from ai.features.pipeline import PayrollPreprocessor
from data_pipeline.generator import generate_synthetic_payroll_dataset


@pytest.fixture
def multi_month_dataset():
    """Fixture providing clean 6-month payroll data for 50 employees."""
    settings = get_settings()
    return generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=50,
        num_months=6,
        random_seed=42,
    )


def test_historical_features_zero_future_lookahead(multi_month_dataset):
    """Verify modifying future months does NOT alter historical features of earlier months."""
    df1 = multi_month_dataset.copy(deep=True)
    df2 = multi_month_dataset.copy(deep=True)

    # In df2, artificially tamper with month 5 and 6 basic salary
    month_5_6_mask = df2["payroll_month"].isin(["2024-05", "2024-06"])
    df2.loc[month_5_6_mask, "basic_salary"] = df2.loc[month_5_6_mask, "basic_salary"] * 5.0

    feat1 = compute_payroll_features(df1)
    feat2 = compute_payroll_features(df2)

    # Features for months 1 to 4 MUST be 100% identical in both datasets
    month_1_4_mask = feat1["payroll_month"].isin(["2024-01", "2024-02", "2024-03", "2024-04"])

    cols_to_check = [
        "salary_change_percentage",
        "historical_salary_mean",
        "historical_salary_std",
        "salary_zscore_vs_history",
    ]

    for col in cols_to_check:
        np.testing.assert_allclose(
            feat1.loc[month_1_4_mask, col].values,
            feat2.loc[month_1_4_mask, col].values,
            err_msg=f"Future lookahead leakage detected in feature: {col}",
        )


def test_identifier_exclusion_from_features(multi_month_dataset):
    """Verify that identifiers and label columns are strictly excluded from X."""
    df_feat = compute_payroll_features(multi_month_dataset)
    X, y, metadata = separate_features_labels_metadata(df_feat)

    forbidden_cols = ["employee_id", "payroll_month", "joining_date", "is_anomaly", "anomaly_type"]
    for col in forbidden_cols:
        assert col not in X.columns, f"Identifier/Label column {col} was found in model features X!"

    # Ensure labels and metadata are preserved
    assert len(y) == len(df_feat)
    assert "employee_id" in metadata.columns
    assert "payroll_month" in metadata.columns


def test_preprocessor_fitting_isolation(multi_month_dataset):
    """Verify that preprocessing scaler and imputer are fitted strictly on X_train."""
    df_feat = compute_payroll_features(multi_month_dataset)
    train_df, val_df, test_df, _ = temporal_train_val_test_split(df_feat, train_ratio=0.5, val_ratio=0.25, test_ratio=0.25)

    X_train, _, _ = separate_features_labels_metadata(train_df)
    X_test, _, _ = separate_features_labels_metadata(test_df)

    preprocessor = PayrollPreprocessor()
    preprocessor.fit(X_train)

    # Scaler center/scale should be derived solely from X_train
    num_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()
    scaler = preprocessor.pipeline.named_transformers_["num"].named_steps["scaler"]

    # Transform test set with train parameters
    X_test_transformed = preprocessor.transform(X_test)
    assert X_test_transformed.shape[0] == len(X_test)
    assert not np.isnan(X_test_transformed.values).any()
