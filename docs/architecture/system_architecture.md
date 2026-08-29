# 🏛️ AI Payroll Guardian — System Architecture

**Version**: `v1.0.0-modular`  
**Date**: August 2026  
**Status**: ACTIVE & STRUCTURED  

---

## 1. 🏗️ High-Level Architectural Diagram

```
                              PAYROLL DATA INGESTION
                     (data_pipeline/loader.py: CSV / Parquet)
                                         ↓
                                   DATA PIPELINE
             (data_pipeline/cleaner.py: Streaming Deterministic Validation)
                                         ↓
                                FEATURE ENGINEERING
               (ai/features/payroll_features.py & cold_start_features.py)
                                         ↓
                         HYBRID AI ANOMALY DETECTOR V2
                     (ai/detection/hybrid_detector.py)
                    ↙                    ↓                    ↘
            ML PROBABILITIES    DETERMINISTIC RULES    STATISTICAL SIGNALS
        (RandomForest / XGBoost)  (Enhanced Rules)    (MAD Robust Z-Scores)
                    ↘                    ↓                    ↙
                         PROBABILITY CALIBRATION
                     (ai/detection/calibrator.py)
                                         ↓
                           STRUCTURED EVIDENCE CARD
                    (ai/explainability/explainer_v2.py)
                                         ↓
                        PAYROLL & COMPLIANCE RAG LAYER
                    (rag/retrieval/retriever.py: Date & Jur Filter)
                                         ↓
               =====================================================
               [FUTURE PHASE 6: LLM EXPLANATION & AI ASSISTANT LAYER]
               =====================================================
                                         ↓
               =====================================================
               [FUTURE PHASE 7: FASTAPI BACKEND & ORCHESTRATION]
               =====================================================
                                         ↓
               =====================================================
               [FUTURE PHASE 8: ENTERPRISE AUDIT DASHBOARD / UI]
               =====================================================
```

---

## 2. 🧩 Component Responsibilities & Module Taxonomy

| Layer / Component | Location | Implementation Status | Core Responsibility |
| :--- | :--- | :---: | :--- |
| **Data Engineering** | `data_pipeline/` | **COMPLETE** | High-performance generation (10k dev, 2.4M main, 18M stress), streaming validation, anomaly injection, and hard-case synthesis. |
| **Feature Engineering** | `ai/features/` | **COMPLETE** | 66 engineered temporal, historical, ratio, and statistical features with zero lookahead data leakage. |
| **AI/ML Detection** | `ai/detection/` | **COMPLETE** | Multi-model anomaly detection (`IsolationForest`, `RandomForest`, `GradientBoosting`, `Autoencoder`), multi-label classification, and `HybridPayrollDetector_V2`. |
| **Explainability** | `ai/explainability/` | **COMPLETE** | Generation of structured `DetailedEvidenceCard` with SHAP features, rule citations, peer comparisons, and calibrated risk scores. |
| **Model Training & Evaluation** | `ai/training/` | **COMPLETE** | Precision, Recall, F1, PR-AUC, ROC-AUC, threshold sweep, and unique-employee false positives per 1,000 employees. |
| **Compliance RAG** | `rag/` | **COMPLETE** | Date- and jurisdiction-aware hybrid statutory and policy retrieval with strict 3-tier authority weighting and auditable citations. |
| **LLM Explanation** | `ai/llm/` | *FUTURE (Phase 6)* | Natural language audit explanation and conversational compliance assistant. |
| **Backend Service** | `backend/` | *FUTURE (Phase 7)* | FastAPI microservices, database connectors, and asynchronous job queues. |
| **Frontend Dashboard**| `frontend/` | *FUTURE (Phase 8)* | Modern auditor interactive UI with anomaly drill-down, charts, and RAG citation viewer. |

---

## 3. 🛡️ Data Privacy & Compliance Safeguards
- **100% Synthetic Datasets**: No PII, real names, PAN, Aadhaar, or bank details.
- **Strict Authority Hierarchy**: Tier 1 (Gov Statutory Law) $\gg$ Tier 2 (Internal Company SOPs) $\gg$ Tier 3 (Reference Guides).
- **Audit Traceability**: Every anomaly report includes deterministic rule IDs, ML confidence bounds, and exact statutory section citations.
