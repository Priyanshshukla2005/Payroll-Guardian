"""Tests for scikit-learn preprocessing pipeline."""

import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from backend.config.settings import get_settings
from ai.features.payroll_features import compute_payroll_features
from ai.features.splitter import separate_features_labels_metadata
from ai.features.pipeline import PayrollPreprocessor
from data_pipeline.generator import generate_synthetic_payroll_dataset


@pytest.fixture
def sample_features():
    """Fixture providing feature-engineered DataFrame."""
    settings = get_settings()
    df = generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=50,
        num_months=3,
        random_seed=42,
    )
    df_feat = compute_payroll_features(df)
    X, y, _ = separate_features_labels_metadata(df_feat)
    return X


def test_payroll_preprocessor_fit_transform(sample_features):
    """Verify preprocessor fits, transforms, and produces valid output without NaNs."""
    preprocessor = PayrollPreprocessor(use_robust_scaling=True)
    X_trans = preprocessor.fit_transform(sample_features)

    assert isinstance(X_trans, pd.DataFrame)
    assert len(X_trans) == len(sample_features)
    assert not X_trans.isna().any().any()
    assert len(preprocessor.feature_names_out_) == X_trans.shape[1]


def test_preprocessor_serialization(sample_features):
    """Verify preprocessor can be saved and loaded from disk via joblib."""
    preprocessor = PayrollPreprocessor()
    preprocessor.fit(sample_features)
    expected_trans = preprocessor.transform(sample_features)

    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "preprocessor.joblib"
        preprocessor.save(save_path)
        assert save_path.exists()

        loaded_preprocessor = PayrollPreprocessor.load(save_path)
        assert loaded_preprocessor.is_fitted
        loaded_trans = loaded_preprocessor.transform(sample_features)

        pd.testing.assert_frame_equal(expected_trans, loaded_trans)
