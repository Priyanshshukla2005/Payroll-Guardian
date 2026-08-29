"""Multi-label anomaly type classifier for AI Payroll Guardian.

Classifies anomalous payroll records into 13 specific anomaly categories,
supporting compound multi-anomaly records without loss of information.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier

ANOMALY_CATEGORIES = [
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


class MultiLabelAnomalyTypeClassifier:
    """Multi-label supervised classifier for categorizing payroll anomaly types."""

    def __init__(
        self,
        categories: Optional[List[str]] = None,
        n_estimators: int = 100,
        max_depth: int = 12,
        random_state: int = 42,
    ):
        self.categories = categories or ANOMALY_CATEGORIES
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.base_estimator = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            class_weight="balanced",
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.model = MultiOutputClassifier(self.base_estimator, n_jobs=-1)
        self.is_fitted: bool = False
        self.feature_names_in_: Optional[List[str]] = None

    def _encode_labels(self, y_type_series: pd.Series) -> np.ndarray:
        """Convert string series (single or comma-separated) into binary multi-hot matrix."""
        n = len(y_type_series)
        k = len(self.categories)
        Y_matrix = np.zeros((n, k), dtype=int)

        for col_idx, cat in enumerate(self.categories):
            mask = y_type_series.astype(str).str.contains(cat, regex=False)
            Y_matrix[:, col_idx] = mask.astype(int).values

        return Y_matrix

    def fit(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y_types: pd.Series,
    ) -> "MultiLabelAnomalyTypeClassifier":
        """Fit multi-label classifier on feature matrix X and string anomaly types."""
        if isinstance(X, pd.DataFrame):
            self.feature_names_in_ = X.columns.tolist()
            X_mat = X.values
        else:
            X_mat = np.asarray(X)

        Y_mat = self._encode_labels(y_types)
        self.model.fit(X_mat, Y_mat)
        self.is_fitted = True
        return self

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Predict per-category probabilities matrix of shape (N, 13)."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before calling predict_proba().")

        X_mat = X.values if isinstance(X, pd.DataFrame) else np.asarray(X)
        proba_list = self.model.predict_proba(X_mat)
        n = len(X_mat)
        k = len(self.categories)
        probs_matrix = np.zeros((n, k), dtype=float)

        for j, estimator_probs in enumerate(proba_list):
            if estimator_probs.shape[1] == 2:
                probs_matrix[:, j] = estimator_probs[:, 1]
            else:
                # Only 1 class seen during training for this estimator
                probs_matrix[:, j] = 0.0

        return probs_matrix

    def predict(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        threshold: float = 0.45,
    ) -> np.ndarray:
        """Predict binary multi-hot indicator matrix (N, 13) using decision threshold."""
        probs = self.predict_proba(X)
        return (probs >= threshold).astype(int)

    def predict_types(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        threshold: float = 0.45,
    ) -> List[str]:
        """Return list of comma-separated anomaly type strings (or 'NONE') for each sample."""
        pred_mat = self.predict(X, threshold=threshold)
        predicted_strings = []

        for row in pred_mat:
            triggered = [self.categories[i] for i, val in enumerate(row) if val == 1]
            predicted_strings.append(",".join(triggered) if triggered else "NONE")

        return predicted_strings

    def evaluate(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y_types_true: pd.Series,
        threshold: float = 0.45,
    ) -> Dict[str, Any]:
        """Evaluate multi-label classification metrics across all 13 anomaly categories."""
        Y_true = self._encode_labels(y_types_true)
        Y_pred = self.predict(X, threshold=threshold)

        # Micro and Macro metrics
        per_type_metrics = {}
        total_tp, total_fp, total_fn = 0, 0, 0

        for idx, cat in enumerate(self.categories):
            yt = Y_true[:, idx]
            yp = Y_pred[:, idx]

            tp = int(np.sum((yp == 1) & (yt == 1)))
            fp = int(np.sum((yp == 1) & (yt == 0)))
            fn = int(np.sum((yp == 0) & (yt == 1)))

            prec = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            rec = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

            total_tp += tp
            total_fp += fp
            total_fn += fn

            per_type_metrics[cat] = {
                "support": int(np.sum(yt == 1)),
                "detected": int(np.sum(yp == 1)),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
            }

        micro_prec = (total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 0.0
        micro_rec = (total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 0.0
        micro_f1 = (2 * micro_prec * micro_rec / (micro_prec + micro_rec)) if (micro_prec + micro_rec) > 0 else 0.0

        return {
            "micro_precision": round(micro_prec, 4),
            "micro_recall": round(micro_rec, 4),
            "micro_f1": round(micro_f1, 4),
            "per_type_metrics": per_type_metrics,
        }

    def save(self, filepath: Union[str, Path]) -> Path:
        """Persist classifier artifact to disk."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "MultiLabelAnomalyTypeClassifier":
        """Load serialized classifier from disk."""
        from ai.detection.anomaly_detector import _register_legacy_unpickle_aliases
        _register_legacy_unpickle_aliases()
        path = Path(filepath)
        return joblib.load(path)
