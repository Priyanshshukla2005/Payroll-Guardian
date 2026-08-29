"""Script to generate and execute notebooks/03_model_training_and_comparison.ipynb."""

import base64
import io
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def create_comparison_notebook(notebook_path: Path):
    cells = []

    def md_cell(source: str):
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in source.split("\n")],
        }

    def code_cell(source: str):
        return {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in source.split("\n")],
        }

    # Title
    cells.append(md_cell("""# 🤖 AI Payroll Guardian — Model Training, Evaluation & Comparison (Phase 3)
**Project**: AI Payroll Guardian  
**Phase**: Phase 3 — Tabular ML Model Training & Multi-Label Anomaly Classification  
**Goal**: Train, evaluate, and benchmark dedicated ML models (Isolation Forest, Random Forest, XGBoost, Autoencoder) against the non-ML deterministic rule baseline.

---
### 📌 Scope of Analysis
1. **Model Training & Validation Setup (Strict Zero Leakage)**
2. **Deterministic Baseline vs ML Models Comparison**
3. **Threshold Optimization & PR Curves**
4. **Confusion Matrices & False Positive Analysis**
5. **Unique Employee FP/1,000 Business Metric**
6. **Feature Importance & Model Explainability**
7. **Task B: Multi-Label Anomaly Type Classification**
8. **Error Analysis (Root Cause of False Alarms & Missed Detections)**
9. **Final Model Selection & Test Set Verification**"""))

    # Section 1
    cells.append(md_cell("""## 1. Environment & Ingestion of ML Partitions"""))

    cells.append(code_cell("""import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_curve, average_precision_score, roc_auc_score

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 10

ROOT_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MODELS_DIR = ROOT_DIR / "models"

X_train = pd.read_parquet(PROCESSED_DIR / "X_train.parquet")
y_train = pd.read_parquet(PROCESSED_DIR / "y_train.parquet")["is_anomaly"]
meta_train = pd.read_parquet(PROCESSED_DIR / "train_metadata.parquet")

X_val = pd.read_parquet(PROCESSED_DIR / "X_val.parquet")
y_val = pd.read_parquet(PROCESSED_DIR / "y_val.parquet")["is_anomaly"]
meta_val = pd.read_parquet(PROCESSED_DIR / "val_metadata.parquet")

X_test = pd.read_parquet(PROCESSED_DIR / "X_test.parquet")
y_test = pd.read_parquet(PROCESSED_DIR / "y_test.parquet")["is_anomaly"]
meta_test = pd.read_parquet(PROCESSED_DIR / "test_metadata.parquet")

print(f"X_train Shape : {X_train.shape} | y_train Anomaly Rate : {y_train.mean()*100:.2f}%")
print(f"X_val Shape   : {X_val.shape}   | y_val Anomaly Rate   : {y_val.mean()*100:.2f}%")
print(f"X_test Shape  : {X_test.shape}  | y_test Anomaly Rate  : {y_test.mean()*100:.2f}%")
"""))

    # Section 2
    cells.append(md_cell("""## 2. Load Trained Model Artifacts & Compute Validation Probabilities"""))

    cells.append(code_cell("""from ai.detection.isolation_forest import IsolationForestDetector
from ai.detection.random_forest import RandomForestDetector
from ai.detection.xgboost_model import GradientBoostingDetector
from ai.detection.autoencoder import TabularAutoencoderDetector

iso_model = IsolationForestDetector.load(MODELS_DIR / "isolationforest.joblib")
rf_model = RandomForestDetector.load(MODELS_DIR / "randomforest.joblib")
xgb_model = GradientBoostingDetector.load(MODELS_DIR / "xgboost.joblib")
ae_model = TabularAutoencoderDetector.load(MODELS_DIR / "autoencoder.joblib")

models = {
    "Isolation Forest": (iso_model, iso_model.optimal_threshold),
    "Random Forest": (rf_model, rf_model.optimal_threshold),
    "XGBoost": (xgb_model, xgb_model.optimal_threshold),
    "Autoencoder": (ae_model, ae_model.optimal_threshold)
}

val_preds = {}
val_probs = {}

for name, (m, thresh) in models.items():
    p = m.predict_proba(X_val)[:, 1]
    val_probs[name] = p
    val_preds[name] = (p >= thresh).astype(int)
    print(f"Loaded {name:<18} | Optimal Threshold: {thresh:.2f}")
"""))

    # Section 3
    cells.append(md_cell("""## 3. Precision-Recall & ROC Curves (Validation Set)"""))

    cells.append(code_cell("""fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# PR Curves
for name, prob in val_probs.items():
    prec, rec, _ = precision_recall_curve(y_val, prob)
    pr_auc = average_precision_score(y_val, prob)
    axes[0].plot(rec, prec, label=f"{name} (PR-AUC = {pr_auc:.4f})", lw=2)

axes[0].set_title("Precision-Recall Curves (Validation Set)", fontsize=13, fontweight="bold")
axes[0].set_xlabel("Recall")
axes[0].set_ylabel("Precision")
axes[0].set_ylim(-0.05, 1.05)
axes[0].legend(loc="lower left")

# ROC Curves
for name, prob in val_probs.items():
    fpr, tpr, _ = roc_curve(y_val, prob)
    roc_auc = roc_auc_score(y_val, prob)
    axes[1].plot(fpr, tpr, label=f"{name} (ROC-AUC = {roc_auc:.4f})", lw=2)

axes[1].plot([0, 1], [0, 1], "k--", lw=1)
axes[1].set_title("ROC Curves (Validation Set)", fontsize=13, fontweight="bold")
axes[1].set_xlabel("False Positive Rate")
axes[1].set_ylabel("True Positive Rate")
axes[1].legend(loc="lower right")

plt.tight_layout()
plt.show()
"""))

    # Section 4
    cells.append(md_cell("""## 4. Confusion Matrices (Validation Set)"""))

    cells.append(code_cell("""fig, axes = plt.subplots(1, 4, figsize=(20, 4))

for idx, (name, pred) in enumerate(val_preds.items()):
    cm = confusion_matrix(y_val, pred, labels=[0, 1])
    sns.heatmap(cm, annot=True, fmt=",d", cmap="Blues", cbar=False, ax=axes[idx],
                xticklabels=["Pred Norm", "Pred Anom"], yticklabels=["True Norm", "True Anom"])
    axes[idx].set_title(name, fontweight="bold")

plt.tight_layout()
plt.show()
"""))

    # Section 5
    cells.append(md_cell("""## 5. Feature Importance Analysis (Random Forest & XGBoost)"""))

    cells.append(code_cell("""rf_importances = rf_model.get_feature_importances()
top_rf = pd.Series(rf_importances).head(15)

xgb_importances = xgb_model.get_feature_importances()
top_xgb = pd.Series(xgb_importances).head(15)

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

top_rf.sort_values().plot(kind="barh", ax=axes[0], color="#1971c2")
axes[0].set_title("Top 15 Features — Random Forest", fontweight="bold")
axes[0].set_xlabel("Relative Importance")

top_xgb.sort_values().plot(kind="barh", ax=axes[1], color="#2f9e44")
axes[1].set_title("Top 15 Features — XGBoost", fontweight="bold")
axes[1].set_xlabel("Relative Importance")

plt.tight_layout()
plt.show()
"""))

    # Section 6
    cells.append(md_cell("""## 6. Multi-Label Anomaly Type Classifier Performance"""))

    cells.append(code_cell("""from ai.detection.type_classifier import MultiLabelAnomalyTypeClassifier

type_clf = MultiLabelAnomalyTypeClassifier.load(MODELS_DIR / "type_classifier.joblib")
type_results = type_clf.evaluate(X_test, meta_test["anomaly_type"], threshold=0.40)

type_df = pd.DataFrame(type_results["per_type_metrics"]).T
display(type_df)

fig, ax = plt.subplots(figsize=(12, 6))
type_df[["precision", "recall", "f1_score"]].plot(kind="bar", ax=ax, colormap="tab10")
plt.title("Multi-Label Anomaly Type Classification Performance (Test Set)", fontweight="bold")
plt.ylabel("Score")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()
"""))

    # Section 7
    cells.append(md_cell("""## 7. Error Analysis: False Positives & False Negatives"""))

    cells.append(code_cell("""best_pred = rf_model.predict(X_test, threshold=rf_model.optimal_threshold)

fp_mask = (best_pred == 1) & (y_test.values == 0)
fn_mask = (best_pred == 0) & (y_test.values == 1)

print(f"Total False Positives on Test Set : {fp_mask.sum()} / {len(y_test):,} records")
print(f"Total False Negatives on Test Set : {fn_mask.sum()} / {len(y_test):,} records")

if fp_mask.sum() > 0:
    print("False Positive Records Sample:")
    display(meta_test[fp_mask].head(5))

if fn_mask.sum() > 0:
    print("False Negative Records Sample (Missed Anomaly Types):")
    display(meta_test[fn_mask]["anomaly_type"].value_counts().head(5))
"""))

    # Section 8
    cells.append(md_cell("""## 8. Final Model Selection & Unbiased Test Set Summary"""))

    cells.append(code_cell("""import json

with open(MODELS_DIR / "model_config.json", "r") as f:
    config = json.load(f)

summary_df = pd.DataFrame([config])
display(summary_df.T.rename(columns={0: "Final Test Benchmark"}))
"""))

    notebook_dict = {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2,
    }

    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(notebook_dict, f, indent=2)
    print(f"Created notebook at {notebook_path}")


def execute_notebook(nb_path: Path):
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    exec_globals = {
        "__name__": "__main__",
        "Path": Path,
        "pd": pd,
        "np": np,
        "plt": plt,
    }

    print(f"Executing {nb_path}...")
    exec_count = 1

    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue

        code_text = "".join(cell.get("source", []))
        cell_outputs = []
        old_stdout = io.StringIO()
        real_stdout = sys.stdout
        sys.stdout = old_stdout

        def custom_display(obj):
            if isinstance(obj, (pd.DataFrame, pd.Series)):
                text_repr = obj.to_string()
                html_repr = obj.to_html() if hasattr(obj, "to_html") else f"<pre>{text_repr}</pre>"
                cell_outputs.append({
                    "data": {"text/plain": text_repr, "text/html": html_repr},
                    "metadata": {},
                    "output_type": "display_data"
                })
            else:
                cell_outputs.append({
                    "data": {"text/plain": str(obj)},
                    "metadata": {},
                    "output_type": "display_data"
                })

        exec_globals["display"] = custom_display

        try:
            plt.clf()
            plt.close("all")
            exec(code_text, exec_globals)
            sys.stdout = real_stdout

            stdout_str = old_stdout.getvalue()
            if stdout_str:
                cell_outputs.insert(0, {
                    "name": "stdout",
                    "output_type": "stream",
                    "text": [line + "\n" for line in stdout_str.split("\n") if line]
                })

            figs = [plt.figure(n) for n in plt.get_fignums()]
            for fig in figs:
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
                buf.seek(0)
                img_b64 = base64.b64encode(buf.read()).decode("utf-8")
                cell_outputs.append({
                    "data": {"image/png": img_b64, "text/plain": "<Figure size ...>"},
                    "metadata": {},
                    "output_type": "display_data"
                })
                plt.close(fig)

            cell["execution_count"] = exec_count
            cell["outputs"] = cell_outputs
            print(f"  [Cell {i+1}] Executed successfully ({len(cell_outputs)} outputs).")
            exec_count += 1

        except Exception as e:
            sys.stdout = real_stdout
            print(f"  [Cell {i+1}] ERROR during execution: {e}")
            cell["execution_count"] = exec_count
            cell["outputs"] = [{
                "ename": type(e).__name__,
                "evalue": str(e),
                "output_type": "error",
                "traceback": [f"{type(e).__name__}: {str(e)}"]
            }]
            exec_count += 1

    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)

    print(f"\nExecution complete: {nb_path}")


if __name__ == "__main__":
    nb_path = Path("notebooks/03_model_training_and_comparison.ipynb")
    create_comparison_notebook(nb_path)
    execute_notebook(nb_path)
