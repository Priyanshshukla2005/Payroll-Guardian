import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from ai.explainability.explainer_v2 import DetailedEvidenceCard, PayrollExplainerV2
from ai.features.cold_start_features import compute_cold_start_and_statistical_features
from ai.features.payroll_features import compute_payroll_features
from backend.dependencies.services import ModelManager


class DetectionService:
    """Orchestrates feature calculation, probability calibration, and anomaly type classification."""

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.last_feature_time_ms: float = 0.0
        self.last_detection_time_ms: float = 0.0

    def _prepare_features(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Execute complete feature engineering pipeline and align with model input schema."""
        res = df_raw.copy()

        # Map common field aliases
        if "pf" not in res.columns and "pf_deduction" in res.columns:
            res["pf"] = res["pf_deduction"]
        if "pf_deduction" not in res.columns and "pf" in res.columns:
            res["pf_deduction"] = res["pf"]

        if "tds" not in res.columns:
            res["tds"] = 0.0
        if "other_deductions" not in res.columns:
            res["other_deductions"] = 0.0
        if "overtime_amount" not in res.columns:
            hourly_rate = (res.get("basic_salary", 0.0) / 208.0) * 1.5
            res["overtime_amount"] = (res.get("overtime_hours", 0.0) * hourly_rate).fillna(0.0)
        if "employment_status" not in res.columns:
            res["employment_status"] = "ACTIVE"
        if "location" not in res.columns:
            res["location"] = "INDIA"

        # 1. Master Payroll Feature Engineering
        df_feat = compute_payroll_features(res)

        # 2. Cold-Start and Statistical Signals
        df_feat = compute_cold_start_and_statistical_features(df_feat)

        # Ensure all columns required by preprocessor exist
        preprocessor = self.model_manager.preprocessor
        if preprocessor and preprocessor.numerical_features:
            for col in preprocessor.numerical_features:
                if col not in df_feat.columns:
                    df_feat[col] = 0.0

        if preprocessor and preprocessor.categorical_features:
            for col in preprocessor.categorical_features:
                if col not in df_feat.columns:
                    df_feat[col] = "missing"

        return df_feat

    def detect_anomalies(
        self,
        df_raw: pd.DataFrame,
        decision_threshold: float = 0.45,
    ) -> List[Tuple[pd.Series, float, List[str], List[str], DetailedEvidenceCard]]:
        """Compute features, predict anomaly risk scores, categorize types, and generate evidence cards.

        Returns:
            List of tuples: (raw_row_series, risk_score, anomaly_types, rule_violations, evidence_card)
        """
        if not self.model_manager.is_loaded:
            self.model_manager.initialize()

        detector = self.model_manager.detector
        if detector is None:
            raise RuntimeError("AI_DETECTOR_UNAVAILABLE: ML anomaly detector is not loaded or model artifact is corrupted.")

        preprocessor = self.model_manager.preprocessor
        type_classifier = self.model_manager.type_classifier
        explainer = self.model_manager.explainer or PayrollExplainerV2()

        # 1. Feature Engineering
        t_feat_start = time.perf_counter()
        df_features = self._prepare_features(df_raw)
        self.last_feature_time_ms = (time.perf_counter() - t_feat_start) * 1000.0

        # 2. Preprocessing & Hybrid Scoring
        t_det_start = time.perf_counter()
        if preprocessor and preprocessor.is_fitted:
            X_preprocessed = preprocessor.transform(df_features)
        elif preprocessor:
            X_preprocessed = preprocessor.fit_transform(df_features)
        else:
            X_preprocessed = df_features.select_dtypes(include=[np.number]).values

        # 3. Hybrid Risk Scoring
        risk_scores = detector.predict_score(X_preprocessed, raw_df=df_raw)

        # 4. Multi-Label Anomaly Type Classification
        if type_classifier and type_classifier.is_fitted:
            predicted_types_raw = type_classifier.predict_types(X_preprocessed, threshold=0.40)
        else:
            predicted_types_raw = ["NONE"] * len(df_raw)

        # 5. Deterministic Rule Violations
        rule_scores = detector.rule_detector.compute_rule_risk_scores(df_raw)
        self.last_detection_time_ms = (time.perf_counter() - t_det_start) * 1000.0

        results = []
        for idx in range(len(df_raw)):
            row = df_raw.iloc[idx]
            r_score = float(risk_scores[idx])

            # Rule violations
            violations = []
            rec_dict = row.to_dict()
            pf_val = rec_dict.get("pf_deduction", rec_dict.get("pf", 0.0))
            basic_val = rec_dict.get("basic_salary", 0.0)
            if pf_val > 0 and abs(pf_val - 0.12 * basic_val) > 5.0:
                violations.append("RULE_PF_MISMATCH")
            if rec_dict.get("present_days", 0) > rec_dict.get("working_days", 26):
                violations.append("RULE_ATTENDANCE_BOUNDS_EXCEEDED")
            if rec_dict.get("overtime_hours", 0) > 60.0:
                violations.append("RULE_OVERTIME_EXCEEDS_CAP")
            if rule_scores[idx] >= 0.50 and not violations:
                violations.append("RULE_RECONCILIATION_VIOLATION")

            # Anomaly types
            if r_score >= decision_threshold or len(violations) > 0:
                types_str = predicted_types_raw[idx]
                types_list = [t.strip() for t in types_str.split(",") if t.strip() and t.strip() != "NONE"]
                if "RULE_PF_MISMATCH" in violations and "INCORRECT_PF" not in types_list:
                    types_list.append("INCORRECT_PF")
                if "RULE_ATTENDANCE_BOUNDS_EXCEEDED" in violations and "ATTENDANCE_MISMATCH" not in types_list:
                    types_list.append("ATTENDANCE_MISMATCH")
                if "RULE_OVERTIME_EXCEEDS_CAP" in violations and "OVERTIME_OUTLIER" not in types_list:
                    types_list.append("OVERTIME_OUTLIER")
                if not types_list:
                    types_list = ["STATISTICAL_ANOMALY"]
            else:
                types_list = ["NONE"]

            # Generate DetailedEvidenceCard
            card = explainer.explain(
                record=row,
                risk_score=r_score,
                predicted_anomaly_types=types_list,
                rule_violations=violations,
            )

            results.append((row, r_score, types_list, violations, card))

        return results
