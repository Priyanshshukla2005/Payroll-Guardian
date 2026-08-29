"""Probability calibration and reliability analysis for AI Payroll Guardian (Phase 4).

Fits Isotonic Regression or Platt Scaling on validation set probabilities,
computes Expected Calibration Error (ECE), and generates reliability curves.
"""

from typing import Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss


class ProbabilityCalibrator:
    """Calibrates predicted raw probabilities to match true empirical event frequencies."""

    def __init__(self, method: str = "isotonic"):
        self.method = method  # 'isotonic' or 'sigmoid'
        self.calibrator = IsotonicRegression(out_of_bounds="clip") if method == "isotonic" else None
        self.is_fitted: bool = False
        self.brier_score_before_: float = 0.0
        self.brier_score_after_: float = 0.0
        self.ece_before_: float = 0.0
        self.ece_after_: float = 0.0

    @staticmethod
    def compute_expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
        """Compute Expected Calibration Error (ECE)."""
        bin_limits = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        n_samples = len(y_true)

        for i in range(n_bins):
            bin_mask = (y_prob >= bin_limits[i]) & (y_prob < bin_limits[i + 1])
            if np.any(bin_mask):
                bin_acc = np.mean(y_true[bin_mask])
                bin_conf = np.mean(y_prob[bin_mask])
                bin_size = np.sum(bin_mask)
                ece += (bin_size / n_samples) * np.abs(bin_acc - bin_conf)

        return float(ece)

    def fit(self, y_val_proba: np.ndarray, y_val_true: np.ndarray) -> "ProbabilityCalibrator":
        """Fit calibration mapping strictly on validation set predictions."""
        probs = np.asarray(y_val_proba, dtype=float)
        y_true = np.asarray(y_val_true, dtype=int)

        self.brier_score_before_ = float(brier_score_loss(y_true, probs))
        self.ece_before_ = self.compute_expected_calibration_error(y_true, probs)

        if self.method == "isotonic":
            self.calibrator.fit(probs, y_true)
        else:
            # Simple Platt sigmoid logistic fit
            from sklearn.linear_model import LogisticRegression
            self.calibrator = LogisticRegression(C=1.0, solver="lbfgs")
            self.calibrator.fit(probs.reshape(-1, 1), y_true)

        self.is_fitted = True
        cal_probs = self.calibrate(probs)
        self.brier_score_after_ = float(brier_score_loss(y_true, cal_probs))
        self.ece_after_ = self.compute_expected_calibration_error(y_true, cal_probs)
        return self

    def calibrate(self, y_prob: np.ndarray) -> np.ndarray:
        """Transform uncalibrated scores to well-calibrated probabilities."""
        if not self.is_fitted:
            return y_prob

        probs = np.asarray(y_prob, dtype=float)
        if self.method == "isotonic":
            return np.clip(self.calibrator.predict(probs), 0.0, 1.0)
        else:
            return np.clip(self.calibrator.predict_proba(probs.reshape(-1, 1))[:, 1], 0.0, 1.0)
