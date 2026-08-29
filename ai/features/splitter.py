"""Dataset splitting module for temporal and population-based partitioning.

Implements chronological (temporal) train/val/test splits, unseen-employee
holdout evaluations, and feature/label/metadata segregation.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


IDENTIFIER_COLUMNS = ["employee_id", "payroll_month", "joining_date"]
LABEL_COLUMNS = ["is_anomaly", "anomaly_type"]


class SplitMetadata(BaseModel):
    """Metadata summary of a split partition."""

    split_name: str
    total_records: int
    unique_employees: int
    months: List[str]
    normal_count: int
    anomaly_count: int
    anomaly_rate: float


class DatasetSplitResult(BaseModel):
    """Container for complete train, validation, and test partitions."""

    train_metadata: SplitMetadata
    val_metadata: SplitMetadata
    test_metadata: SplitMetadata
    unseen_metadata: Optional[SplitMetadata] = None


def separate_features_labels_metadata(
    df: pd.DataFrame,
    exclude_identifiers: bool = True,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Segregate feature matrix X, target label y, and tracking metadata.

    Args:
        df: Feature-engineered DataFrame.
        exclude_identifiers: Whether to strictly strip employee IDs and month strings from X.

    Returns:
        Tuple of:
        - X: Feature DataFrame (numerical and categorical model features only)
        - y: Target label Series (is_anomaly)
        - metadata: Tracking DataFrame (employee_id, payroll_month, is_anomaly, anomaly_type)
    """
    # Metadata columns to extract
    meta_cols = [col for col in IDENTIFIER_COLUMNS + LABEL_COLUMNS if col in df.columns]
    metadata = df[meta_cols].copy()

    # Target label y
    y = df["is_anomaly"].copy() if "is_anomaly" in df.columns else pd.Series(0, index=df.index)

    # Features X
    cols_to_drop = LABEL_COLUMNS.copy()
    if exclude_identifiers:
        cols_to_drop.extend(IDENTIFIER_COLUMNS)

    drop_existing = [c for c in cols_to_drop if c in df.columns]
    X = df.drop(columns=drop_existing).copy()

    return X, y, metadata


def temporal_train_val_test_split(
    df: pd.DataFrame,
    train_ratio: float = 0.67,
    val_ratio: float = 0.165,
    test_ratio: float = 0.165,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, DatasetSplitResult]:
    """Chronologically partition payroll history into train, validation, and test sets.

    Ensures zero future lookahead: model trains strictly on earlier months,
    validates on intermediate months, and tests on the latest historical months.

    Args:
        df: Input DataFrame with 'payroll_month' column.
        train_ratio: Fraction of timeline for training (e.g., 0.67).
        val_ratio: Fraction of timeline for validation (e.g., 0.165).
        test_ratio: Fraction of timeline for final holdout testing (e.g., 0.165).

    Returns:
        Tuple of (train_df, val_df, test_df, split_summary).
    """
    if "payroll_month" not in df.columns:
        raise ValueError("Cannot perform temporal split: 'payroll_month' column missing.")

    unique_months = sorted(df["payroll_month"].unique().tolist())
    n_months = len(unique_months)

    if n_months < 3:
        raise ValueError(f"Temporal split requires at least 3 distinct months; found {n_months}.")

    n_train_months = max(int(np.floor(n_months * train_ratio)), 1)
    n_val_months = max(int(np.floor(n_months * val_ratio)), 1)
    # Remaining months go to test
    n_test_months = n_months - n_train_months - n_val_months
    if n_test_months < 1:
        n_test_months = 1
        n_train_months = n_months - n_val_months - n_test_months

    train_months = unique_months[:n_train_months]
    val_months = unique_months[n_train_months : n_train_months + n_val_months]
    test_months = unique_months[n_train_months + n_val_months :]

    train_df = df[df["payroll_month"].isin(train_months)].copy().reset_index(drop=True)
    val_df = df[df["payroll_month"].isin(val_months)].copy().reset_index(drop=True)
    test_df = df[df["payroll_month"].isin(test_months)].copy().reset_index(drop=True)

    def _summarize_split(split_df: pd.DataFrame, name: str, months: List[str]) -> SplitMetadata:
        total = len(split_df)
        n_anom = int((split_df["is_anomaly"] == 1).sum()) if "is_anomaly" in split_df.columns else 0
        n_norm = total - n_anom
        rate = (n_anom / total) if total > 0 else 0.0
        n_emps = split_df["employee_id"].nunique() if "employee_id" in split_df.columns else 0
        return SplitMetadata(
            split_name=name,
            total_records=total,
            unique_employees=n_emps,
            months=months,
            normal_count=n_norm,
            anomaly_count=n_anom,
            anomaly_rate=round(rate, 4),
        )

    summary = DatasetSplitResult(
        train_metadata=_summarize_split(train_df, "Train", train_months),
        val_metadata=_summarize_split(val_df, "Validation", val_months),
        test_metadata=_summarize_split(test_df, "Test", test_months),
    )

    return train_df, val_df, test_df, summary


def unseen_employee_split(
    df: pd.DataFrame,
    holdout_ratio: float = 0.10,
    random_seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, SplitMetadata]:
    """Partition dataset into known employees and completely unseen held-out employees.

    Useful for evaluating zero-shot employee generalization without historical employee IDs.

    Args:
        df: Input DataFrame.
        holdout_ratio: Proportion of unique employees to hold out (e.g. 0.10).
        random_seed: Random seed for employee ID selection.

    Returns:
        Tuple of (seen_df, unseen_df, unseen_metadata).
    """
    if "employee_id" not in df.columns:
        raise ValueError("Cannot perform employee split: 'employee_id' column missing.")

    rng = np.random.default_rng(random_seed)
    all_emp_ids = np.array(df["employee_id"].unique())
    n_holdout = max(int(len(all_emp_ids) * holdout_ratio), 1)

    holdout_emp_ids = set(rng.choice(all_emp_ids, size=n_holdout, replace=False))

    unseen_mask = df["employee_id"].isin(holdout_emp_ids)
    unseen_df = df[unseen_mask].copy().reset_index(drop=True)
    seen_df = df[~unseen_mask].copy().reset_index(drop=True)

    n_anom = int((unseen_df["is_anomaly"] == 1).sum()) if "is_anomaly" in unseen_df.columns else 0
    total = len(unseen_df)
    meta = SplitMetadata(
        split_name="Unseen_Employees",
        total_records=total,
        unique_employees=len(holdout_emp_ids),
        months=sorted(unseen_df["payroll_month"].unique().tolist()) if "payroll_month" in unseen_df.columns else [],
        normal_count=total - n_anom,
        anomaly_count=n_anom,
        anomaly_rate=round(n_anom / total, 4) if total > 0 else 0.0,
    )

    return seen_df, unseen_df, meta
