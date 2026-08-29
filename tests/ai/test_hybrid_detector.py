"""Unit tests for HybridPayrollDetector_V2 and rule override behavior."""

import numpy as np
import pandas as pd
import pytest

from ai.detection.enhanced_rules import EnhancedRuleDetector
from ai.detection.hybrid_detector import HybridPayrollDetector_V2
from ai.detection.random_forest import RandomForestDetector


@pytest.fixture
def mock_feature_matrix():
    """Fixture providing mock feature matrix and raw records."""
    np.random.seed(42)
    n = 20
    cols = ["feat_1", "feat_2", "num__robust_salary_zscore_dept"]
    X = pd.DataFrame(np.random.randn(n, len(cols)), columns=cols)
    y = pd.Series(np.random.choice([0, 1], size=n, p=[0.8, 0.2]))

    raw_records = pd.DataFrame({
        "basic_salary": [30000.0] * n,
        "allowances": [36000.0] * n,
        "overtime_amount": [0.0] * n,
        "bonus": [0.0] * n,
        "gross_salary": [66000.0] * n,
        "pf": [3600.0] * n,
        "esi": [0.0] * n,
        "tds": [3000.0] * n,
        "other_deductions": [200.0] * n,
        "total_deductions": [6800.0] * n,
        "net_salary": [59200.0] * n,
        "present_days": [26] * n,
        "working_days": [26] * n,
        "leave_days": [0] * n,
        "overtime_hours": [0.0] * n,
    })
    return X, y, raw_records


def test_hybrid_detector_fit_and_rule_override(mock_feature_matrix):
    """Verify that deterministic rule violation guarantees a 1.0 risk score in Hybrid V2."""
    X, y, raw_records = mock_feature_matrix
    hybrid = HybridPayrollDetector_V2(
        base_ml_model=RandomForestDetector(n_estimators=10, max_depth=4, random_state=42),
        rule_detector=EnhancedRuleDetector(),
    )
    hybrid.fit(X, y)

    # In raw_records[0], corrupt PF: expected 3600, set to 5000 -> rule violation
    raw_tampered = raw_records.copy()
    raw_tampered.at[0, "pf"] = 5000.0

    signals = hybrid.compute_risk_signals(X, raw_df=raw_tampered)
    assert signals.at[0, "rule_score"] == 1.0
    assert signals.at[0, "final_risk_score"] == 1.0

    preds = hybrid.predict(X, raw_df=raw_tampered, threshold=0.5)
    assert preds[0] == 1


def test_hybrid_detector_save_load(mock_feature_matrix, tmp_path):
    """Verify Hybrid V2 serialization and reloading."""
    X, y, _ = mock_feature_matrix
    hybrid = HybridPayrollDetector_V2(
        base_ml_model=RandomForestDetector(n_estimators=10, max_depth=4, random_state=42)
    )
    hybrid.fit(X, y)

    save_path = tmp_path / "hybrid_test.joblib"
    hybrid.save(save_path)
    assert save_path.exists()

    loaded = HybridPayrollDetector_V2.load(save_path)
    assert loaded.is_fitted
    np.testing.assert_allclose(hybrid.predict_score(X), loaded.predict_score(X))
