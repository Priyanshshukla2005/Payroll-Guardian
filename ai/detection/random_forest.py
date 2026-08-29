"""Supervised Random Forest anomaly classifier for AI Payroll Guardian."""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from ai.detection.anomaly_detector import BaseAnomalyDetector


class RandomForestDetector(BaseAnomalyDetector):
    """Supervised Random Forest classifier with balanced class weighting."""

    def __init__(
        self,
        n_estimators: int = 150,
        max_depth: Optional[int] = 16,
        min_samples_split: int = 10,
        min_samples_leaf: int = 4,
        max_features: Union[str, float] = "sqrt",
        class_weight: Union[str, dict] = "balanced",
        random_state: int = 42,
    ):
        super().__init__(name="RandomForest", model_type="supervised")
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.class_weight = class_weight
        self.random_state = random_state

        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            max_features=self.max_features,
            class_weight=self.class_weight,
            random_state=self.random_state,
            n_jobs=-1,
        )

    def fit(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y: Union[pd.Series, np.ndarray],
    ) -> "RandomForestDetector":
        """Fit Random Forest on training feature matrix X and ground truth binary labels y."""
        if y is None:
            raise ValueError("Supervised RandomForest requires binary target labels y.")

        if isinstance(X, pd.DataFrame):
            self.feature_names_in_ = X.columns.tolist()
            X_mat = X.values
        else:
            X_mat = np.asarray(X)

        y_arr = np.asarray(y).astype(int)
        self.model.fit(X_mat, y_arr)
        self.is_fitted = True
        return self

    def predict_score(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Compute anomaly probability as the continuous anomaly score."""
        proba = self.predict_proba(X)
        return proba[:, 1]

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Predict class probabilities [P(normal), P(anomaly)]."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict_proba().")
        X_mat = X.values if isinstance(X, pd.DataFrame) else np.asarray(X)
        return self.model.predict_proba(X_mat)

    def get_feature_importances(self) -> Optional[Dict[str, float]]:
        """Return dictionary mapping feature names to Gini importance scores."""
        if not self.is_fitted:
            return None
        importances = self.model.feature_importances_
        if self.feature_names_in_ is not None and len(self.feature_names_in_) == len(importances):
            return dict(sorted(zip(self.feature_names_in_, importances), key=lambda x: x[1], reverse=True))
        return {f"feat_{i}": float(v) for i, v in enumerate(importances)}
