# AI Payroll Guardian — Notebooks

This directory contains research, exploratory data analysis, and validation notebooks.

## Notebook Index

- **`01_payroll_eda.ipynb`**: Comprehensive Exploratory Data Analysis (EDA) of synthetic clean and anomalous payroll records.
  - Dataset dimensions, schema audit, and missing values
  - Salary distributions across departments and designations
  - Overtime and attendance patterns
  - Deduction and bonus structures
  - Month-over-month salary progression and legitimate increment dynamics
  - Anomaly distribution across all 13 injected anomaly types
  - Comparative case studies of normal vs. anomalous employee profiles

## Running Notebooks

Launch Jupyter from the project root:

```bash
jupyter notebook notebooks/01_payroll_eda.ipynb
```
or run headless execution:

```bash
jupyter nbconvert --to notebook --execute notebooks/01_payroll_eda.ipynb --output 01_payroll_eda_executed.ipynb
```
