"""Isolation Forest unsupervised anomaly detector for AI Payroll Guardian.

Provides tree-based partitioning outlier scoring. Raw outputs are designated
strictly as 'anomaly_score', and normalized comparison outputs are designated
as 'calibrated_pseudo_score' (NOT true statistical probabilities).
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ai.detection.anomaly_detector import BaseAnomalyDetector


class IsolationForestDetector(BaseAnomalyDetector):
    """Unsupervised tree isolation anomaly detector."""

    def __init__(
        self,
        n_estimators: int = 150,
        max_samples: Union[int, float, str] = "auto",
        contamination: Union[float, str] = 0.05,
        max_features: float = 0.85,
        random_state: int = 42,
        train_on_normal_only: bool = True,
    ):
        super().__init__(name="IsolationForest", model_type="unsupervised")
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.contamination = contamination
        self.max_features = max_features
        self.random_state = random_state
        self.train_on_normal_only = train_on_normal_only

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            max_samples=self.max_samples,
            contamination=self.contamination,
            max_features=self.max_features,
            random_state=self.random_state,
            n_jobs=-1,
        )

        # Min and max reference bounds for score calibration
        self.score_min_: float = 0.0
        self.score_max_: float = 1.0

    def fit(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y: Optional[Union[pd.Series, np.ndarray]] = None,
    ) -> "IsolationForestDetector":
        """Fit Isolation Forest on training data (optionally filtering to normal records)."""
        if isinstance(X, pd.DataFrame):
            self.feature_names_in_ = X.columns.tolist()
            X_mat = X.values
        else:
            X_mat = np.asarray(X)

        if self.train_on_normal_only and y is not None:
            y_arr = np.asarray(y)
            normal_mask = (y_arr == 0)
            X_fit = X_mat[normal_mask] if np.any(normal_mask) else X_mat
        else:
            X_fit = X_mat

        self.model.fit(X_fit)
        self.is_fitted = True

        # Calculate calibration bounds on training set
        raw_scores = -self.model.score_samples(X_fit)
        self.score_min_ = float(np.min(raw_scores))
        self.score_max_ = float(np.max(raw_scores)) if np.max(raw_scores) > self.score_min_ else self.score_min_ + 1.0

        return self

    def predict_score(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Compute raw Isolation Forest anomaly score. Higher values indicate higher anomaly severity."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict_score().")
        X_mat = X.values if isinstance(X, pd.DataFrame) else np.asarray(X)
        # sklearn score_samples returns negative anomaly score (lower is more anomalous)
        # Invert sign so higher value = more anomalous
        raw_score = -self.model.score_samples(X_mat)
        return raw_score

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Compute calibrated pseudo-scores bounded in [0, 1] for benchmark comparison.

        NOTE: This represents a min-max calibrated anomaly score, NOT a true Bayesian probability.
        """
        raw_scores = self.predict_score(X)
        # Min-max scaling to [0, 1]
        denom = max(self.score_max_ - self.score_min_, 1e-6)
        calibrated_pseudo_score = np.clip((raw_scores - self.score_min_) / denom, 0.0, 1.0)

        # Return 2D array [1 - pseudo_score, pseudo_score]
        p_normal = 1.0 - calibrated_pseudo_score
        return np.column_stack([p_normal, calibrated_pseudo_score])
