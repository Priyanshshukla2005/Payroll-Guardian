"""Feature engineering module for payroll anomaly detection and ML model preparation.

Calculates month-over-month (MoM) deltas, financial & attendance ratios,
historical rolling window statistics per employee, and peer-group benchmarks.
Supports in-memory processing and out-of-core streaming execution.
"""

from pathlib import Path
from typing import Generator, List, Optional, Union
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def compute_ratio_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute intra-record payroll and attendance ratio features."""
    res = df.copy()
    eps = 1e-6

    # Attendance ratios
    if "working_days" in res.columns:
        wd = res["working_days"].replace(0, np.nan)
        if "present_days" in res.columns:
            res["attendance_ratio"] = (res["present_days"] / wd).fillna(0.0).clip(0, 5.0)
        if "leave_days" in res.columns:
            res["leave_ratio"] = (res["leave_days"] / wd).fillna(0.0).clip(0, 5.0)

    # Overtime intensity
    if "overtime_hours" in res.columns and "present_days" in res.columns:
        res["overtime_per_present_day"] = (
            res["overtime_hours"] / np.maximum(res["present_days"], 1.0)
        ).fillna(0.0)

    # Financial component ratios
    if "gross_salary" in res.columns:
        gross_safe = np.maximum(res["gross_salary"], eps)

        if "total_deductions" in res.columns:
            res["deduction_to_gross_ratio"] = (res["total_deductions"] / gross_safe).fillna(0.0)

        if "net_salary" in res.columns:
            res["net_to_gross_ratio"] = (res["net_salary"] / gross_safe).fillna(0.0)

        if "basic_salary" in res.columns:
            res["basic_to_gross_ratio"] = (res["basic_salary"] / gross_safe).fillna(0.0)

        if "esi" in res.columns:
            res["esi_to_gross_ratio"] = (res["esi"] / gross_safe).fillna(0.0)

    if "basic_salary" in res.columns:
        basic_safe = np.maximum(res["basic_salary"], eps)

        if "allowances" in res.columns:
            res["allowance_to_basic_ratio"] = (res["allowances"] / basic_safe).fillna(0.0)

        if "pf" in res.columns:
            res["pf_to_basic_ratio"] = (res["pf"] / basic_safe).fillna(0.0)

    return res


def compute_mom_change_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Month-over-Month (MoM) percentage and absolute changes per employee."""
    res = df.copy()
    if "employee_id" not in res.columns or "payroll_month" not in res.columns:
        return res

    res = res.sort_values(by=["employee_id", "payroll_month"]).reset_index(drop=True)
    grouped = res.groupby("employee_id")

    shift_cols = {
        "basic_salary": "salary_change_percentage",
        "gross_salary": "gross_salary_change_percentage",
        "overtime_hours": "overtime_change_percentage",
        "bonus": "bonus_change_percentage",
        "total_deductions": "deduction_change_percentage",
        "net_salary": "net_salary_change_percentage",
    }

    for src_col, target_col in shift_cols.items():
        if src_col in res.columns:
            prev_val = grouped[src_col].shift(1)
            pct_change = ((res[src_col] - prev_val) / np.maximum(prev_val.abs(), 1.0)) * 100.0
            res[target_col] = pct_change.fillna(0.0)
            res[f"prev_{src_col}"] = prev_val.fillna(res[src_col])

    if "present_days" in res.columns:
        prev_present = grouped["present_days"].shift(1)
        res["present_days_change"] = (res["present_days"] - prev_present).fillna(0.0)

    return res


def compute_historical_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute historical cumulative statistics (mean, std, z-scores) per employee."""
    res = df.copy()
    if "employee_id" not in res.columns or "payroll_month" not in res.columns:
        return res

    res = res.sort_values(by=["employee_id", "payroll_month"]).reset_index(drop=True)
    tracked_cols = ["basic_salary", "gross_salary", "overtime_hours", "total_deductions"]

    for col in tracked_cols:
        if col not in res.columns:
            continue

        exp_mean = res.groupby("employee_id")[col].transform(
            lambda s: s.shift(1).expanding(min_periods=1).mean()
        )
        exp_std = res.groupby("employee_id")[col].transform(
            lambda s: s.shift(1).expanding(min_periods=2).std()
        )

        prefix = "salary" if col == "basic_salary" else col.replace("_hours", "").replace("_salary", "")

        res[f"historical_{prefix}_mean"] = exp_mean.fillna(res[col])
        res[f"historical_{prefix}_std"] = exp_std.fillna(0.0)

        std_safe = np.maximum(res[f"historical_{prefix}_std"], 1.0)
        res[f"{prefix}_zscore_vs_history"] = (
            (res[col] - res[f"historical_{prefix}_mean"]) / std_safe
        ).fillna(0.0)

    return res


def compute_peer_group_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute peer-group comparisons (department & designation benchmarks for the same month)."""
    res = df.copy()
    eps = 1e-6

    if "payroll_month" not in res.columns or "gross_salary" not in res.columns:
        return res

    if "department" in res.columns:
        dept_grp = res.groupby(["payroll_month", "department"])["gross_salary"]
        res["dept_month_gross_mean"] = dept_grp.transform("mean")
        res["dept_month_gross_std"] = dept_grp.transform("std").fillna(0.0)
        res["gross_vs_dept_ratio"] = (
            res["gross_salary"] / np.maximum(res["dept_month_gross_mean"], eps)
        ).fillna(1.0)

    if "designation" in res.columns:
        desig_grp = res.groupby(["payroll_month", "designation"])["gross_salary"]
        res["desig_month_gross_mean"] = desig_grp.transform("mean")
        res["desig_month_gross_std"] = desig_grp.transform("std").fillna(0.0)
        res["gross_vs_desig_ratio"] = (
            res["gross_salary"] / np.maximum(res["desig_month_gross_mean"], eps)
        ).fillna(1.0)

        if "overtime_hours" in res.columns:
            ot_grp = res.groupby(["payroll_month", "designation"])["overtime_hours"]
            res["desig_month_overtime_mean"] = ot_grp.transform("mean").fillna(0.0)
            res["desig_month_overtime_std"] = ot_grp.transform("std").fillna(0.0)

    return res


def compute_payroll_features(df: pd.DataFrame) -> pd.DataFrame:
    """Master pipeline to calculate all derived and engineered features for ML."""
    df_feat = compute_ratio_features(df)
    df_feat = compute_mom_change_features(df_feat)
    df_feat = compute_historical_rolling_features(df_feat)
    df_feat = compute_peer_group_features(df_feat)
    return df_feat


def compute_payroll_features_stream(
    chunks: Generator[pd.DataFrame, None, None],
) -> Generator[pd.DataFrame, None, None]:
    """Stream feature calculation over employee chunks without high memory consumption.

    Args:
        chunks: Generator yielding DataFrame chunks grouped by employee.

    Yields:
        Feature-engineered DataFrame chunks.
    """
    for chunk in chunks:
        yield compute_payroll_features(chunk)
