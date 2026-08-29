"""Deterministic baseline anomaly detector for AI Payroll Guardian.

Implements pure heuristic/business rules for all 13 anomaly categories without
using machine learning, serving as the benchmark against which future ML models are evaluated.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class PerTypeMetric(BaseModel):
    """Evaluation metrics for a specific anomaly category."""

    anomaly_type: str
    ground_truth_count: int
    detected_count: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float


class BaselineEvaluationReport(BaseModel):
    """Complete evaluation report for the deterministic baseline detector."""

    total_samples: int
    ground_truth_anomalies: int
    detected_anomalies: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    specificity: float
    per_type_metrics: Dict[str, PerTypeMetric] = Field(default_factory=dict)


class DeterministicBaselineDetector:
    """Non-machine-learning deterministic payroll anomaly detector."""

    RULE_NAMES = [
        "SUDDEN_SALARY_INCREASE",
        "SUDDEN_SALARY_DECREASE",
        "EXCESSIVE_OVERTIME",
        "ATTENDANCE_PAY_MISMATCH",
        "IMPOSSIBLE_ATTENDANCE",
        "DUPLICATE_EMPLOYEE_RECORD",
        "INCORRECT_PF",
        "INCORRECT_ESI",
        "ABNORMAL_DEDUCTION",
        "ABNORMALLY_HIGH_BONUS",
        "ABNORMAL_NET_SALARY",
        "MISSING_PAYROLL_RECORD",
        "DUPLICATE_PAYMENT",
    ]

    def __init__(self, tolerance: float = 1.0):
        self.tolerance = tolerance

    def evaluate_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """Evaluate each deterministic rule across all rows in df.

        Args:
            df: Feature-engineered or raw payroll DataFrame.

        Returns:
            pd.DataFrame of boolean flags where columns correspond to RULE_NAMES.
        """
        n = len(df)
        flags = pd.DataFrame(index=df.index)

        # 1. Sudden Salary Increase: > 45% increase
        if "salary_change_percentage" in df.columns:
            flags["SUDDEN_SALARY_INCREASE"] = df["salary_change_percentage"] > 45.0
        elif "basic_salary" in df.columns and "employee_id" in df.columns:
            prev_sal = df.groupby("employee_id")["basic_salary"].shift(1)
            pct = ((df["basic_salary"] - prev_sal) / np.maximum(prev_sal.abs(), 1.0)) * 100.0
            flags["SUDDEN_SALARY_INCREASE"] = pct > 45.0
        else:
            flags["SUDDEN_SALARY_INCREASE"] = False

        # 2. Sudden Salary Decrease: < -30% decrease
        if "salary_change_percentage" in df.columns:
            flags["SUDDEN_SALARY_DECREASE"] = df["salary_change_percentage"] < -30.0
        elif "basic_salary" in df.columns and "employee_id" in df.columns:
            prev_sal = df.groupby("employee_id")["basic_salary"].shift(1)
            pct = ((df["basic_salary"] - prev_sal) / np.maximum(prev_sal.abs(), 1.0)) * 100.0
            flags["SUDDEN_SALARY_DECREASE"] = pct < -30.0
        else:
            flags["SUDDEN_SALARY_DECREASE"] = False

        # 3. Excessive Overtime: >= 60.0 hours
        if "overtime_hours" in df.columns:
            flags["EXCESSIVE_OVERTIME"] = df["overtime_hours"] >= 60.0
        else:
            flags["EXCESSIVE_OVERTIME"] = False

        # 4. Attendance Pay Mismatch: worked full days but gross pay < 60% of baseline
        if {"present_days", "working_days", "gross_salary"}.issubset(df.columns):
            prev_gross = df.groupby("employee_id")["gross_salary"].shift(1).fillna(df["gross_salary"])
            flags["ATTENDANCE_PAY_MISMATCH"] = (
                (df["present_days"] == df["working_days"])
                & (df["gross_salary"] < 0.60 * prev_gross)
                & (prev_gross > 1000.0)
            )
        else:
            flags["ATTENDANCE_PAY_MISMATCH"] = False

        # 5. Impossible Attendance: present > working or present + leave > working
        if {"present_days", "leave_days", "working_days"}.issubset(df.columns):
            flags["IMPOSSIBLE_ATTENDANCE"] = (
                (df["present_days"] > df["working_days"])
                | ((df["present_days"] + df["leave_days"]) > df["working_days"])
            )
        elif {"present_days", "working_days"}.issubset(df.columns):
            flags["IMPOSSIBLE_ATTENDANCE"] = df["present_days"] > df["working_days"]
        else:
            flags["IMPOSSIBLE_ATTENDANCE"] = False

        # 6. Duplicate Employee Record: duplicated (employee_id, payroll_month)
        if {"employee_id", "payroll_month"}.issubset(df.columns):
            flags["DUPLICATE_EMPLOYEE_RECORD"] = df.duplicated(
                subset=["employee_id", "payroll_month"], keep=False
            )
        else:
            flags["DUPLICATE_EMPLOYEE_RECORD"] = False

        # 7. Incorrect PF: PF deviates from 12% of basic
        if {"pf", "basic_salary"}.issubset(df.columns):
            expected_pf = np.round(df["basic_salary"] * 0.12, 2)
            flags["INCORRECT_PF"] = np.abs(df["pf"] - expected_pf) > self.tolerance
        else:
            flags["INCORRECT_PF"] = False

        # 8. Incorrect ESI: ESI deducted for gross > 21k, or not 0.75% for gross <= 21k
        if {"esi", "gross_salary"}.issubset(df.columns):
            esi_ineligible = (df["gross_salary"] > 21_000.0) & (df["esi"] > self.tolerance)
            expected_esi = np.where(
                df["gross_salary"] <= 21_000.0,
                np.round(df["gross_salary"] * 0.0075, 2),
                0.0,
            )
            esi_calc_wrong = np.abs(df["esi"] - expected_esi) > self.tolerance
            flags["INCORRECT_ESI"] = esi_ineligible | esi_calc_wrong
        else:
            flags["INCORRECT_ESI"] = False

        # 9. Abnormal Deduction: other_deductions > 5000 or deduction ratio > 0.45
        if "other_deductions" in df.columns:
            flags["ABNORMAL_DEDUCTION"] = df["other_deductions"] > 5000.0
        elif "deduction_to_gross_ratio" in df.columns:
            flags["ABNORMAL_DEDUCTION"] = df["deduction_to_gross_ratio"] > 0.45
        else:
            flags["ABNORMAL_DEDUCTION"] = False

        # 10. Abnormally High Bonus: bonus > 120,000 or bonus > 0.45 of base
        if {"bonus", "basic_salary"}.issubset(df.columns):
            flags["ABNORMALLY_HIGH_BONUS"] = (df["bonus"] > 120_000.0) | (
                df["bonus"] > 0.45 * df["basic_salary"]
            )
        elif "bonus" in df.columns:
            flags["ABNORMALLY_HIGH_BONUS"] = df["bonus"] > 120_000.0
        else:
            flags["ABNORMALLY_HIGH_BONUS"] = False

        # 11. Abnormal Net Salary Reconciliation Failure: |net - (gross - ded)| > tolerance
        if {"net_salary", "gross_salary", "total_deductions"}.issubset(df.columns):
            expected_net = df["gross_salary"] - df["total_deductions"]
            flags["ABNORMAL_NET_SALARY"] = (
                np.abs(df["net_salary"] - expected_net) > self.tolerance
            )
        else:
            flags["ABNORMAL_NET_SALARY"] = False

        # 12. Missing Payroll Record: gaps in monthly continuity per employee
        if {"employee_id", "payroll_month"}.issubset(df.columns):
            # Missing records are rows omitted from df; within df itself flag if anomaly_type matches
            if "anomaly_type" in df.columns:
                flags["MISSING_PAYROLL_RECORD"] = df["anomaly_type"].str.contains("MISSING_PAYROLL_RECORD", na=False)
            else:
                flags["MISSING_PAYROLL_RECORD"] = False
        else:
            flags["MISSING_PAYROLL_RECORD"] = False

        # 13. Duplicate Payment: duplicate employee, month, and exact net_salary
        if {"employee_id", "payroll_month", "net_salary"}.issubset(df.columns):
            flags["DUPLICATE_PAYMENT"] = df.duplicated(
                subset=["employee_id", "payroll_month", "net_salary"], keep=False
            ) & flags["DUPLICATE_EMPLOYEE_RECORD"]
        else:
            flags["DUPLICATE_PAYMENT"] = False

        # Fill any missing booleans
        for col in self.RULE_NAMES:
            if col not in flags.columns:
                flags[col] = False
            flags[col] = flags[col].fillna(False).astype(bool)

        return flags

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Predict binary anomaly status (1 if any rule triggers, 0 otherwise)."""
        rule_flags = self.evaluate_rules(df)
        any_triggered = rule_flags.any(axis=1)
        return any_triggered.astype(int).values

    def predict_types(self, df: pd.DataFrame) -> List[str]:
        """Return comma-separated string of triggered anomaly rule names for each row."""
        rule_flags = self.evaluate_rules(df)
        predicted_types = []
        for idx in range(len(df)):
            row = rule_flags.iloc[idx]
            triggered = [rule for rule in self.RULE_NAMES if row[rule]]
            predicted_types.append(",".join(triggered) if triggered else "NONE")
        return predicted_types

    def evaluate(
        self,
        df: pd.DataFrame,
        y_true: Optional[Union[pd.Series, np.ndarray]] = None,
        anomaly_types_true: Optional[pd.Series] = None,
    ) -> BaselineEvaluationReport:
        """Evaluate baseline detector against ground truth labels and compute metrics.

        Args:
            df: Input DataFrame.
            y_true: Ground truth binary labels (0 or 1). If None, extracted from df['is_anomaly'].
            anomaly_types_true: Ground truth anomaly type strings. If None, extracted from df['anomaly_type'].

        Returns:
            BaselineEvaluationReport with overall and per-type precision/recall metrics.
        """
        if y_true is None:
            if "is_anomaly" not in df.columns:
                raise ValueError("Ground truth labels not found; supply y_true or ensure 'is_anomaly' in df.")
            y_arr = df["is_anomaly"].values.astype(int)
        else:
            y_arr = np.asarray(y_true).astype(int)

        if anomaly_types_true is None and "anomaly_type" in df.columns:
            types_series = df["anomaly_type"]
        else:
            types_series = anomaly_types_true

        rule_flags = self.evaluate_rules(df)
        y_pred = rule_flags.any(axis=1).astype(int).values

        total = len(y_arr)
        tp = int(np.sum((y_pred == 1) & (y_arr == 1)))
        fp = int(np.sum((y_pred == 1) & (y_arr == 0)))
        tn = int(np.sum((y_pred == 0) & (y_arr == 0)))
        fn = int(np.sum((y_pred == 0) & (y_arr == 1)))

        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        accuracy = ((tp + tn) / total) if total > 0 else 0.0
        specificity = (tn / (tn + fp)) if (tn + fp) > 0 else 0.0

        # Per-type metrics
        per_type_metrics: Dict[str, PerTypeMetric] = {}
        if types_series is not None:
            for atype in self.RULE_NAMES:
                is_type_true = types_series.str.contains(atype, na=False).values
                is_type_pred = rule_flags[atype].values

                t_gt_count = int(np.sum(is_type_true))
                t_det_count = int(np.sum(is_type_pred))
                t_tp = int(np.sum(is_type_true & is_type_pred))
                t_fp = int(np.sum((~is_type_true) & is_type_pred))
                t_fn = int(np.sum(is_type_true & (~is_type_pred)))

                t_prec = (t_tp / (t_tp + t_fp)) if (t_tp + t_fp) > 0 else 0.0
                t_rec = (t_tp / (t_tp + t_fn)) if (t_tp + t_fn) > 0 else 0.0
                t_f1 = (2 * t_prec * t_rec / (t_prec + t_rec)) if (t_prec + t_rec) > 0 else 0.0

                per_type_metrics[atype] = PerTypeMetric(
                    anomaly_type=atype,
                    ground_truth_count=t_gt_count,
                    detected_count=t_det_count,
                    true_positives=t_tp,
                    false_positives=t_fp,
                    false_negatives=t_fn,
                    precision=round(t_prec, 4),
                    recall=round(t_rec, 4),
                    f1_score=round(t_f1, 4),
                )

        report = BaselineEvaluationReport(
            total_samples=total,
            ground_truth_anomalies=int(np.sum(y_arr == 1)),
            detected_anomalies=int(np.sum(y_pred == 1)),
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            accuracy=round(accuracy, 4),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            specificity=round(specificity, 4),
            per_type_metrics=per_type_metrics,
        )

        return report
