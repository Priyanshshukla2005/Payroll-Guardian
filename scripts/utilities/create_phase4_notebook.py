"""Script to generate and execute notebooks/04_hardening_and_generalization.ipynb."""

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


def create_phase4_notebook(notebook_path: Path):
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
    cells.append(md_cell("""# 🛡️ AI Payroll Guardian — Model Hardening, Generalization & Hybrid Detection (Phase 4)
**Project**: AI Payroll Guardian  
**Phase**: Phase 4 — Model Hardening, Hard-Case Benchmarking & Generalization  
**Goal**: Address subtle statutory errors, cold-start blind spots, and camouflaged anomalies using a **Hybrid Architecture (ML + Deterministic Rules + Robust Statistical Signals)**.

---
### 📌 Scope of Analysis
1. **Frozen Phase 3 Baseline vs Version 2 Architecture**
2. **Hard-Case Challenge Benchmark (Subtle PF/ESI, Cold Start, Compound, Camouflaged)**
3. **Detection Sensitivity across Anomaly Magnitudes & Tenure Brackets**
4. **Cross-Company Generalization (Shifted Fintech Archetype)**
5. **Feature Group Ablation Study**
6. **Probability Calibration & Reliability Curves**
7. **Enhanced Structured Evidence Signals (V2 Explainer)**
8. **Final Architectural Decision & Production Recommendations**"""))

    # Section 1
    cells.append(md_cell("""## 1. Ingest Hard-Case Suite & Frozen Baseline Reference"""))

    cells.append(code_cell("""import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 10

ROOT_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SYNTHETIC_DIR = ROOT_DIR / "data" / "synthetic"
MODELS_V1_DIR = ROOT_DIR / "models" / "v1"
MODELS_V2_DIR = ROOT_DIR / "models" / "v2"
EXPERIMENTS_DIR = ROOT_DIR / "experiments"

import json
with open(EXPERIMENTS_DIR / "baseline_v1.json", "r") as f:
    baseline_v1 = json.load(f)

print(f"Frozen V1 Model: {baseline_v1['model_name']} | Frozen Test F1: {baseline_v1['test_f1']*100:.2f}% | FP/1k: {baseline_v1['test_unique_employee_fp_per_1000']:.1f}")

hard_df = pd.read_parquet(SYNTHETIC_DIR / "hard_cases_payroll.parquet")
print(f"Loaded Hard-Case Suite: {len(hard_df):,} records across {hard_df['challenge_category'].nunique()} challenge categories.")
"""))

    # Section 2
    cells.append(md_cell("""## 2. Hard-Case Challenge Categories Breakdown"""))

    cells.append(code_cell("""cat_counts = hard_df["challenge_category"].value_counts()
display(cat_counts.to_frame("Record Count"))

plt.figure(figsize=(10, 5))
cat_counts.plot(kind="barh", color="#1971c2")
plt.title("Hard-Case Challenge Scenarios Distribution", fontweight="bold")
plt.xlabel("Record Count")
plt.tight_layout()
plt.show()
"""))

    # Section 3
    cells.append(md_cell("""## 3. Head-to-Head Comparison: Phase 3 V1 vs Phase 4 V2 (Hard Cases)"""))

    cells.append(code_cell("""with open(MODELS_V2_DIR / "phase4_hardening_report.json", "r") as f:
    p4_report = json.load(f)

hard_comp = pd.DataFrame([
    {"Model": "RandomForest_V1 (Phase 3)", "Overall Recall": f"{p4_report['hard_cases_comparison']['v1_rf_recall']*100:.1f}%", "Subtle Statutory Recall": f"{p4_report['hard_cases_comparison']['subtle_statutory_v1_rec']*100:.1f}%", "Cold-Start Recall": f"{p4_report['hard_cases_comparison']['cold_start_v1_rec']*100:.1f}%"},
    {"Model": "Hybrid_V2 (Phase 4)", "Overall Recall": f"{p4_report['hard_cases_comparison']['v2_hybrid_recall']*100:.1f}%", "Subtle Statutory Recall": f"{p4_report['hard_cases_comparison']['subtle_statutory_v2_rec']*100:.1f}%", "Cold-Start Recall": f"{p4_report['hard_cases_comparison']['cold_start_v2_rec']*100:.1f}%"}
])
display(hard_comp)

fig, ax = plt.subplots(figsize=(8, 5))
rec_df = pd.DataFrame({
    "V1 RandomForest": [p4_report['hard_cases_comparison']['v1_rf_recall']*100, p4_report['hard_cases_comparison']['subtle_statutory_v1_rec']*100, p4_report['hard_cases_comparison']['cold_start_v1_rec']*100],
    "V2 Hybrid": [p4_report['hard_cases_comparison']['v2_hybrid_recall']*100, p4_report['hard_cases_comparison']['subtle_statutory_v2_rec']*100, p4_report['hard_cases_comparison']['cold_start_v2_rec']*100],
}, index=["Overall Hard Cases", "Subtle Statutory (PF/ESI)", "Cold-Start Employees"])

rec_df.plot(kind="bar", ax=ax, color=["#868e96", "#2f9e44"])
plt.title("Detection Recall: Phase 3 V1 vs Phase 4 V2 Hybrid", fontweight="bold")
plt.ylabel("Recall (%)")
plt.ylim(0, 115)
plt.xticks(rotation=0)
plt.legend(loc="upper left")
plt.tight_layout()
plt.show()
"""))

    # Section 4
    cells.append(md_cell("""## 4. Feature Group Ablation Study Results"""))

    cells.append(code_cell("""ablation_data = p4_report["ablation_results"]
ab_df = pd.DataFrame(ablation_data).T
ab_df["f1_score"] = ab_df["f1_score"] * 100
ab_df["recall"] = ab_df["recall"] * 100
ab_df["precision"] = ab_df["precision"] * 100
display(ab_df.round(2))

plt.figure(figsize=(10, 5))
ab_df["f1_score"].sort_values().plot(kind="barh", color="#e03131")
plt.title("Validation F1 Score under Feature Ablation", fontweight="bold")
plt.xlabel("Validation F1 Score (%)")
plt.tight_layout()
plt.show()
"""))

    # Section 5
    cells.append(md_cell("""## 5. Cross-Company Generalization Analysis (Shifted Fintech Archetype)"""))

    cells.append(code_cell("""gen_df = pd.DataFrame([
    {"Model": "RandomForest_V1", "Shifted Company F1": f"{p4_report['cross_company_generalization']['v1_rf_f1']*100:.2f}%"},
    {"Model": "Hybrid_V2", "Shifted Company F1": f"{p4_report['cross_company_generalization']['v2_hybrid_f1']*100:.2f}%"}
])
display(gen_df)
"""))

    # Section 6
    cells.append(md_cell("""## 6. Structured Evidence Card Example (Explainer V2)"""))

    cells.append(code_cell("""with open(MODELS_V2_DIR / "sample_evidence_v2.json", "r") as f:
    sample_evidence = json.load(f)

print(json.dumps(sample_evidence, indent=2))
"""))

    # Section 7
    cells.append(md_cell("""## 7. Final Model Decision & Phase 5 Transition"""))

    cells.append(code_cell("""print(f"FINAL DECISION: {p4_report['final_decision']}")
print(f"RATIONALE     : {p4_report['decision_rationale']}")
"""))

    notebook_dict = {
        "cells": cells,
        "metadata": {
            "language_info": {"name": "python"}
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
    nb_path = Path("notebooks/04_hardening_and_generalization.ipynb")
    create_phase4_notebook(nb_path)
    execute_notebook(nb_path)
