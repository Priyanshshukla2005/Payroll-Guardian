"""Unit tests for Phase 3 lightweight evidence generator and structured explainability."""

import pandas as pd
import pytest

from ai.explainability.explainer import PayrollExplainer, PayrollExplanation


def test_payroll_explainer_evidence_generation():
    """Verify structured signal generation for an anomalous employee record."""
    explainer = PayrollExplainer(
        feature_names=["salary_change_percentage", "overtime_hours"],
        feature_importances={"salary_change_percentage": 0.45, "overtime_hours": 0.35},
    )

    record = {
        "employee_id": "EMP000123",
        "payroll_month": "2024-10",
        "salary_change_percentage": 65.0,
        "overtime_hours": 85.0,
        "historical_salary_mean": 30000.0,
        "salary_zscore_vs_history": 3.8,
    }

    explanation = explainer.explain_record(
        record=record,
        anomaly_probability=0.96,
        predicted_category="SUDDEN_SALARY_INCREASE",
        triggered_rules=["SUDDEN_SALARY_INCREASE", "EXCESSIVE_OVERTIME"],
    )

    assert isinstance(explanation, PayrollExplanation)
    assert explanation.employee_id == "EMP000123"
    assert explanation.anomaly_probability == 0.96
    assert explanation.predicted_label == 1
    assert len(explanation.top_signals) >= 1
    assert "EMP000123" in explanation.human_readable_summary
    assert len(explanation.triggered_rules) == 2
