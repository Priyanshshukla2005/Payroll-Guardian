"""Gradient Boosted Trees anomaly detector for AI Payroll Guardian.

Uses XGBoost (with HistGradientBoostingClassifier fallback) for supervised
tabular anomaly classification with imbalance weighting.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from sklearn.ensemble import HistGradientBoostingClassifier

from ai.detection.anomaly_detector import BaseAnomalyDetector


class GradientBoostingDetector(BaseAnomalyDetector):
    """Gradient boosted decision tree classifier (XGBoost with HistGradientBoosting fallback)."""

    def __init__(
        self,
        n_estimators: int = 150,
        max_depth: int = 6,
        learning_rate: float = 0.08,
        subsample: float = 0.85,
        colsample_bytree: float = 0.85,
        random_state: int = 42,
    ):
        super().__init__(name="XGBoost" if HAS_XGBOOST else "HistGradientBoosting", model_type="supervised")
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state
        self.use_xgboost = HAS_XGBOOST
        self.model = None

    def fit(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y: Union[pd.Series, np.ndarray],
    ) -> "GradientBoostingDetector":
        """Fit Gradient Boosting model with positive class imbalance weighting."""
        if y is None:
            raise ValueError("Supervised Gradient Boosting requires binary target labels y.")

        if isinstance(X, pd.DataFrame):
            self.feature_names_in_ = X.columns.tolist()
            X_mat = X.values
        else:
            X_mat = np.asarray(X)

        y_arr = np.asarray(y).astype(int)
        n_pos = int(np.sum(y_arr == 1))
        n_neg = int(np.sum(y_arr == 0))
        scale_pos_weight = (n_neg / max(n_pos, 1))

        if self.use_xgboost:
            self.model = xgb.XGBClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                subsample=self.subsample,
                colsample_bytree=self.colsample_bytree,
                scale_pos_weight=scale_pos_weight,
                random_state=self.random_state,
                eval_metric="logloss",
                n_jobs=-1,
            )
            self.model.fit(X_mat, y_arr)
        else:
            # Fallback to HistGradientBoostingClassifier
            self.model = HistGradientBoostingClassifier(
                max_iter=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                class_weight="balanced",
                random_state=self.random_state,
            )
            self.model.fit(X_mat, y_arr)

        self.is_fitted = True
        return self

    def predict_score(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Compute anomaly probability score."""
        proba = self.predict_proba(X)
        return proba[:, 1]

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Predict class probabilities [P(normal), P(anomaly)]."""
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Model must be fitted before calling predict_proba().")
        X_mat = X.values if isinstance(X, pd.DataFrame) else np.asarray(X)
        return self.model.predict_proba(X_mat)

    def get_feature_importances(self) -> Optional[Dict[str, float]]:
        """Return feature importance scores."""
        if not self.is_fitted or self.model is None:
            return None

        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            if self.feature_names_in_ is not None and len(self.feature_names_in_) == len(importances):
                return dict(sorted(zip(self.feature_names_in_, importances), key=lambda x: x[1], reverse=True))
            return {f"feat_{i}": float(v) for i, v in enumerate(importances)}

        return None
