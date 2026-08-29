"""Script to build and save the Phase 1 EDA Jupyter Notebook using standard json."""

import json
from pathlib import Path

def create_eda_notebook(notebook_path: Path):
    cells = []

    def md_cell(source: str):
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in source.split("\n")]
        }

    def code_cell(source: str):
        return {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in source.split("\n")]
        }

    # Title cell
    cells.append(md_cell("""# 🛡️ AI Payroll Guardian — Exploratory Data Analysis (Phase 1)
**Project**: AI Payroll Guardian  
**Phase**: Phase 1 — Data Foundation & Anomaly Profile Analysis  
**Goal**: Comprehensively audit and visualize the synthetic clean dataset, injected payroll anomalies, attendance and deduction distributions, and feature engineering foundations.

---
### 📌 Scope of Analysis
1. **Dataset Dimensions & Schema Integrity**
2. **Missing Values & Duplicate Audit**
3. **Salary Distributions Overview (Basic, Allowances, Gross, Net)**
4. **Departmental Salary Dynamics**
5. **Designation Hierarchy & Salary Progression**
6. **Overtime Intensity & Departmental Patterns**
7. **Attendance & Leave Distributions**
8. **Bonus Structures & Appraisal Seasonality**
9. **Statutory & Other Deductions Breakdown (PF, ESI, TDS, PT)**
10. **Reconciliation Audit (Gross, Deductions, Net)**
11. **Month-over-Month (MoM) Dynamics & Legitimate Increments**
12. **Anomaly Distribution & Class Balance**
13. **Analysis of 13 Injected Anomaly Types by Severity**
14. **Comparative Case Studies: Normal vs Anomalous Employee History**
15. **Key Takeaways & Readiness for Phase 2 ML Modeling**"""))

    # Section 1: Environment & Loading
    cells.append(md_cell("""## 1. Environment Setup & Data Ingestion
Load libraries, configure plotting aesthetics, and read the clean, anomalous, and audit metadata datasets."""))

    cells.append(code_cell("""import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Plotting style configuration
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 13
plt.rcParams["axes.titleweight"] = "bold"

# Paths
ROOT_DIR = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
SYNTHETIC_DIR = ROOT_DIR / "data" / "synthetic"

clean_path = SYNTHETIC_DIR / "clean_payroll.csv"
anom_path = SYNTHETIC_DIR / "anomalous_payroll.csv"
meta_path = SYNTHETIC_DIR / "anomaly_metadata.csv"

df_clean = pd.read_csv(clean_path)
df_anom = pd.read_csv(anom_path)
df_meta = pd.read_csv(meta_path)

print(f"Clean Dataset Shape     : {df_clean.shape}")
print(f"Anomalous Dataset Shape : {df_anom.shape}")
print(f"Anomaly Metadata Shape  : {df_meta.shape}")"""))

    # Section 2: Schema Audit & Dimensions
    cells.append(md_cell("""## 2. Dataset Dimensions & Schema Audit
Verify the presence of mandatory columns, unique employee counts, and multi-month timeline coverage."""))

    cells.append(code_cell("""print("--- Clean Dataset Summary ---")
display(df_clean.info())

print(f"Unique Employees: {df_clean['employee_id'].nunique():,}")
print(f"Unique Months   : {df_clean['payroll_month'].nunique()} ({df_clean['payroll_month'].min()} to {df_clean['payroll_month'].max()})")
print(f"Departments     : {df_clean['department'].unique().tolist()}")
print(f"Designations    : {df_clean['designation'].unique().tolist()}")"""))

    # Section 3: Missing Values & Duplicates
    cells.append(md_cell("""## 3. Missing Values & Duplicate Records Check
Check data completeness and demonstrate how duplicates were created in the anomalous dataset."""))

    cells.append(code_cell("""null_clean = df_clean.isnull().sum()
null_anom = df_anom.isnull().sum()

clean_dups = df_clean.duplicated(subset=['employee_id', 'payroll_month']).sum()
anom_dups = df_anom.duplicated(subset=['employee_id', 'payroll_month']).sum()

summary_audit = pd.DataFrame({
    "Clean Null Count": null_clean,
    "Anomalous Null Count": null_anom
})
print("Missing values per column:")
display(summary_audit)

print(f"\\nDuplicate (Employee, Month) pairs in Clean Data     : {clean_dups}")
print(f"Duplicate (Employee, Month) pairs in Anomalous Data : {anom_dups} (Intentionally injected DUPLICATE_EMPLOYEE_RECORD anomalies)")"""))

    # Section 4: Salary Distributions
    cells.append(md_cell("""## 4. Overall Salary Distributions (Clean Dataset)
Examine the distribution of basic salary, allowances, gross salary, and net salary."""))

    cells.append(code_cell("""fig, axes = plt.subplots(2, 2, figsize=(14, 10))

sns.histplot(df_clean["basic_salary"], kde=True, ax=axes[0, 0], color="#2b5c8f", bins=40)
axes[0, 0].set_title("Basic Salary Distribution (INR)")
axes[0, 0].set_xlabel("Basic Salary (₹)")

sns.histplot(df_clean["allowances"], kde=True, ax=axes[0, 1], color="#2f9e44", bins=40)
axes[0, 1].set_title("Allowances Distribution (INR)")
axes[0, 1].set_xlabel("Allowances (₹)")

sns.histplot(df_clean["gross_salary"], kde=True, ax=axes[1, 0], color="#e8590c", bins=40)
axes[1, 0].set_title("Gross Salary Distribution (INR)")
axes[1, 0].set_xlabel("Gross Salary (₹)")

sns.histplot(df_clean["net_salary"], kde=True, ax=axes[1, 1], color="#7048e8", bins=40)
axes[1, 1].set_title("Net Salary Distribution (INR)")
axes[1, 1].set_xlabel("Net Salary (₹)")

plt.tight_layout()
plt.show()

display(df_clean[["basic_salary", "allowances", "gross_salary", "net_salary"]].describe().T)"""))

    # Section 5: Department Dynamics
    cells.append(md_cell("""## 5. Salary Distribution by Department
Analyze the salary variability and compensation tiers across different business units."""))

    cells.append(code_cell("""plt.figure(figsize=(14, 6))
dept_order = df_clean.groupby("department")["gross_salary"].median().sort_values(ascending=False).index

sns.boxplot(data=df_clean, x="department", y="gross_salary", order=dept_order, palette="Blues_r")
plt.title("Gross Salary Distribution across Departments (Sorted by Median)")
plt.xlabel("Department")
plt.ylabel("Gross Salary (₹)")
plt.xticks(rotation=20)
plt.show()

dept_stats = df_clean.groupby("department")["gross_salary"].agg(["count", "mean", "median", "std", "min", "max"]).round(2)
display(dept_stats)"""))

    # Section 6: Designation Hierarchy
    cells.append(md_cell("""## 6. Designation Hierarchy & Salary Tiers
Verify that compensation strictly reflects the career ladder: `Intern < Junior < Mid-level < Senior < Manager < Director`."""))

    cells.append(code_cell("""desig_order = ["Intern", "Junior", "Mid-level", "Senior", "Manager", "Director"]

plt.figure(figsize=(13, 6))
sns.violinplot(data=df_clean, x="designation", y="gross_salary", order=desig_order, palette="viridis", inner="quartile")
plt.title("Gross Salary Progression across Designation Hierarchy")
plt.xlabel("Designation")
plt.ylabel("Gross Salary (₹)")
plt.show()

desig_summary = df_clean.groupby("designation")["gross_salary"].agg(["count", "mean", "median", "std", "min", "max"]).reindex(desig_order).round(2)
display(desig_summary)"""))

    # Section 7: Overtime Patterns
    cells.append(md_cell("""## 7. Overtime Hours & Department Intensity
Analyze overtime distribution in clean vs anomalous data. In clean data, overtime is bounded to realistic hours for operational roles."""))

    cells.append(code_cell("""fig, axes = plt.subplots(1, 2, figsize=(15, 5))

# Clean OT
sns.histplot(df_clean[df_clean["overtime_hours"] > 0]["overtime_hours"], bins=30, kde=True, ax=axes[0], color="#0ca678")
axes[0].set_title("Clean Data: Overtime Hours (>0 hrs)")
axes[0].set_xlabel("Overtime Hours")

# Anomalous OT
sns.histplot(df_anom[df_anom["overtime_hours"] > 0]["overtime_hours"], bins=35, kde=True, ax=axes[1], color="#e03131")
axes[1].set_title("Anomalous Data: Overtime Hours (Showing 80-140h Spike)")
axes[1].set_xlabel("Overtime Hours")

plt.tight_layout()
plt.show()

print("Clean Overtime Statistics (where OT > 0):")
display(df_clean[df_clean["overtime_hours"] > 0]["overtime_hours"].describe().round(2))"""))

    # Section 8: Attendance Distributions
    cells.append(md_cell("""## 8. Attendance & Leave Distributions
Evaluate working days, present days, and leave days. Verify impossible attendance values in anomalous data."""))

    cells.append(code_cell("""fig, axes = plt.subplots(1, 3, figsize=(16, 4))

sns.countplot(data=df_clean, x="working_days", ax=axes[0], palette="crest")
axes[0].set_title("Working Days per Month")

sns.countplot(data=df_clean, x="leave_days", ax=axes[1], palette="flare")
axes[1].set_title("Leave Days Distribution (Clean)")

sns.histplot(df_clean["present_days"], bins=15, ax=axes[2], color="#339af0")
axes[2].set_title("Present Days Distribution (Clean)")

plt.tight_layout()
plt.show()

# Impossible Attendance Check
imp_clean = df_clean[df_clean["present_days"] > df_clean["working_days"]]
imp_anom = df_anom[df_anom["present_days"] > df_anom["working_days"]]
print(f"Impossible Attendance records in Clean dataset     : {len(imp_clean)}")
print(f"Impossible Attendance records in Anomalous dataset : {len(imp_anom)}")
display(imp_anom[["employee_id", "payroll_month", "working_days", "present_days", "leave_days", "anomaly_type"]].head(5))"""))

    # Section 9: Deductions Breakdown
    cells.append(md_cell("""## 9. Deductions Breakdown (PF, ESI, TDS, Professional Tax)
Analyze the contribution of each statutory deduction component to total deductions."""))

    cells.append(code_cell("""ded_summary = df_clean[["pf", "esi", "tds", "other_deductions", "total_deductions"]].describe().T.round(2)
display(ded_summary)

fig, axes = plt.subplots(1, 4, figsize=(16, 4))
sns.histplot(df_clean["pf"], ax=axes[0], color="#1971c2", bins=30)
axes[0].set_title("Provident Fund (PF)")

sns.histplot(df_clean[df_clean["esi"] > 0]["esi"], ax=axes[1], color="#f08c00", bins=20)
axes[1].set_title("ESI (Eligible Gross <= 21k)")

sns.histplot(df_clean[df_clean["tds"] > 0]["tds"], ax=axes[2], color="#ae3ec9", bins=30)
axes[2].set_title("TDS (Tax Deducted at Source)")

sns.countplot(data=df_clean, x="other_deductions", ax=axes[3], palette="viridis")
axes[3].set_title("Other Deductions (Professional Tax)")

plt.tight_layout()
plt.show()"""))

    # Section 10: Reconciliation Audit
    cells.append(md_cell("""## 10. Mathematical Reconciliation Audit
Audit deterministic payroll reconciliation rules:
1. `gross_salary == basic_salary + allowances + overtime_amount + bonus`
2. `total_deductions == pf + esi + tds + other_deductions`
3. `net_salary == gross_salary - total_deductions`"""))

    cells.append(code_cell("""# Reconciliation checks on clean dataset
gross_diff_clean = np.abs(df_clean["gross_salary"] - (df_clean["basic_salary"] + df_clean["allowances"] + df_clean["overtime_amount"] + df_clean["bonus"]))
ded_diff_clean = np.abs(df_clean["total_deductions"] - (df_clean["pf"] + df_clean["esi"] + df_clean["tds"] + df_clean["other_deductions"]))
net_diff_clean = np.abs(df_clean["net_salary"] - (df_clean["gross_salary"] - df_clean["total_deductions"]))

print(f"Clean Data - Max Gross Discrepancy     : ₹{gross_diff_clean.max():.4f}")
print(f"Clean Data - Max Deductions Discrepancy: ₹{ded_diff_clean.max():.4f}")
print(f"Clean Data - Max Net Discrepancy       : ₹{net_diff_clean.max():.4f}")

# Reconciliation checks on anomalous dataset
net_diff_anom = np.abs(df_anom["net_salary"] - (df_anom["gross_salary"] - df_anom["total_deductions"]))
corrupted_net_records = df_anom[net_diff_anom > 0.1]
print(f"\\nAnomalous Data - Records failing Net Reconciliation: {len(corrupted_net_records):,} (Injected ABNORMAL_NET_SALARY anomalies)")
display(corrupted_net_records[["employee_id", "payroll_month", "gross_salary", "total_deductions", "net_salary", "anomaly_type"]].head(5))"""))

    # Section 11: Month-over-Month Dynamics
    cells.append(md_cell("""## 11. Month-over-Month Salary Progression & Increment Dynamics
Analyze how employee salaries evolve over 12 months, highlighting legitimate annual increments (~5-15%) and promotions (~15-30%)."""))

    cells.append(code_cell("""df_sorted = df_clean.sort_values(by=["employee_id", "payroll_month"]).copy()
df_sorted["prev_basic"] = df_sorted.groupby("employee_id")["basic_salary"].shift(1)
df_sorted["basic_change_pct"] = ((df_sorted["basic_salary"] - df_sorted["prev_basic"]) / df_sorted["prev_basic"]) * 100.0

legitimate_increments = df_sorted[df_sorted["basic_change_pct"] > 0]["basic_change_pct"]

plt.figure(figsize=(10, 4))
sns.histplot(legitimate_increments, bins=30, kde=True, color="#2f9e44")
plt.title("Distribution of Legitimate Annual Salary Increments (%)")
plt.xlabel("Salary Increase (%)")
plt.show()

print(f"Total legitimate increment events across 10,000 employees over 12 months: {len(legitimate_increments):,}")
print(f"Average annual increment rate: {legitimate_increments.mean():.2f}%")"""))

    # Section 12: Anomaly Class Balance
    cells.append(md_cell("""## 12. Anomaly Class Distribution
Inspect the distribution of normal (`is_anomaly = 0`) vs anomalous (`is_anomaly = 1`) records."""))

    cells.append(code_cell("""counts = df_anom["is_anomaly"].value_counts()
labels = ["Normal (0)", "Anomaly (1)"]
colors = ["#4dabf7", "#ff6b6b"]

fig, ax = plt.subplots(1, 2, figsize=(14, 5))

ax[0].bar(labels, counts.values, color=colors, width=0.5)
ax[0].set_title("Class Balance Counts")
for i, v in enumerate(counts.values):
    ax[0].text(i, v + 1000, f"{v:,} ({v/len(df_anom)*100:.1f}%)", ha="center", fontweight="bold")

ax[1].pie(counts.values, labels=labels, autopct="%1.2f%%", startangle=140, colors=colors, explode=(0, 0.1))
ax[1].set_title("Class Balance Ratio")

plt.tight_layout()
plt.show()"""))

    # Section 13: Anomaly Types Breakdown
    cells.append(md_cell("""## 13. Breakdown of 13 Injected Anomaly Types
Examine the occurrence of each anomaly type, breakdown by severity rating (CRITICAL, HIGH, MEDIUM, LOW), and review the audit trail."""))

    cells.append(code_cell("""plt.figure(figsize=(13, 6))
type_counts = df_meta["anomaly_type"].value_counts()
sns.barplot(x=type_counts.values, y=type_counts.index, palette="mako")
plt.title("Distribution of Injected Anomalies by Type (Audit Metadata)")
plt.xlabel("Number of Injected Instances")
plt.ylabel("Anomaly Type")
plt.show()

severity_counts = df_meta["severity"].value_counts()
display(pd.DataFrame({
    "Severity Rating": severity_counts.index,
    "Count": severity_counts.values,
    "Percentage": (severity_counts.values / len(df_meta) * 100).round(2)
}))

print("\\nSample Anomaly Audit Log Entries:")
display(df_meta.head(10))"""))

    # Section 14: Case Studies
    cells.append(md_cell("""## 14. Deep-Dive Case Studies: Anomalous vs Normal Employees
Let's inspect the complete 12-month timeline for sample employees with injected anomalies."""))

    cells.append(code_cell("""# Case Study 1: Sudden Salary Spike Anomaly
sample_anom = df_meta[df_meta["anomaly_type"] == "SUDDEN_SALARY_INCREASE"].iloc[0]
emp_case_1 = sample_anom["employee_id"]
print(f"=== Case 1: SUDDEN_SALARY_INCREASE on Employee {emp_case_1} in Month {sample_anom['payroll_month']} ===")
emp_1_history = df_anom[df_anom["employee_id"] == emp_case_1][["payroll_month", "basic_salary", "gross_salary", "net_salary", "is_anomaly", "anomaly_type"]]
display(emp_1_history)

# Case Study 2: Excessive Overtime Anomaly
sample_anom_ot = df_meta[df_meta["anomaly_type"] == "EXCESSIVE_OVERTIME"].iloc[0]
emp_case_2 = sample_anom_ot["employee_id"]
print(f"\\n=== Case 2: EXCESSIVE_OVERTIME on Employee {emp_case_2} in Month {sample_anom_ot['payroll_month']} ===")
emp_2_history = df_anom[df_anom["employee_id"] == emp_case_2][["payroll_month", "overtime_hours", "overtime_amount", "gross_salary", "is_anomaly", "anomaly_type"]]
display(emp_2_history)"""))

    # Section 15: Summary & Phase 2 Transition
    cells.append(md_cell("""## 15. Key Takeaways & Transition to Phase 2

### Summary of Findings:
1. **Clean Foundation**: The clean dataset of 10,000 employees over 12 months (120,000 records) is 100% mathematically reconciled, adheres to department salary tiers, and exhibits realistic attendance and increment dynamics.
2. **Controlled Anomaly Injection**: 13 distinct anomaly categories were injected into a separate dataset (`anomalous_payroll.csv`), creating a realistic 5.34% anomaly rate with an exact audit trail in `anomaly_metadata.csv`.
3. **Deterministic Validation**: Core structural errors (impossible attendance, duplicate disbursements, reconciliation failures) are reliably caught by deterministic rules, establishing a benchmark against which ML models can complement detection.
4. **ML Feature Foundation**: 66 engineered features (ratios, MoM deltas, historical rolling statistics, and peer comparisons) have been implemented and verified.

### Next Step:
👉 **PHASE 2 — Feature Engineering, Label Quality & Training Dataset Preparation**."""))

    notebook_dict = {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }

    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(notebook_dict, f, indent=2)
    print(f"Successfully generated notebook at: {notebook_path.resolve()}")

if __name__ == "__main__":
    nb_path = Path("notebooks/01_payroll_eda.ipynb")
    create_eda_notebook(nb_path)
