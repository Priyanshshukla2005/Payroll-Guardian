"""Hybrid Anomaly Detector Architecture for AI Payroll Guardian (Phase 4).

Combines Supervised ML Behavioral Modeling + Enhanced Deterministic Rules Engine +
Robust Statistical Cohort Signals into a calibrated, robust Risk Score.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd

from ai.detection.anomaly_detector import BaseAnomalyDetector
from ai.detection.calibrator import ProbabilityCalibrator
from ai.detection.enhanced_rules import EnhancedRuleDetector
from ai.detection.random_forest import RandomForestDetector


class HybridPayrollDetector_V2(BaseAnomalyDetector):
    """Hybrid multi-layered payroll verification and anomaly detection engine."""

    def __init__(
        self,
        base_ml_model: Optional[BaseAnomalyDetector] = None,
        rule_detector: Optional[EnhancedRuleDetector] = None,
        calibrator: Optional[ProbabilityCalibrator] = None,
        ml_weight: float = 0.85,
        stats_weight: float = 0.15,
        optimal_threshold: float = 0.45,
    ):
        super().__init__(name="HybridPayrollDetector_V2", model_type="hybrid")
        self.ml_model = base_ml_model or RandomForestDetector(n_estimators=150, max_depth=16, class_weight="balanced", random_state=42)
        self.rule_detector = rule_detector or EnhancedRuleDetector()
        self.calibrator = calibrator or ProbabilityCalibrator(method="isotonic")
        self.ml_weight = ml_weight
        self.stats_weight = stats_weight
        self.optimal_threshold = optimal_threshold
        self.is_fitted: bool = False

    def fit(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y: Union[pd.Series, np.ndarray],
        X_val: Optional[Union[pd.DataFrame, np.ndarray]] = None,
        y_val: Optional[Union[pd.Series, np.ndarray]] = None,
    ) -> "HybridPayrollDetector_V2":
        """Fit ML component on training data and fit probability calibrator on validation data."""
        self.ml_model.fit(X, y)
        self.feature_names_in_ = self.ml_model.feature_names_in_

        # Fit calibrator on validation set if provided
        if X_val is not None and y_val is not None:
            raw_val_probs = self.ml_model.predict_proba(X_val)[:, 1]
            self.calibrator.fit(raw_val_probs, np.asarray(y_val))

        self.is_fitted = True
        return self

    def _extract_statistical_score(self, X: pd.DataFrame) -> np.ndarray:
        """Compute statistical deviation score based on robust cohort MAD z-scores."""
        stat_cols = [
            "num__robust_salary_zscore_dept",
            "num__robust_gross_zscore_desig",
            "num__robust_overtime_zscore_desig",
            "num__salary_zscore_vs_history",
        ]
        available = [c for c in stat_cols if c in X.columns]
        if not available:
            return np.zeros(len(X), dtype=float)

        # Max absolute robust z-score mapped through sigmoid
        z_matrix = X[available].abs().values
        max_z = np.max(z_matrix, axis=1)
        # Sigmoid compression: z=3.0 -> ~0.50, z=5.0 -> ~0.88
        stat_scores = 1.0 / (1.0 + np.exp(-1.2 * (max_z - 3.0)))
        return stat_scores

    def compute_risk_signals(
        self,
        X: pd.DataFrame,
        raw_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """Compute individual risk signals: ML score, Rule score, Statistical score, and Final Risk."""
        if not self.is_fitted:
            raise RuntimeError("Hybrid detector must be fitted before computing risk signals.")

        # 1. ML Behavioral Probability
        raw_ml_probs = self.ml_model.predict_proba(X)[:, 1]
        ml_probs = self.calibrator.calibrate(raw_ml_probs) if self.calibrator.is_fitted else raw_ml_probs

        # 2. Deterministic Rule Score
        if raw_df is not None:
            rule_scores = self.rule_detector.compute_rule_risk_scores(raw_df)
        else:
            rule_scores = np.zeros(len(X), dtype=float)

        # 3. Robust Statistical Anomaly Score
        stat_scores = self._extract_statistical_score(X)

        # 4. Hybrid Combination: Hard rules override, otherwise weighted blend
        soft_blend = (self.ml_weight * ml_probs) + (self.stats_weight * stat_scores)
        final_risk = np.maximum(rule_scores, soft_blend)
        final_risk = np.clip(final_risk, 0.0, 1.0)

        signals_df = pd.DataFrame({
            "ml_probability": np.round(ml_probs, 4),
            "rule_score": np.round(rule_scores, 4),
            "statistical_score": np.round(stat_scores, 4),
            "final_risk_score": np.round(final_risk, 4),
        }, index=X.index)

        return signals_df

    def predict_score(self, X: Union[pd.DataFrame, np.ndarray], raw_df: Optional[pd.DataFrame] = None) -> np.ndarray:
        """Compute final combined risk score in [0, 1]."""
        X_df = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X, columns=self.feature_names_in_)
        signals = self.compute_risk_signals(X_df, raw_df=raw_df)
        return signals["final_risk_score"].values

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray], raw_df: Optional[pd.DataFrame] = None) -> np.ndarray:
        """Predict 2D array of class probabilities [P(normal), P(anomaly)]."""
        risk = self.predict_score(X, raw_df=raw_df)
        p_normal = 1.0 - risk
        return np.column_stack([p_normal, risk])

    def predict(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        raw_df: Optional[pd.DataFrame] = None,
        threshold: Optional[float] = None,
    ) -> np.ndarray:
        """Predict binary anomaly flag using decision threshold."""
        thresh = threshold if threshold is not None else self.optimal_threshold
        risk = self.predict_score(X, raw_df=raw_df)
        return (risk >= thresh).astype(int)

    def get_feature_importances(self) -> Optional[Dict[str, float]]:
        """Extract feature importances from underlying ML tree model."""
        return self.ml_model.get_feature_importances()
