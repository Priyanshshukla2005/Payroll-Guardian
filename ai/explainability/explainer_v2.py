"""Enhanced structured explainability and audit evidence generator V2 (Phase 4).

Extracts multivariate behavioral signals, historical baseline comparisons,
peer cohort benchmarks, and deterministic rule violations for flagged records.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class DetailedEvidenceCard(BaseModel):
    """Structured audit evidence card suitable for human review and downstream LLM consumption."""

    employee_id: str
    payroll_month: str
    risk_score: float
    confidence: str  # 'VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW'
    top_signals: List[str]
    historical_comparison: Dict[str, Any]
    peer_comparison: Dict[str, Any]
    rule_violations: List[str]
    anomaly_types: List[str]
    human_readable_summary: str


class PayrollExplainerV2:
    """Generates structured evidence cards for flagged employee records."""

    def __init__(
        self,
        feature_names: Optional[List[str]] = None,
        feature_importances: Optional[Dict[str, float]] = None,
    ):
        self.feature_names = feature_names or []
        self.feature_importances = feature_importances or {}

    def explain(
        self,
        record: Union[pd.Series, dict],
        risk_score: float,
        predicted_anomaly_types: Optional[List[str]] = None,
        rule_violations: Optional[List[str]] = None,
    ) -> DetailedEvidenceCard:
        """Generate structured audit evidence card."""
        rec = record.to_dict() if isinstance(record, pd.Series) else record
        emp_id = str(rec.get("employee_id", "EMP_UNKNOWN"))
        month = str(rec.get("payroll_month", "YYYY-MM"))
        anom_types = predicted_anomaly_types or ["ANOMALY"]
        violations = rule_violations or []

        top_signals: List[str] = []

        # 1. Salary shift signal
        sal_pct = float(rec.get("salary_change_percentage", rec.get("num__salary_change_percentage", 0.0)))
        if abs(sal_pct) > 10.0:
            top_signals.append(f"Basic salary changed {sal_pct:+.1f}% MoM (observed: ₹{float(rec.get('basic_salary', 0.0)):,.2f})")

        # 2. Overtime signal
        ot = float(rec.get("overtime_hours", rec.get("num__overtime_hours", 0.0)))
        if ot > 30.0:
            top_signals.append(f"Logged {ot:.1f} hours overtime (exceeds normal monthly baseline)")

        # 3. Attendance signal
        att_ratio = float(rec.get("attendance_ratio", rec.get("num__attendance_ratio", 1.0)))
        if att_ratio > 1.0 or att_ratio < 0.50:
            top_signals.append(f"Attendance ratio is {att_ratio:.2f} ({rec.get('present_days', 0)} present / {rec.get('working_days', 26)} working days)")

        # 4. Deduction signal
        ded_ratio = float(rec.get("deduction_to_gross_ratio", rec.get("num__deduction_to_gross_ratio", 0.10)))
        if ded_ratio > 0.35:
            top_signals.append(f"Deduction burden is {ded_ratio*100:.1f}% of gross earnings")

        # 5. Rule violation signals
        for v in violations:
            top_signals.append(f"Deterministic Rule Triggered: {v}")

        if not top_signals:
            top_signals.append("Multivariate statistical anomaly across historical and cohort dimensions")

        # Historical comparison
        hist_comp = {
            "observed_basic": float(rec.get("basic_salary", 0.0)),
            "historical_mean_basic": float(rec.get("historical_salary_mean", 0.0)),
            "salary_zscore_vs_history": float(rec.get("salary_zscore_vs_history", 0.0)),
            "months_of_prior_history": float(rec.get("months_of_history", 0.0)),
        }

        # Peer comparison
        peer_comp = {
            "department": str(rec.get("department", "N/A")),
            "designation": str(rec.get("designation", "N/A")),
            "dept_mean_gross": float(rec.get("dept_month_gross_mean", 0.0)),
            "gross_vs_dept_ratio": float(rec.get("gross_vs_dept_ratio", 1.0)),
        }

        # Confidence level
        if risk_score >= 0.85:
            confidence = "VERY_HIGH"
        elif risk_score >= 0.65:
            confidence = "HIGH"
        elif risk_score >= 0.45:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        types_str = ", ".join(anom_types)
        summary = (
            f"Employee {emp_id} ({month}) evaluated with {risk_score*100:.1f}% risk score ({confidence} confidence) "
            f"classified as [{types_str}]. Primary signals: {'; '.join(top_signals[:3])}."
        )

        return DetailedEvidenceCard(
            employee_id=emp_id,
            payroll_month=month,
            risk_score=round(risk_score, 4),
            confidence=confidence,
            top_signals=top_signals,
            historical_comparison=hist_comp,
            peer_comparison=peer_comp,
            rule_violations=violations,
            anomaly_types=anom_types,
            human_readable_summary=summary,
        )
