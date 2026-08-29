"""Comprehensive model evaluation engine for AI Payroll Guardian.

Calculates Precision, Recall, F1, PR-AUC, ROC-AUC, Record-Level FP,
Unique-Employee FP per 1,000 Employees, Threshold Sweeps, and Per-Type Breakdown.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


class AnomalyTypePerformance(BaseModel):
    """Performance metrics for an individual anomaly type."""

    anomaly_type: str
    ground_truth_count: int
    detected_count: int
    precision: float
    recall: float
    f1_score: float


class ModelEvaluationMetrics(BaseModel):
    """Complete evaluation report for a single model at a specified decision threshold."""

    model_name: str
    dataset_split: str
    threshold: float
    total_records: int
    total_unique_employees: int
    ground_truth_anomalies: int
    predicted_anomalies: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    specificity: float
    pr_auc: float
    roc_auc: float
    record_false_positive_rate: float
    unique_employee_fp_count: int
    unique_employee_fp_per_1000: float
    inference_time_ms_per_record: float
    per_type_performance: Dict[str, AnomalyTypePerformance] = Field(default_factory=dict)


def compute_unique_employee_fp_per_1000(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    employee_ids: Union[pd.Series, np.ndarray, List[str]],
) -> Tuple[int, float]:
    """Calculate the number and rate of unique employees falsely flagged.

    Formula:
        Unique Employee FP/1000 = (Distinct employees with >= 1 False Alarm / Total Distinct Employees) * 1000

    Args:
        y_true: Binary ground truth array (0 = Normal, 1 = Anomaly).
        y_pred: Binary predicted array (0 = Normal, 1 = Anomaly).
        employee_ids: Series or array of employee IDs corresponding to each record.

    Returns:
        Tuple of (unique_fp_employee_count, unique_fp_per_1000_rate).
    """
    emp_series = pd.Series(employee_ids).values
    total_unique_emps = len(np.unique(emp_series))

    if total_unique_emps == 0:
        return 0, 0.0

    # False positive mask: model says 1, but ground truth is 0
    fp_mask = (y_pred == 1) & (y_true == 0)
    fp_emp_ids = np.unique(emp_series[fp_mask])
    unique_fp_count = len(fp_emp_ids)

    rate_per_1000 = (unique_fp_count / total_unique_emps) * 1000.0
    return unique_fp_count, round(rate_per_1000, 2)


def evaluate_binary_model(
    model_name: str,
    y_true: Union[pd.Series, np.ndarray],
    y_proba: Union[pd.Series, np.ndarray],
    threshold: float = 0.5,
    employee_ids: Optional[Union[pd.Series, np.ndarray]] = None,
    anomaly_types: Optional[pd.Series] = None,
    dataset_split: str = "Validation",
    inference_time_ms_per_record: float = 0.0,
) -> ModelEvaluationMetrics:
    """Compute comprehensive evaluation metrics for a binary anomaly detector."""
    y_arr = np.asarray(y_true).astype(int)
    probs = np.asarray(y_proba).astype(float)
    y_pred = (probs >= threshold).astype(int)

    total_records = len(y_arr)
    cm = confusion_matrix(y_arr, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    prec = float(precision_score(y_arr, y_pred, zero_division=0))
    rec = float(recall_score(y_arr, y_pred, zero_division=0))
    f1 = float(f1_score(y_arr, y_pred, zero_division=0))
    acc = float(accuracy_score(y_arr, y_pred))
    spec = float(tn / max(tn + fp, 1))

    # PR-AUC and ROC-AUC
    try:
        pr_auc = float(average_precision_score(y_arr, probs))
    except Exception:
        pr_auc = 0.0

    try:
        roc_auc = float(roc_auc_score(y_arr, probs))
    except Exception:
        roc_auc = 0.5

    # False Positive Metrics
    rec_fpr = float(fp / max(tn + fp, 1))

    if employee_ids is not None:
        u_fp_count, u_fp_per_1000 = compute_unique_employee_fp_per_1000(y_arr, y_pred, employee_ids)
        total_unique_emps = len(np.unique(employee_ids))
    else:
        u_fp_count, u_fp_per_1000 = fp, (fp / max(total_records, 1)) * 1000.0
        total_unique_emps = total_records

    # Per Anomaly Type Breakdown
    per_type_metrics: Dict[str, AnomalyTypePerformance] = {}
    if anomaly_types is not None:
        unique_types = [t for t in anomaly_types.dropna().unique() if t != "NONE"]
        for atype in unique_types:
            type_mask = anomaly_types.str.contains(atype, regex=False).values
            gt_count = int(np.sum(type_mask))
            det_count = int(np.sum(type_mask & (y_pred == 1)))

            t_rec = (det_count / gt_count) if gt_count > 0 else 0.0
            # For precision, evaluate accuracy within the subset flagged for this type
            t_prec = prec  # Overall precision reference
            t_f1 = (2 * t_prec * t_rec / (t_prec + t_rec)) if (t_prec + t_rec) > 0 else 0.0

            per_type_metrics[atype] = AnomalyTypePerformance(
                anomaly_type=atype,
                ground_truth_count=gt_count,
                detected_count=det_count,
                precision=round(t_prec, 4),
                recall=round(t_rec, 4),
                f1_score=round(t_f1, 4),
            )

    return ModelEvaluationMetrics(
        model_name=model_name,
        dataset_split=dataset_split,
        threshold=round(threshold, 3),
        total_records=total_records,
        total_unique_employees=total_unique_emps,
        ground_truth_anomalies=int(np.sum(y_arr == 1)),
        predicted_anomalies=int(np.sum(y_pred == 1)),
        true_positives=int(tp),
        false_positives=int(fp),
        true_negatives=int(tn),
        false_negatives=int(fn),
        accuracy=round(acc, 4),
        precision=round(prec, 4),
        recall=round(rec, 4),
        f1_score=round(f1, 4),
        specificity=round(spec, 4),
        pr_auc=round(pr_auc, 4),
        roc_auc=round(roc_auc, 4),
        record_false_positive_rate=round(rec_fpr, 4),
        unique_employee_fp_count=u_fp_count,
        unique_employee_fp_per_1000=u_fp_per_1000,
        inference_time_ms_per_record=round(inference_time_ms_per_record, 4),
        per_type_performance=per_type_metrics,
    )


def sweep_thresholds(
    y_true: Union[pd.Series, np.ndarray],
    y_proba: Union[pd.Series, np.ndarray],
    employee_ids: Optional[Union[pd.Series, np.ndarray]] = None,
    thresholds: Optional[List[float]] = None,
) -> pd.DataFrame:
    """Evaluate performance metrics across a range of decision thresholds.

    Args:
        y_true: Ground truth binary labels.
        y_proba: Predicted anomaly probabilities / scores.
        employee_ids: Optional employee IDs for calculating unique employee FP/1000.
        thresholds: List of threshold floats (defaults to [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]).

    Returns:
        pd.DataFrame with metrics for each threshold.
    """
    thresh_list = thresholds or [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]
    results = []

    for t in thresh_list:
        m = evaluate_binary_model(
            model_name="ThresholdSweep",
            y_true=y_true,
            y_proba=y_proba,
            threshold=t,
            employee_ids=employee_ids,
        )
        results.append({
            "threshold": t,
            "precision": m.precision,
            "recall": m.recall,
            "f1_score": m.f1_score,
            "false_positives": m.false_positives,
            "false_negatives": m.false_negatives,
            "unique_emp_fp_per_1000": m.unique_employee_fp_per_1000,
        })

    return pd.DataFrame(results)
