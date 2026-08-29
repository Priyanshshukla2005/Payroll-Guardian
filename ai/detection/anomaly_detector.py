"""Base anomaly detector abstract interface for AI Payroll Guardian."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import joblib
import numpy as np
import pandas as pd


def _register_legacy_unpickle_aliases():
    """Register backwards-compatible module mappings for legacy Phase 3 pickled models."""
    import sys
    import types
    import ai.detection.anomaly_detector
    import ai.detection.autoencoder
    import ai.detection.isolation_forest
    import ai.detection.random_forest
    import ai.detection.type_classifier
    import ai.detection.xgboost_model
    import ai.features.pipeline

    aliases = {
        "src": types.ModuleType("src"),
        "src.models": types.ModuleType("src.models"),
        "src.models.anomaly_detector": ai.detection.anomaly_detector,
        "src.models.random_forest_model": ai.detection.random_forest,
        "src.models.isolation_forest_model": ai.detection.isolation_forest,
        "src.models.gradient_boosting_model": ai.detection.xgboost_model,
        "src.models.autoencoder_model": ai.detection.autoencoder,
        "src.models.type_classifier": ai.detection.type_classifier,
        "src.preprocessing": types.ModuleType("src.preprocessing"),
        "src.preprocessing.pipeline": ai.features.pipeline,
    }
    for k, v in aliases.items():
        if k not in sys.modules:
            sys.modules[k] = v


class BaseAnomalyDetector(ABC):
    """Abstract base class for all payroll anomaly detection models."""

    def __init__(self, name: str, model_type: str = "supervised"):
        self.name = name
        self.model_type = model_type  # 'supervised', 'unsupervised', 'reconstruction'
        self.is_fitted: bool = False
        self.feature_names_in_: Optional[List[str]] = None
        self.optimal_threshold: float = 0.5

    @abstractmethod
    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[Union[pd.Series, np.ndarray]] = None) -> "BaseAnomalyDetector":
        """Fit the model on training feature matrix X and optional labels y."""
        pass

    @abstractmethod
    def predict_score(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Compute continuous anomaly score (higher value = more anomalous)."""
        pass

    @abstractmethod
    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Predict class probabilities [P(normal), P(anomaly)] or calibrated pseudo-probabilities.

        Returns 2D array of shape (N, 2).
        """
        pass

    def predict(self, X: Union[pd.DataFrame, np.ndarray], threshold: Optional[float] = None) -> np.ndarray:
        """Predict binary anomaly flag (0 = Normal, 1 = Anomaly) using decision threshold."""
        thresh = threshold if threshold is not None else self.optimal_threshold
        proba = self.predict_proba(X)
        anomaly_prob = proba[:, 1]
        return (anomaly_prob >= thresh).astype(int)

    def get_feature_importances(self) -> Optional[Dict[str, float]]:
        """Return dictionary mapping feature names to importance scores if supported."""
        return None

    def save(self, filepath: Union[str, Path]) -> Path:
        """Persist fitted model artifact to disk."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "BaseAnomalyDetector":
        """Load serialized model artifact from disk with legacy alias support."""
        _register_legacy_unpickle_aliases()
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found at: {path.resolve()}")
        loaded = joblib.load(path)
        return loaded
