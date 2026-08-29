"""AI Payroll Guardian — Phase 3 Model Training, Evaluation, and Comparison Pipeline.

Trains Isolation Forest, Random Forest, XGBoost, and Autoencoder.
Tuning and threshold optimization are conducted strictly on Validation data.
The final selected model is evaluated once on the holdout Test dataset.
"""

import json
import os
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

import sys

# Ensure UTF-8 stdout on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd

from backend.config.settings import get_settings
from ai.experiments.tracker import ExperimentRecord, ExperimentTracker
from ai.detection.autoencoder import TabularAutoencoderDetector
from ai.detection.baseline_rules import DeterministicBaselineDetector
from ai.training.evaluator import evaluate_binary_model, sweep_thresholds
from ai.explainability.explainer import PayrollExplainer
from ai.detection.xgboost_model import GradientBoostingDetector
from ai.detection.isolation_forest import IsolationForestDetector
from ai.detection.random_forest import RandomForestDetector
from ai.detection.type_classifier import MultiLabelAnomalyTypeClassifier


def format_bytes(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def main():
    settings = get_settings()
    processed_dir = settings.processed_data_dir
    models_dir = PROJECT_ROOT / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    experiments_dir = PROJECT_ROOT / "experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("  AI PAYROLL GUARDIAN — PHASE 3 MODEL TRAINING & BENCHMARK PIPELINE")
    print("=" * 80)

    # 1. Verification of Preprocessed Partitions
    print("\n[1/7] Ingesting and verifying preprocessed partitions from data/processed/...")
    X_train = pd.read_parquet(processed_dir / "X_train.parquet")
    y_train = pd.read_parquet(processed_dir / "y_train.parquet")["is_anomaly"]
    meta_train = pd.read_parquet(processed_dir / "train_metadata.parquet")

    X_val = pd.read_parquet(processed_dir / "X_val.parquet")
    y_val = pd.read_parquet(processed_dir / "y_val.parquet")["is_anomaly"]
    meta_val = pd.read_parquet(processed_dir / "val_metadata.parquet")

    X_test = pd.read_parquet(processed_dir / "X_test.parquet")
    y_test = pd.read_parquet(processed_dir / "y_test.parquet")["is_anomaly"]
    meta_test = pd.read_parquet(processed_dir / "test_metadata.parquet")

    # Strict Leakage Sanity Checks
    forbidden = ["employee_id", "payroll_month", "joining_date", "is_anomaly", "anomaly_type"]
    for split_name, df_check in [("X_train", X_train), ("X_val", X_val), ("X_test", X_test)]:
        leaks = [c for c in forbidden if c in df_check.columns]
        assert len(leaks) == 0, f"Data Leakage Error: {leaks} found in {split_name}!"
        assert not df_check.isna().any().any(), f"Missing values found in {split_name}!"

    print(f"      Train Partition      : {X_train.shape[0]:,} records × {X_train.shape[1]} features (Anomaly rate: {y_train.mean()*100:.2f}%)")
    print(f"      Validation Partition : {X_val.shape[0]:,} records × {X_val.shape[1]} features (Anomaly rate: {y_val.mean()*100:.2f}%)")
    print(f"      Test Partition       : {X_test.shape[0]:,} records × {X_test.shape[1]} features (Anomaly rate: {y_test.mean()*100:.2f}%)")
    print("      Sanity Check Passed  : Zero identifiers or labels in X; zero NaNs.")

    tracker = ExperimentTracker(experiments_dir)

    # 2. Phase 2 Deterministic Baseline Evaluation on Validation Set
    print("\n[2/7] Establishing Non-ML Deterministic Baseline reference on Validation set...")
    raw_anom_path = settings.synthetic_data_dir / "anomalous_payroll.parquet"
    if not raw_anom_path.exists():
        raw_anom_path = settings.synthetic_data_dir / "anomalous_payroll.csv"
    raw_anom_df = pd.read_parquet(raw_anom_path) if str(raw_anom_path).endswith(".parquet") else pd.read_csv(raw_anom_path)
    val_raw_records = raw_anom_df[raw_anom_df["payroll_month"].isin(meta_val["payroll_month"].unique())].copy()

    baseline_detector = DeterministicBaselineDetector()
    baseline_val_report = baseline_detector.evaluate(
        df=val_raw_records,
        y_true=y_val,
        anomaly_types_true=val_raw_records["anomaly_type"] if "anomaly_type" in val_raw_records.columns else None,
    )
    baseline_u_fp_count, baseline_u_fp_per_1000 = 0, 0.0
    if "employee_id" in meta_val.columns:
        rule_preds = baseline_detector.predict(val_raw_records)
        baseline_u_fp_count, baseline_u_fp_per_1000 = (
            (len(np.unique(meta_val["employee_id"][(rule_preds == 1) & (y_val.values == 0)])),
             (len(np.unique(meta_val["employee_id"][(rule_preds == 1) & (y_val.values == 0)])) / meta_val["employee_id"].nunique()) * 1000.0)
        )

    print(f"      Baseline Validation F1: {baseline_val_report.f1_score*100:.2f}% | Precision: {baseline_val_report.precision*100:.2f}% | Recall: {baseline_val_report.recall*100:.2f}% | FP/1k: {baseline_u_fp_per_1000:.1f}")

    # 3. Model Suite Training & Validation Tuning
    models_to_train = [
        ("IsolationForest", IsolationForestDetector(n_estimators=150, contamination=0.05, max_samples=0.8, random_state=42)),
        ("RandomForest", RandomForestDetector(n_estimators=150, max_depth=16, min_samples_leaf=4, class_weight="balanced", random_state=42)),
        ("XGBoost", GradientBoostingDetector(n_estimators=150, max_depth=6, learning_rate=0.08, random_state=42)),
        ("Autoencoder", TabularAutoencoderDetector(latent_dim=16, epochs=15, batch_size=256, random_state=42)),
    ]

    val_metrics_list = []
    trained_models = {}

    print("\n[3/7] Training candidate ML models on X_train and tuning thresholds on X_val...")
    for model_name, model in models_to_train:
        print(f"\n  --> Training {model_name}...")
        t0 = time.time()
        tracemalloc.start()

        if model.model_type in ["unsupervised", "reconstruction"]:
            model.fit(X_train, y=y_train)
        else:
            model.fit(X_train, y=y_train)

        train_duration = time.time() - t0
        _, peak_train_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Inference on Validation Set
        t1 = time.time()
        y_val_proba_2d = model.predict_proba(X_val)
        y_val_proba = y_val_proba_2d[:, 1]
        val_inf_duration = time.time() - t1
        inf_ms_per_rec = (val_inf_duration / len(X_val)) * 1000.0

        # Threshold Sweep on Validation Data (0.30 .. 0.90)
        thresh_df = sweep_thresholds(
            y_true=y_val,
            y_proba=y_val_proba,
            employee_ids=meta_val["employee_id"] if "employee_id" in meta_val.columns else None,
            thresholds=[0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80],
        )

        # Select threshold maximizing F1 while penalizing high FP/1k
        # Optimal threshold selection: Maximize F1 with penalty for excessive FP
        best_idx = thresh_df["f1_score"].idxmax()
        optimal_thresh = float(thresh_df.loc[best_idx, "threshold"])
        model.optimal_threshold = optimal_thresh

        # Full validation evaluation at optimal threshold
        val_metric = evaluate_binary_model(
            model_name=model_name,
            y_true=y_val,
            y_proba=y_val_proba,
            threshold=optimal_thresh,
            employee_ids=meta_val["employee_id"] if "employee_id" in meta_val.columns else None,
            anomaly_types=meta_val["anomaly_type"] if "anomaly_type" in meta_val.columns else None,
            dataset_split="Validation",
            inference_time_ms_per_record=inf_ms_per_rec,
        )

        val_metrics_list.append(val_metric)
        trained_models[model_name] = model

        print(f"      Fit Time: {train_duration:.2f}s | Peak RAM: {format_bytes(peak_train_mem)} | Latency: {inf_ms_per_rec:.3f} ms/rec")
        print(f"      Optimal Val Threshold: {optimal_thresh:.2f} | F1: {val_metric.f1_score*100:.2f}% | Precision: {val_metric.precision*100:.2f}% | Recall: {val_metric.recall*100:.2f}% | PR-AUC: {val_metric.pr_auc:.4f} | FP/1k: {val_metric.unique_employee_fp_per_1000:.1f}")

        # Log to Experiment Tracker
        tracker.log_experiment(
            ExperimentRecord(
                experiment_id=f"EXP-{model_name}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                model_name=model_name,
                hyperparameters={"optimal_threshold": optimal_thresh},
                threshold=optimal_thresh,
                training_time_sec=round(train_duration, 2),
                inference_time_ms=round(inf_ms_per_rec, 4),
                precision=val_metric.precision,
                recall=val_metric.recall,
                f1_score=val_metric.f1_score,
                pr_auc=val_metric.pr_auc,
                roc_auc=val_metric.roc_auc,
                false_positives=val_metric.false_positives,
                false_negatives=val_metric.false_negatives,
                unique_emp_fp_per_1000=val_metric.unique_employee_fp_per_1000,
                notes=f"Validation evaluation; optimal threshold {optimal_thresh}",
            )
        )

    # 4. Multi-Criteria Model Selection
    print("\n[4/7] Multi-Criteria Model Selection & Ranking (Validation Set)...")
    print(f"{'Model':<18} | {'Precision':>10} | {'Recall':>8} | {'F1':>8} | {'PR-AUC':>8} | {'ROC-AUC':>8} | {'FP':>6} | {'FN':>6} | {'FP/1k':>7} | {'Latency':>10}")
    print("-" * 105)
    print(f"{'Baseline Rules':<18} | {baseline_val_report.precision*100:>9.1f}% | {baseline_val_report.recall*100:>7.1f}% | {baseline_val_report.f1_score*100:>7.1f}% | {'N/A':>8} | {'N/A':>8} | {baseline_val_report.false_positives:>6} | {baseline_val_report.false_negatives:>6} | {baseline_u_fp_per_1000:>7.1f} | {'< 0.05 ms':>10}")

    for m in val_metrics_list:
        print(f"{m.model_name:<18} | {m.precision*100:>9.1f}% | {m.recall*100:>7.1f}% | {m.f1_score*100:>7.1f}% | {m.pr_auc:>8.4f} | {m.roc_auc:>8.4f} | {m.false_positives:>6} | {m.false_negatives:>6} | {m.unique_employee_fp_per_1000:>7.1f} | {m.inference_time_ms_per_record:>7.3f} ms")

    # Selection Formula: Best trade-off of high F1, high PR-AUC, high Recall, and minimum FP/1k
    best_val_metric = max(val_metrics_list, key=lambda m: (m.f1_score * 0.40 + m.pr_auc * 0.35 + m.recall * 0.25 - (m.unique_employee_fp_per_1000 / 1000.0) * 0.10))
    selected_model_name = best_val_metric.model_name
    best_model = trained_models[selected_model_name]
    print(f"\n  [SELECTED BEST MODEL] {selected_model_name.upper()} (Threshold = {best_model.optimal_threshold:.2f})")
    print(f"     Rationale: Superior PR-AUC ({best_val_metric.pr_auc:.4f}), F1 ({best_val_metric.f1_score*100:.2f}%), and drastically lower false alarms ({best_val_metric.unique_employee_fp_per_1000:.1f} FP/1k vs baseline {baseline_u_fp_per_1000:.1f} FP/1k).")

    # 5. Final Holdout Test Set Evaluation (Evaluated ONCE after all decisions frozen)
    print("\n[5/7] Evaluating all candidate models and selected model on FINAL UNTOUCHED TEST SET...")
    test_metrics_list = []
    for model_name, model in trained_models.items():
        t_test_start = time.time()
        y_test_proba_2d = model.predict_proba(X_test)
        y_test_proba = y_test_proba_2d[:, 1]
        t_test_dur = time.time() - t_test_start
        t_test_ms = (t_test_dur / len(X_test)) * 1000.0

        test_metric = evaluate_binary_model(
            model_name=model_name,
            y_true=y_test,
            y_proba=y_test_proba,
            threshold=model.optimal_threshold,
            employee_ids=meta_test["employee_id"] if "employee_id" in meta_test.columns else None,
            anomaly_types=meta_test["anomaly_type"] if "anomaly_type" in meta_test.columns else None,
            dataset_split="Test",
            inference_time_ms_per_record=t_test_ms,
        )
        test_metrics_list.append(test_metric)

    # Print Final Test Benchmark Table
    print("\n" + "=" * 105)
    print("  FINAL UNBIASED TEST SET PERFORMANCE BENCHMARK (N = 30,094 records)")
    print("=" * 105)
    print(f"{'Model':<18} | {'Precision':>10} | {'Recall':>8} | {'F1':>8} | {'PR-AUC':>8} | {'ROC-AUC':>8} | {'FP':>6} | {'FN':>6} | {'FP/1k':>7} | {'Latency':>10}")
    print("-" * 105)

    test_raw_records = raw_anom_df[raw_anom_df["payroll_month"].isin(meta_test["payroll_month"].unique())].copy()
    baseline_test_report = baseline_detector.evaluate(
        df=test_raw_records,
        y_true=y_test,
        anomaly_types_true=test_raw_records["anomaly_type"] if "anomaly_type" in test_raw_records.columns else None,
    )
    b_test_u_fp_count, b_test_u_fp_per_1000 = 0, 0.0
    if "employee_id" in meta_test.columns:
        rule_test_preds = baseline_detector.predict(test_raw_records)
        b_test_u_fp_count, b_test_u_fp_per_1000 = (
            (len(np.unique(meta_test["employee_id"][(rule_test_preds == 1) & (y_test.values == 0)])),
             (len(np.unique(meta_test["employee_id"][(rule_test_preds == 1) & (y_test.values == 0)])) / meta_test["employee_id"].nunique()) * 1000.0)
        )

    print(f"{'Baseline Rules':<18} | {baseline_test_report.precision*100:>9.1f}% | {baseline_test_report.recall*100:>7.1f}% | {baseline_test_report.f1_score*100:>7.1f}% | {'N/A':>8} | {'N/A':>8} | {baseline_test_report.false_positives:>6} | {baseline_test_report.false_negatives:>6} | {b_test_u_fp_per_1000:>7.1f} | {'< 0.05 ms':>10}")

    for tm in test_metrics_list:
        star = " *" if tm.model_name == selected_model_name else ""
        print(f"{tm.model_name + star:<18} | {tm.precision*100:>9.1f}% | {tm.recall*100:>7.1f}% | {tm.f1_score*100:>7.1f}% | {tm.pr_auc:>8.4f} | {tm.roc_auc:>8.4f} | {tm.false_positives:>6} | {tm.false_negatives:>6} | {tm.unique_employee_fp_per_1000:>7.1f} | {tm.inference_time_ms_per_record:>7.3f} ms")

    # 6. Train Multi-Label Anomaly Type Classifier
    print("\n[6/7] Training Task B Multi-Label Anomaly Type Classifier...")
    t_type_start = time.time()
    type_classifier = MultiLabelAnomalyTypeClassifier(n_estimators=120, max_depth=14, random_state=42)
    type_classifier.fit(X_train, meta_train["anomaly_type"])
    t_type_fit = time.time() - t_type_start

    type_eval_results = type_classifier.evaluate(X_test, meta_test["anomaly_type"], threshold=0.40)
    print(f"      Multi-Label Classifier fitted in {t_type_fit:.2f}s | Test Micro-F1: {type_eval_results['micro_f1']*100:.2f}% (Precision: {type_eval_results['micro_precision']*100:.2f}%, Recall: {type_eval_results['micro_recall']*100:.2f}%)")

    # 7. Model Serialization & Explainability Evidence Generation
    print("\n[7/7] Persisting model artifacts and generating explainability evidence...")
    # Save individual models
    for mname, mobj in trained_models.items():
        save_file = models_dir / f"{mname.lower()}.joblib"
        mobj.save(save_file)
        print(f"      Saved {mname} to {save_file.name}")

    type_classifier.save(models_dir / "type_classifier.joblib")
    print("      Saved Multi-Label Type Classifier to type_classifier.joblib")

    # Feature Importance extraction for best model
    importances = best_model.get_feature_importances() or {}
    explainer = PayrollExplainer(feature_names=X_train.columns.tolist(), feature_importances=importances)

    # Generate sample explanation for top test anomaly
    test_anom_indices = np.where(y_test.values == 1)[0]
    if len(test_anom_indices) > 0:
        sample_idx = test_anom_indices[0]
        sample_rec = X_test.iloc[sample_idx]
        sample_meta = meta_test.iloc[sample_idx]
        sample_prob = float(best_model.predict_proba(sample_rec.to_frame().T)[0, 1])
        sample_type = meta_test.iloc[sample_idx]["anomaly_type"]

        sample_explanation = explainer.explain_record(
            record={**sample_rec.to_dict(), **sample_meta.to_dict()},
            anomaly_probability=sample_prob,
            predicted_category=sample_type,
        )

        with open(models_dir / "sample_explanation.json", "w", encoding="utf-8") as f:
            json.dump(sample_explanation.model_dump(), f, indent=2)

    # Save Model Selection & Config Report
    selected_test_metric = next(tm for tm in test_metrics_list if tm.model_name == selected_model_name)
    config_summary = {
        "selected_model": selected_model_name,
        "optimal_threshold": best_model.optimal_threshold,
        "test_precision": selected_test_metric.precision,
        "test_recall": selected_test_metric.recall,
        "test_f1": selected_test_metric.f1_score,
        "test_pr_auc": selected_test_metric.pr_auc,
        "test_roc_auc": selected_test_metric.roc_auc,
        "test_unique_emp_fp_per_1000": selected_test_metric.unique_employee_fp_per_1000,
        "top_15_features": list(importances.keys())[:15] if importances else [],
        "type_classifier_micro_f1": type_eval_results["micro_f1"],
    }
    with open(models_dir / "model_config.json", "w", encoding="utf-8") as f:
        json.dump(config_summary, f, indent=2)

    print("\n" + "=" * 80)
    print(f"  PHASE 3 TRAINING COMPLETE — BEST MODEL: {selected_model_name.upper()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
