"""Cold-start features and robust statistical anomaly signals for AI Payroll Guardian.

Provides historical observation depth indicators, dynamic cohort fallbacks,
Median Absolute Deviation (MAD), and robust z-score signals.
"""

from typing import List, Optional
import numpy as np
import pandas as pd


def compute_robust_mad_zscore(values: np.ndarray, medians: np.ndarray, mads: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    """Compute robust z-score: (x - median) / (1.4826 * MAD + eps)."""
    scale = 1.4826 * np.maximum(mads, eps)
    return (values - medians) / scale


def compute_cold_start_and_statistical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute observation depth, robust cohort MAD z-scores, and dynamic fallbacks.

    Args:
        df: Input DataFrame with basic payroll columns.

    Returns:
        pd.DataFrame with added cold-start and robust statistical features.
    """
    out = df.copy()

    # 1. Observation History Depth & Flags
    if "employee_id" in out.columns and "payroll_month" in out.columns:
        out = out.sort_values(by=["employee_id", "payroll_month"]).reset_index(drop=True)
        # Count strictly prior observations (t - 1)
        out["historical_observation_count"] = out.groupby("employee_id").cumcount().astype(float)
        out["months_of_history"] = out["historical_observation_count"]
        out["has_previous_salary"] = (out["historical_observation_count"] > 0).astype(float)
        out["has_previous_overtime"] = (out["historical_observation_count"] > 0).astype(float)
    else:
        out["historical_observation_count"] = 0.0
        out["months_of_history"] = 0.0
        out["has_previous_salary"] = 0.0
        out["has_previous_overtime"] = 0.0

    # 2. Robust Cohort Statistics (Department Level)
    if "department" in out.columns and "payroll_month" in out.columns and "basic_salary" in out.columns:
        # Dept Median and MAD for basic salary
        dept_grp = out.groupby(["payroll_month", "department"])["basic_salary"]
        dept_median = dept_grp.transform("median")
        dept_mad = (out["basic_salary"] - dept_median).abs()
        dept_mad_val = out.groupby(["payroll_month", "department"]).apply(
            lambda g: (g["basic_salary"] - g["basic_salary"].median()).abs().median()
        )
        # Merge back MAD values
        out["dept_month_basic_median"] = dept_median
        out["dept_month_basic_mad"] = out.groupby(["payroll_month", "department"])["basic_salary"].transform(
            lambda s: (s - s.median()).abs().median()
        ).fillna(1000.0)
        out["robust_salary_zscore_dept"] = compute_robust_mad_zscore(
            out["basic_salary"].values,
            out["dept_month_basic_median"].values,
            out["dept_month_basic_mad"].values,
        )

        # Department cohort empirical percentile rank [0, 1]
        out["stat_gross_percentile_in_dept"] = out.groupby(["payroll_month", "department"])["gross_salary"].rank(pct=True)

    # 3. Robust Cohort Statistics (Designation Level)
    if "designation" in out.columns and "payroll_month" in out.columns and "gross_salary" in out.columns:
        out["desig_month_gross_median"] = out.groupby(["payroll_month", "designation"])["gross_salary"].transform("median")
        out["desig_month_gross_mad"] = out.groupby(["payroll_month", "designation"])["gross_salary"].transform(
            lambda s: (s - s.median()).abs().median()
        ).fillna(1000.0)
        out["robust_gross_zscore_desig"] = compute_robust_mad_zscore(
            out["gross_salary"].values,
            out["desig_month_gross_median"].values,
            out["desig_month_gross_mad"].values,
        )

    # 4. Overtime Cohort Deviation
    if "designation" in out.columns and "payroll_month" in out.columns and "overtime_hours" in out.columns:
        out["desig_month_ot_median"] = out.groupby(["payroll_month", "designation"])["overtime_hours"].transform("median")
        out["desig_month_ot_mad"] = out.groupby(["payroll_month", "designation"])["overtime_hours"].transform(
            lambda s: (s - s.median()).abs().median()
        ).fillna(5.0)
        out["robust_overtime_zscore_desig"] = compute_robust_mad_zscore(
            out["overtime_hours"].values,
            out["desig_month_ot_median"].values,
            out["desig_month_ot_mad"].values,
        )

    # Fill any remaining NaNs with 0.0
    out = out.fillna(0.0)
    return out
