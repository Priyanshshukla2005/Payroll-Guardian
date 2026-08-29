"""Lightweight model explainability and evidence generation engine for AI Payroll Guardian.

Extracts structured evidence, top contributing feature deviations, historical z-scores,
and rule flags for flagged employee payroll records.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class FeatureSignal(BaseModel):
    """Structured evidence signal for an individual feature."""

    feature_name: str
    observed_value: float
    historical_mean: Optional[float] = None
    z_score: Optional[float] = None
    percentage_change: Optional[float] = None
    importance_rank: int
    signal_severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'


class PayrollExplanation(BaseModel):
    """Structured evidence report explaining why an anomaly was flagged."""

    employee_id: str
    payroll_month: str
    anomaly_probability: float
    predicted_label: int
    primary_category: str
    top_signals: List[FeatureSignal]
    triggered_rules: List[str] = Field(default_factory=list)
    human_readable_summary: str


class PayrollExplainer:
    """Extracts structured explainability evidence for flagged payroll records."""

    def __init__(
        self,
        feature_names: Optional[List[str]] = None,
        feature_importances: Optional[Dict[str, float]] = None,
    ):
        self.feature_names = feature_names or []
        self.feature_importances = feature_importances or {}

    def explain_record(
        self,
        record: Union[pd.Series, dict],
        anomaly_probability: float,
        predicted_category: str = "UNKNOWN",
        triggered_rules: Optional[List[str]] = None,
        top_k: int = 4,
    ) -> PayrollExplanation:
        """Generate structured evidence signals for a single payroll record."""
        rec_dict = record.to_dict() if isinstance(record, pd.Series) else record

        emp_id = str(rec_dict.get("employee_id", "UNKNOWN"))
        month = str(rec_dict.get("payroll_month", "UNKNOWN"))
        rules = triggered_rules or []

        signals: List[FeatureSignal] = []

        # Key deviation checks
        # 1. Salary change %
        sal_pct = float(rec_dict.get("salary_change_percentage", rec_dict.get("num__salary_change_percentage", 0.0)))
        if abs(sal_pct) > 15.0:
            signals.append(
                FeatureSignal(
                    feature_name="salary_change_percentage",
                    observed_value=round(sal_pct, 2),
                    historical_mean=float(rec_dict.get("historical_salary_mean", 0.0)),
                    z_score=float(rec_dict.get("salary_zscore_vs_history", 0.0)),
                    percentage_change=round(sal_pct, 2),
                    importance_rank=1,
                    signal_severity="CRITICAL" if abs(sal_pct) > 40.0 else "HIGH",
                )
            )

        # 2. Overtime hours
        ot_hours = float(rec_dict.get("overtime_hours", rec_dict.get("num__overtime_hours", 0.0)))
        if ot_hours > 35.0:
            signals.append(
                FeatureSignal(
                    feature_name="overtime_hours",
                    observed_value=round(ot_hours, 1),
                    historical_mean=float(rec_dict.get("historical_overtime_mean", 0.0)),
                    z_score=float(rec_dict.get("overtime_zscore_vs_history", 0.0)),
                    percentage_change=float(rec_dict.get("overtime_change_percentage", 0.0)),
                    importance_rank=2,
                    signal_severity="CRITICAL" if ot_hours > 60.0 else "HIGH",
                )
            )

        # 3. Attendance ratio
        att_ratio = float(rec_dict.get("attendance_ratio", rec_dict.get("num__attendance_ratio", 1.0)))
        if att_ratio > 1.001 or att_ratio < 0.40:
            signals.append(
                FeatureSignal(
                    feature_name="attendance_ratio",
                    observed_value=round(att_ratio, 3),
                    percentage_change=float(rec_dict.get("present_days_change", 0.0)),
                    importance_rank=3,
                    signal_severity="CRITICAL" if att_ratio > 1.0 else "MEDIUM",
                )
            )

        # 4. Deduction-to-gross ratio
        ded_ratio = float(rec_dict.get("deduction_to_gross_ratio", rec_dict.get("num__deduction_to_gross_ratio", 0.10)))
        if ded_ratio > 0.35:
            signals.append(
                FeatureSignal(
                    feature_name="deduction_to_gross_ratio",
                    observed_value=round(ded_ratio, 3),
                    historical_mean=float(rec_dict.get("historical_total_deductions_mean", 0.0)),
                    z_score=float(rec_dict.get("total_deductions_zscore_vs_history", 0.0)),
                    importance_rank=4,
                    signal_severity="CRITICAL" if ded_ratio > 0.50 else "HIGH",
                )
            )

        # 5. Bonus
        bonus = float(rec_dict.get("bonus", rec_dict.get("num__bonus", 0.0)))
        if bonus > 50_000.0:
            signals.append(
                FeatureSignal(
                    feature_name="bonus",
                    observed_value=round(bonus, 2),
                    percentage_change=float(rec_dict.get("bonus_change_percentage", 0.0)),
                    importance_rank=5,
                    signal_severity="HIGH" if bonus > 100_000.0 else "MEDIUM",
                )
            )

        # Build summary
        signal_summaries = []
        for s in signals[:top_k]:
            if s.percentage_change is not None and abs(s.percentage_change) > 0.1:
                signal_summaries.append(f"{s.feature_name} shifted {s.percentage_change:+.1f}% (observed: {s.observed_value})")
            else:
                signal_summaries.append(f"{s.feature_name} = {s.observed_value}")

        signals_text = "; ".join(signal_summaries) if signal_summaries else "Multivariate pattern divergence"
        summary_text = (
            f"Employee {emp_id} ({month}) flagged with {anomaly_probability*100:.1f}% anomaly probability "
            f"[{predicted_category}]. Key signals: {signals_text}."
        )

        return PayrollExplanation(
            employee_id=emp_id,
            payroll_month=month,
            anomaly_probability=round(anomaly_probability, 4),
            predicted_label=1 if anomaly_probability >= 0.5 else 0,
            primary_category=predicted_category,
            top_signals=signals[:top_k],
            triggered_rules=rules,
            human_readable_summary=summary_text,
        )
