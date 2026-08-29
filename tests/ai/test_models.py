"""Unit tests for Phase 3 anomaly detection models and serialization."""

import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from backend.config.settings import get_settings
from ai.features.payroll_features import compute_payroll_features
from ai.features.splitter import separate_features_labels_metadata
from ai.detection.autoencoder import TabularAutoencoderDetector
from ai.detection.xgboost_model import GradientBoostingDetector
from ai.detection.isolation_forest import IsolationForestDetector
from ai.detection.random_forest import RandomForestDetector
from ai.detection.type_classifier import MultiLabelAnomalyTypeClassifier
from ai.features.pipeline import PayrollPreprocessor
from data_pipeline.injector import PayrollAnomalyInjector
from data_pipeline.generator import generate_synthetic_payroll_dataset


@pytest.fixture(scope="module")
def prepared_dataset():
    """Fixture providing clean and anomalous preprocessed feature matrix for testing."""
    settings = get_settings()
    df_clean = generate_synthetic_payroll_dataset(
        settings=settings,
        num_employees=60,
        num_months=4,
        random_seed=42,
    )
    injector = PayrollAnomalyInjector(random_seed=42)
    df_anom, _ = injector.inject_all_anomalies(df_clean, anomaly_rate=0.10)
    df_feat = compute_payroll_features(df_anom)
    X_raw, y, meta = separate_features_labels_metadata(df_feat)
    preprocessor = PayrollPreprocessor(use_robust_scaling=True)
    X = preprocessor.fit_transform(X_raw)
    return X, y, meta


def test_random_forest_fit_predict_save_load(prepared_dataset):
    """Test RandomForest detector fit, probability bounds, thresholding, and joblib persistence."""
    X, y, _ = prepared_dataset
    rf = RandomForestDetector(n_estimators=30, max_depth=8, random_state=42)
    rf.fit(X, y)

    probs = rf.predict_proba(X)
    assert probs.shape == (len(X), 2)
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)
    np.testing.assert_allclose(probs.sum(axis=1), 1.0, atol=1e-5)

    preds = rf.predict(X, threshold=0.5)
    assert preds.shape == (len(X),)
    assert set(np.unique(preds)).issubset({0, 1})

    # Test serialization
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "rf_test.joblib"
        rf.save(save_path)
        assert save_path.exists()

        loaded_rf = RandomForestDetector.load(save_path)
        loaded_probs = loaded_rf.predict_proba(X)
        np.testing.assert_allclose(probs, loaded_probs)


def test_xgboost_fit_predict(prepared_dataset):
    """Test GradientBoosting / XGBoost detector fit and probability output."""
    X, y, _ = prepared_dataset
    xgb = GradientBoostingDetector(n_estimators=30, max_depth=4, random_state=42)
    xgb.fit(X, y)

    probs = xgb.predict_proba(X)
    assert probs.shape == (len(X), 2)
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)

    preds = xgb.predict(X, threshold=0.5)
    assert preds.shape == (len(X),)


def test_isolation_forest_pseudo_score(prepared_dataset):
    """Test Isolation Forest anomaly score and calibrated pseudo-score output."""
    X, y, _ = prepared_dataset
    iso = IsolationForestDetector(n_estimators=30, contamination=0.10, random_state=42)
    iso.fit(X, y)

    raw_scores = iso.predict_score(X)
    assert len(raw_scores) == len(X)

    pseudo_probs = iso.predict_proba(X)
    assert pseudo_probs.shape == (len(X), 2)
    assert np.all(pseudo_probs >= 0.0) and np.all(pseudo_probs <= 1.0)


def test_autoencoder_reconstruction_fit_predict(prepared_dataset):
    """Test TabularAutoencoder reconstruction error and output bounds."""
    X, y, _ = prepared_dataset
    ae = TabularAutoencoderDetector(latent_dim=8, epochs=4, batch_size=64, random_state=42)
    ae.fit(X, y)

    mse_scores = ae.predict_score(X)
    assert len(mse_scores) == len(X)
    assert np.all(mse_scores >= 0.0)

    probs = ae.predict_proba(X)
    assert probs.shape == (len(X), 2)
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)


def test_multilabel_anomaly_type_classifier(prepared_dataset):
    """Test MultiLabelAnomalyTypeClassifier multi-output prediction and evaluation."""
    X, _, meta = prepared_dataset
    clf = MultiLabelAnomalyTypeClassifier(n_estimators=30, max_depth=6, random_state=42)
    clf.fit(X, meta["anomaly_type"])

    pred_mat = clf.predict(X, threshold=0.4)
    assert pred_mat.shape == (len(X), len(clf.categories))
    assert set(np.unique(pred_mat)).issubset({0, 1})

    pred_strings = clf.predict_types(X, threshold=0.4)
    assert len(pred_strings) == len(X)
    assert isinstance(pred_strings[0], str)
