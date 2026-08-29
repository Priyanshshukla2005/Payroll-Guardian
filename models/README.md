# 🤖 AI Payroll Guardian — Model Directory

This directory stores serialized model artifacts, versioned checkpoints, probability calibrators, and configuration schemas.

---

## 🗂️ Directory Structure

```
models/
├── v1/                       # Phase 3 Baseline Models (Random Forest, XGBoost, Isolation Forest)
├── v2/                       # Phase 4 Hardened Hybrid Models (HybridPayrollDetector_V2)
├── model_config.json         # Master model hyperparameter & feature schema
└── sample_evidence_v2.json   # Sample structured evidence card for RAG testing
```

---

## ⚙️ How to Retrain Models

To retrain and serialize all anomaly detection models:

```bash
# 1. Train Phase 3 Baseline Models
python scripts/training/train_models.py

# 2. Train Phase 4 Hardened Hybrid Models
python scripts/training/run_phase4_hardening.py
```

> **Note**: Binary joblib artifacts (`*.joblib`) are excluded from git tracking via `.gitignore`. The lightweight metadata configurations and sample cards are committed.
