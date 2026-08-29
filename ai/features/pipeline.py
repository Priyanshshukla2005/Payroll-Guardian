"""Reusable scikit-learn preprocessing pipeline for AI Payroll Guardian.

Handles missing values, robust/standard scaling of numerical features,
and one-hot encoding of categorical features with strict train-only fitting.
"""

from pathlib import Path
from typing import List, Optional, Union
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler


class PayrollPreprocessor:
    """Preprocesses payroll feature matrices for ML anomaly detection models."""

    def __init__(
        self,
        numerical_features: Optional[List[str]] = None,
        categorical_features: Optional[List[str]] = None,
        use_robust_scaling: bool = True,
    ):
        self.numerical_features = numerical_features
        self.categorical_features = categorical_features
        self.use_robust_scaling = use_robust_scaling
        self.pipeline: Optional[ColumnTransformer] = None
        self.feature_names_out_: Optional[List[str]] = None
        self.is_fitted: bool = False

    def _infer_column_types(self, X: pd.DataFrame):
        """Automatically detect numerical vs categorical features if not explicitly provided."""
        if self.numerical_features is None:
            self.numerical_features = X.select_dtypes(include=[np.number]).columns.tolist()
        if self.categorical_features is None:
            self.categorical_features = X.select_dtypes(include=["object", "category"]).columns.tolist()

    def build_pipeline(self) -> ColumnTransformer:
        """Construct the underlying scikit-learn ColumnTransformer."""
        scaler = RobustScaler() if self.use_robust_scaling else StandardScaler()

        num_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", scaler),
            ]
        )

        cat_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
        )

        transformers = []
        if self.numerical_features:
            transformers.append(("num", num_transformer, self.numerical_features))
        if self.categorical_features:
            transformers.append(("cat", cat_transformer, self.categorical_features))

        return ColumnTransformer(transformers=transformers, remainder="drop")

    def fit(self, X: pd.DataFrame) -> "PayrollPreprocessor":
        """Fit preprocessing transformers strictly on training data."""
        self._infer_column_types(X)
        self.pipeline = self.build_pipeline()
        self.pipeline.fit(X)
        self.is_fitted = True

        # Extract generated feature names
        try:
            self.feature_names_out_ = self.pipeline.get_feature_names_out().tolist()
        except Exception:
            self.feature_names_out_ = [f"feature_{i}" for i in range(self.transform(X.iloc[0:2]).shape[1])]

        return self

    def transform(self, X: pd.DataFrame, return_df: bool = True) -> Union[np.ndarray, pd.DataFrame]:
        """Transform feature matrix using fitted preprocessor."""
        if not self.is_fitted or self.pipeline is None:
            raise RuntimeError("PayrollPreprocessor must be fitted on training data before calling transform().")

        transformed_array = self.pipeline.transform(X)

        if return_df:
            cols = self.feature_names_out_ or [f"feat_{i}" for i in range(transformed_array.shape[1])]
            return pd.DataFrame(transformed_array, columns=cols, index=X.index)

        return transformed_array

    def fit_transform(self, X: pd.DataFrame, return_df: bool = True) -> Union[np.ndarray, pd.DataFrame]:
        """Fit on training data and return transformed representation."""
        return self.fit(X).transform(X, return_df=return_df)

    def save(self, filepath: Union[str, Path]) -> Path:
        """Persist fitted preprocessor to disk."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "PayrollPreprocessor":
        """Load serialized preprocessor from disk."""
        from ai.detection.anomaly_detector import _register_legacy_unpickle_aliases
        _register_legacy_unpickle_aliases()
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Preprocessor file not found at: {path.resolve()}")
        return joblib.load(path)
