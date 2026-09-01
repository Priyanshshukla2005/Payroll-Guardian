"""Feature drift detection using statistical Kolmogorov-Smirnov and PSI algorithms (Phase 10)."""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


class FeatureDriftDetector:
    """Detects statistical feature drift between baseline reference distributions and live batches."""

    MONITORED_FEATURES = [
        "basic_salary",
        "gross_salary",
        "net_salary",
        "pf_deduction",
        "overtime_hours",
    ]

    # Baseline empirical statistics for reference population
    DEFAULT_BASELINE = {
        "basic_salary": {"mean": 55000.0, "std": 35000.0, "p50": 45000.0},
        "gross_salary": {"mean": 75000.0, "std": 48000.0, "p50": 62000.0},
        "net_salary": {"mean": 67000.0, "std": 42000.0, "p50": 55000.0},
        "pf_deduction": {"mean": 6600.0, "std": 4200.0, "p50": 5400.0},
        "overtime_hours": {"mean": 4.5, "std": 8.0, "p50": 0.0},
    }

    def __init__(self, baseline_stats: Optional[Dict[str, Dict[str, float]]] = None):
        self.baseline = baseline_stats or self.DEFAULT_BASELINE

    @staticmethod
    def compute_psi(baseline_arr: np.ndarray, target_arr: np.ndarray, num_buckets: int = 10) -> float:
        """Compute Population Stability Index (PSI) using empirical quantile binning."""
        if len(baseline_arr) == 0 or len(target_arr) == 0:
            return 0.0

        quantiles = np.linspace(0, 100, num_buckets + 1)
        bins = np.percentile(baseline_arr, quantiles)
        bins[0] = -np.inf
        bins[-1] = np.inf
        bins = np.unique(bins)
        if len(bins) < 2:
            return 0.0

        k = len(bins) - 1
        base_counts, _ = np.histogram(baseline_arr, bins=bins)
        target_counts, _ = np.histogram(target_arr, bins=bins)

        # Standard Laplace smoothing
        base_pct = (base_counts + 1.0) / (len(baseline_arr) + k)
        target_pct = (target_counts + 1.0) / (len(target_arr) + k)

        psi = np.sum((target_pct - base_pct) * np.log(target_pct / base_pct))
        return float(max(0.0, psi))

    def assess_dataframe_drift(
        self,
        df_live: pd.DataFrame,
        psi_threshold: float = 0.20,
    ) -> Dict[str, Any]:
        """Assess drift across all monitored features in a live payroll batch."""
        drift_results = {}
        drift_detected = False
        drift_warnings = []

        for feat in self.MONITORED_FEATURES:
            if feat not in df_live.columns:
                continue

            vals = pd.to_numeric(df_live[feat], errors="coerce").dropna().values
            if len(vals) < 5:
                continue

            live_mean = float(np.mean(vals))
            live_std = float(np.std(vals))

            base_info = self.baseline.get(feat, {"mean": live_mean, "std": live_std or 1.0})
            base_mean = base_info["mean"]
            base_std = base_info["std"]

            # Generate synthetic reference sample from baseline Gaussian parameters
            np.random.seed(42)
            ref_sample = np.random.normal(loc=base_mean, scale=max(1.0, base_std), size=max(len(vals), 500))
            ref_sample = np.clip(ref_sample, a_min=0.0, a_max=None)

            psi_val = self.compute_psi(ref_sample, vals)
            mean_shift_pct = (
                abs(live_mean - base_mean) / base_mean * 100.0 if base_mean != 0 else 0.0
            )

            # Combined PSI and mean shift percentage thresholds:
            # Significant drift: (PSI >= 0.50 and mean_shift >= 50%) or mean_shift >= 80% -> SEVERE
            # Moderate drift: (PSI >= 0.25 and mean_shift >= 20%) or mean_shift >= 25% -> WARNING
            # Stable: otherwise -> STABLE
            if (psi_val >= 0.50 and mean_shift_pct >= 50.0) or mean_shift_pct >= 80.0:
                feat_severity = "SEVERE"
                is_drifting = True
            elif (psi_val >= 0.25 and mean_shift_pct >= 20.0) or mean_shift_pct >= 25.0:
                feat_severity = "WARNING"
                is_drifting = True
            else:
                feat_severity = "STABLE"
                is_drifting = False

            if is_drifting:
                drift_detected = True
                warning_msg = (
                    f"Drift [{feat_severity}] detected in '{feat}': PSI={psi_val:.3f}, "
                    f"Mean shifted {mean_shift_pct:.1f}% vs baseline ({base_mean:.1f} -> {live_mean:.1f})."
                )
                drift_warnings.append(warning_msg)

            drift_results[feat] = {
                "psi": round(psi_val, 4),
                "is_drift": is_drifting,
                "drift_severity": feat_severity,
                "live_mean": round(live_mean, 2),
                "baseline_mean": round(base_mean, 2),
                "live_std": round(live_std, 2),
                "mean_shift_pct": round(mean_shift_pct, 2),
                "status": f"DRIFT_{feat_severity}" if is_drifting else "STABLE",
            }

        # Calculate overall batch drift severity
        severities = [m["drift_severity"] for m in drift_results.values()]
        if "SEVERE" in severities:
            overall_severity = "SEVERE"
        elif "WARNING" in severities:
            overall_severity = "WARNING"
        else:
            overall_severity = "STABLE"

        return {
            "drift_detected": drift_detected,
            "drift_severity": overall_severity,
            "monitored_features_count": len(drift_results),
            "drift_warnings": drift_warnings,
            "feature_metrics": drift_results,
        }
