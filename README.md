# 🛡️ AI Payroll Guardian
**Intelligent Payroll Verification, Multi-Layered Anomaly Detection & Regulatory Compliance Platform**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 47 Passed](https://img.shields.io/badge/Tests-47%20Passed-brightgreen.svg)](#-testing--validation)
[![Architecture: Modular](https://img.shields.io/badge/Architecture-Modular%20V2-orange.svg)](#-system-architecture)

---

## 📌 Problem Statement

Enterprise payroll processing handles millions of monthly disbursements across complex statutory frameworks (Provident Fund, ESI, TDS, State Professional Tax) and internal company policies. Traditional payroll software relies exclusively on rigid, static threshold rules or manual spot-checks:
- **Subtle Statutory Drifts**: Small unauthorized deduction reductions or calculation drifts evade static rules.
- **Cold-Start & Tenure Vulnerabilities**: New joiners lacking historical records trigger high false-alarm rates or slip past detection.
- **Complex Compound Fraud**: Ghost employees, collusion-based overtime inflation, and creeping unauthorized salary bumps remain hidden within normal aggregates.
- **Compliance Ambiguity**: When an anomaly is flagged, auditors lack immediate, grounded statutory citations to justify payroll holds.

---

## 💡 The Solution: Multi-Layered Hybrid AI + RAG Knowledge Grounding

AI Payroll Guardian introduces a four-pillar defense architecture:
1. **Machine Learning Anomaly Detectors**: Isolation Forests, Random Forests, and Gradient Boosting to detect subtle multi-dimensional tabular outliers.
2. **Deterministic Statutory & Arithmetic Rules**: Strict mathematical checks for bounds, reconciliation balance, and labor law compliance.
3. **Robust Statistical Signals**: Median Absolute Deviation (MAD) robust z-scores and cold-start observation depth tracking.
4. **Authoritative Compliance RAG**: Date-aware and jurisdiction-isolated retrieval of official government acts (EPFO, ESIC, Income Tax, State PT) and company SOPs with audit citations.

---

## 🏛️ System Architecture

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

## 🚀 Current Capabilities (Phases 1 → 5 Complete)

| Phase | Milestone | Core Highlights |
| :---: | :--- | :--- |
| **Phase 1** | **Synthetic Generation & Validation** | Scalable generation (10k dev, 2.4M main, 18M stress), 13 anomaly archetypes, and chunked streaming validation. |
| **Phase 2** | **Feature Engineering & Leakage Audit** | 66 temporal & ratio features with verified zero future-lookahead leakage. |
| **Phase 3** | **ML Model Comparison & FP/1k Metric** | Trained tabular ML models; achieved $0.3$ unique-employee false positives per 1,000 employees. |
| **Phase 4** | **Model Hardening & Hybrid V2** | Cold-start recall boosted from 0.0% to 100.0%, subtle PF errors from 6.8% to 87.0% using `HybridPayrollDetector_V2`. |
| **Phase 5** | **Payroll & Compliance RAG** | 100% Recall@1, 1.000 MRR, 3-tier authority weighting, date lifespan filtering, and traceable citations. |

---

## 🗂️ Project Repository Structure

```
Payroll-Guardian/
├── ai/                         # Machine learning & statistical intelligence layer
│   ├── detection/              # Anomaly detectors, rules, calibrators, hybrid engine
│   ├── features/               # 66 temporal, historical & cold-start features
│   ├── explainability/         # Structured evidence card & SHAP attribution
│   ├── training/               # Multi-metric evaluator & threshold sweeps
│   ├── experiments/            # Experiment trackers & telemetry loggers
│   └── __init__.py
├── rag/                        # Compliance RAG Knowledge System
│   ├── ingestion/              # Document loader, registry & deduplication
│   ├── retrieval/              # Vector store, hybrid reranker & retriever
│   ├── embeddings/             # SentenceTransformers & dense TF-IDF providers
│   ├── chunking/               # Structural semantic chunker
│   ├── citations/              # Auditable citation badge generator
│   ├── evaluation/             # Ground-truth retrieval benchmark suite
│   └── __init__.py
├── data_pipeline/              # Data engineering, generators, cleaners, injectors
├── backend/                    # Reserved for Phase 7 FastAPI services & schemas
├── frontend/                   # Reserved for Phase 8 Auditor Dashboard UI
├── data/                       # Datasets, schemas & regulatory knowledge base
├── models/                     # Serialized model checkpoints & configs (v1 & v2)
├── experiments/                # Experiment benchmark records & evaluation JSONs
├── notebooks/                  # Interactive Jupyter exploratory & evaluation notebooks
├── scripts/                    # CLI execution scripts (data, training, rag, utilities)
├── tests/                      # Pytest unit & integration test suites
├── configs/                    # Environment & dataset JSON configurations
├── docs/                       # Architectural specs, model cards & phase reports
├── pyproject.toml              # Project packaging & dependencies
├── requirements.txt            # Locked requirements
├── LICENSE                     # MIT License
└── README.md                   # Project documentation
```

---

## 📊 Dataset & Scale Specifications

All payroll datasets generated and processed by AI Payroll Guardian are **100% synthetic** and reproducible:
- **Development Scale (`dev`)**: 10,000 employees $\times$ 12 months = **120,000 records** (rapid iteration).
- **Main ML Scale (`main`)**: 100,000 employees $\times$ 24 months = **2,400,000 records** (full model training).
- **Stress Scale (`stress`)**: 500,000 employees $\times$ 36 months = **18,000,000 records** (scalability & memory benchmark).

```bash
# Generate development dataset
python scripts/data/generate_dataset.py --scale dev
```

---

## 🤖 AI Models & Detection Engines

1. **`RandomForestDetector`**: Tuned ensemble classifier operating on 94 engineered features.
2. **`GradientBoostingDetector`**: Histogram-based gradient boosting optimized for tabular inference.
3. **`IsolationForestDetector`**: Unsupervised tree isolation generating calibrated anomaly scores.
4. **`TabularAutoencoderDetector`**: Deep reconstruction network flagging non-linear feature anomalies.
5. **`HybridPayrollDetector_V2`**: Ensembles ML probabilities, enhanced deterministic rules, and robust MAD z-scores with isotonic probability calibration.
6. **`MultiLabelAnomalyTypeClassifier`**: Multi-output classifier categorizing detected anomalies across 13 distinct types.

---

## 📚 Compliance RAG Knowledge System

The RAG layer translates detected anomaly evidence cards into grounded legal and policy context:
- **Tier 1 (Authoritative Government Law)**: EPFO Act 1952, ESIC Act 1948, Income Tax Act Section 192, State Professional Tax Acts (Maharashtra, Karnataka).
- **Tier 2 (Company Policies)**: Enterprise Overtime Policy (1.5x basic rate, 40h cap), Leave & LOP Guidelines.
- **Tier 3 (Reference Guides)**: General payroll literature.
- **Date & Jurisdiction Isolation**: Ensures payroll disbursements in Maharashtra are never evaluated against Karnataka rules, and expired circulars are excluded.

---

## 🧪 Testing & Validation

Run the complete test suite across AI, Data, RAG, and Integration layers:

```bash
python -m pytest -v
```

```
============================= 47 passed in 8.47s ==============================
```

---

## 🚀 Quickstart & Setup

### 1. Installation
```bash
git clone https://github.com/Priyanshshukla2005/Payroll-Guardian.git
cd Payroll-Guardian

python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Run Pipeline Scripts
```bash
# Ingest and benchmark RAG knowledge system
python scripts/rag/run_rag_pipeline.py

# Train & benchmark Phase 4 Hardened Hybrid Detector
python scripts/training/run_phase4_hardening.py
```

---

## 🗺️ Project Roadmap

- [x] **Phase 1**: Synthetic Data Generation & Streaming Validation
- [x] **Phase 2**: Feature Engineering, Leakage Audit & Deterministic Baseline
- [x] **Phase 3**: ML Model Training, Comparison & False Positive Optimization
- [x] **Phase 4**: Model Hardening, Calibration & Cold-Start Robustness
- [x] **Phase 5**: Payroll & Compliance RAG Knowledge System
- [ ] **Phase 6**: LLM Natural Language Explanation & Payroll AI Assistant Layer
- [ ] **Phase 7**: Production FastAPI Backend & Microservice Architecture
- [ ] **Phase 8**: Auditor Web Dashboard & Interactive Visualization
- [ ] **Phase 9**: End-to-End System Integration & Stress Testing
- [ ] **Phase 10**: Real-World Pilot Validation & Audit Hardening

---

## 🔒 Limitations & Ethical Disclaimer

> [!WARNING]
> - **SYNTHETIC DATA**: The current models are trained on realistic synthetic datasets designed to replicate Indian enterprise payroll behaviors. They are not yet production-certified for live corporate disbursement authorization.
> - **DECISION SUPPORT ONLY**: AI Payroll Guardian serves as an auditor decision-support tool. It flags discrepancies and provides regulatory citations; all final payroll disbursements remain subject to authorized human audit.
