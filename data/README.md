# 📊 AI Payroll Guardian — Data Directory

This directory contains the synthetic datasets, raw schemas, processed features, and regulatory knowledge bases.

---

## 🗂️ Directory Structure

```
data/
├── raw/                      # Ingested raw payroll feeds (CSV / Parquet)
├── synthetic/                # Generated synthetic payroll datasets (Clean & Anomalous)
├── processed/                # Preprocessed ML train/validation/test feature matrices
└── knowledge/                # Payroll compliance & statutory knowledge base
    ├── raw/                  # Official Markdown statutory acts & company policies
    ├── parsed/               # Parsed section ASTs
    ├── chunks/               # Structural semantic chunk records
    ├── metadata/             # Document registry, SHA-256 hashes, evaluation metrics
    └── embeddings/           # Vector store index and dense embeddings
```

---

## ⚙️ How to Regenerate Datasets

To regenerate the development, main, or stress datasets from scratch:

```bash
# 1. Generate 10k development dataset (120k records)
python scripts/data/generate_dataset.py --scale dev

# 2. Generate 100k main ML dataset (2.4M records)
python scripts/data/generate_dataset.py --scale main

# 3. Generate 500k stress dataset (18M records)
python scripts/data/generate_dataset.py --scale stress
```

> **Note**: Large multi-gigabyte synthetic datasets (`anomalous_payroll.csv`, `X_train.parquet`) are excluded from git version control via `.gitignore` to maintain a lightweight repository. All data generation is 100% deterministic and reproducible via the scripts above.
