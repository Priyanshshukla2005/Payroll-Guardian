# AI Payroll Guardian — Backend & Service Architecture (Phase 10 Hardened)

## 1. Overview & Objective

Phase 10 establishes the **Enterprise Production-Ready Backend Layer** for AI Payroll Guardian. The backend service exposes the complete intelligence stack—Phase 4 Hybrid Anomaly Detection, Phase 5 Compliance RAG Knowledge Retrieval, Phase 6 Grounded LLM Explanations, Phase 8 React Frontend integration, and Phase 10 Enterprise Security, Persistence, RBAC, and Monitoring—through clean, standardized RESTful endpoints built with FastAPI.

```
                                  AUDITOR / CLIENT
                                         ↓
                                     app.py (Root Startup Wrapper)
                                         ↓
                                 backend/main.py:app (Canonical FastAPI Application)
                      (CORS, Request-ID, Logging, Error Handling, Lifespan)
                                         ↓
                                 API ROUTERS (/api/v1)
    ┌──────────┬──────────┬──────────┬──────────┬────────────┬──────────┬────────────┬──────────┐
    ↓          ↓          ↓          ↓          ↓            ↓          ↓            ↓          ↓
 /health    /live,/ready   /auth      /payroll  /anomalies  /compliance /assistant  /monitoring   /audit
    └──────────┴──────────┴────┬─────┴──────────┴─────┬──────┴──────────┴────────────┴─────┬──────┴────────┘
                               │                      │                                    │
                               ↓                      ↓                                    ↓
                       SECURITY & RBAC        SERVICE LAYER                        PERSISTENCE LAYER
                       (JWT Bearer Token)     (Analysis, Detection,                (SQLAlchemy ORM,
                       (ADMIN, PAYROLL_ADMIN,  Compliance, Explanation,             Postgres / SQLite,
                        AUDITOR, VIEWER)       JobManager Async Worker)             AuditRepository)
                                                      ↓
                                    ┌─────────────────┼─────────────────┐
                                    ↓                 ↓                 ↓
                            DETECTION SERVICE COMPLIANCE SERVICE EXPLANATION SERVICE
                            (ai/detection/)       (rag/)            (ai/llm/)
                                    ↓                 ↓                 ↓
                            Hybrid Anomaly       Authoritative     Grounded LLM
                              Prediction         RAG Retrieval      Explanation
                                    └─────────────────┬─────────────────┘
                                                      ↓
                                            UNIFIED JSON RESPONSE
                                                      ↓
                                                   CLIENT
```

---

## 2. Directory Structure

```
Payroll Guardian/
├── app.py                       # Single user-facing backend startup entrypoint
├── backend/
│   ├── __init__.py              # Exports canonical app instance
│   ├── main.py                  # Canonical FastAPI app factory, lifespan manager, middleware
│   ├── api/                     # REST Controllers (thin routing layer)
│   │   ├── __init__.py
│   │   ├── health.py            # Liveness, Readiness, and Diagnostics probes (/health, /live, /ready)
│   │   ├── auth.py              # JWT login, current user profile, token refresh
│   │   ├── payroll.py           # Batch JSON & CSV/Parquet payroll ingestion & async job status
│   │   ├── anomalies.py         # Anomaly exploration, employee drilldown, and auditor resolution
│   │   ├── compliance.py        # Statutory knowledge search & source document inspection
│   │   ├── assistant.py         # Grounded conversational Q&A assistant
│   │   ├── monitoring.py        # Real-time model metrics and PSI feature drift reports
│   │   └── audit.py             # Immutable audit trail inspection
│   ├── auth/                    # JWT token creation/verification, bcrypt hashing & RBAC route guards
│   ├── database/                # SQLAlchemy ORM models, session management, repository abstractions, seeders
│   ├── services/                # Business orchestration & service domain
│   │   ├── __init__.py
│   │   ├── payroll_service.py   # Normalization, schema casting, CSV parsing
│   │   ├── detection_service.py # Feature engineering, ML scoring, rule execution
│   │   ├── compliance_service.py# RAG vector retrieval, jurisdiction/date filters
│   │   ├── explanation_service.py# Grounded LLM explainer & assistant invocation
│   │   ├── job_manager.py       # Asynchronous ThreadPool task runner for background jobs
│   │   └── analysis_service.py  # End-to-end multi-step analysis pipeline orchestrator
│   │   └── analysis_service.py  # Master end-to-end analysis pipeline orchestrator
│   ├── schemas/                 # Pydantic data contracts and response schemas
│   │   ├── __init__.py
│   │   ├── common.py            # Standardized error envelopes and health models
│   │   ├── payroll.py           # Ingestion payroll row & batch input contracts
│   │   ├── anomaly.py           # Structured evidence, citations, and explanations
│   │   ├── analysis.py          # Batch summary, job states, and unified response
│   │   ├── compliance.py        # Compliance query and search results
│   │   └── assistant.py         # Conversational assistant query and response
│   ├── dependencies/            # FastAPI dependency injection & persistence
│   │   ├── __init__.py
│   │   └── services.py          # ModelManager lifecycle singleton & AnalysisRepository
│   ├── middleware/              # Security, logging, and error handling
│   │   ├── __init__.py
│   │   ├── request_id.py        # UUID4 request tracing & X-Request-ID propagation
│   │   ├── logging.py           # Structured, zero-PII access logging
│   │   └── error_handling.py    # Global standardized exception handlers
│   ├── config/                  # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py          # Environment variables & system parameters
│   └── utils/                   # Helper utilities
│       ├── __init__.py
│       └── security.py          # File upload sanitization & MIME/extension verification
```

---

## 3. Starting the Backend

### 3.1 Recommended Startup (Root Wrapper)
```bash
python app.py
```
This launches Uvicorn programmatically, loading the canonical FastAPI app from `backend.main:app` with host `0.0.0.0` and port `8000` by default.

### 3.2 Advanced / Direct Uvicorn CLI
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 4. Core API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Comprehensive health check across AI, RAG, and LLM services |
| `GET` | `/api/v1/health/liveness` | Lightweight container liveness probe |
| `GET` | `/api/v1/health/readiness` | Readiness verification of loaded models and vector indices |
| `POST` | `/api/v1/payroll/analyze` | Ingest and analyze a JSON batch of payroll records |
| `POST` | `/api/v1/payroll/upload` | Upload and analyze a CSV/JSON/Parquet payroll file |
| `GET` | `/api/v1/payroll/analysis/{id}` | Retrieve full analysis results by unique Analysis ID |
| `GET` | `/api/v1/anomalies/{analysis_id}` | List flagged anomalies with optional severity/type filters |
| `GET` | `/api/v1/anomalies/{id}/{emp_id}` | Retrieve specific employee evidence, RAG citations, and explanation |
| `POST` | `/api/v1/compliance/search` | Search statutory acts, circulars, and internal policies |
| `POST` | `/api/v1/assistant/query` | Conversational grounded assistant for administrator inquiries |

---

## 5. Service Architecture & Orchestration

### 5.1 Model Lifecycle Management (`ModelManager`)
- Models and vector stores are loaded **once** at application startup via FastAPI's `lifespan` context manager.
- Reuses:
  - `HybridPayrollDetector_V2` (from `models/v2/hybrid_detector_v2.joblib`)
  - `PayrollPreprocessor` (from `models/v2/preprocessor_v2.joblib`)
  - `MultiLabelAnomalyTypeClassifier` (from `models/v2/type_classifier_v2.joblib`)
  - `PayrollRAGRetriever` (with indexed vector embeddings from `data/knowledge/embeddings/`)
  - `PayrollLLMClient` (configured with `MockGroundedLLMProvider` or external provider)
- Eliminates per-request deserialization overhead.

### 5.2 End-to-End Orchestration Flow (`AnalysisService`)
1. **Input Normalization**: Ingests JSON records or parses CSV/Parquet uploads into a standardized pandas DataFrame (`PayrollService`).
2. **Feature Engineering**: Calculates 66 derived ratios, historical rolling windows, peer benchmarks, and robust MAD statistical signals (`DetectionService`).
3. **Hybrid Detection**: Evaluates calibrated ML probabilities, deterministic rule violations, and multi-label anomaly categories.
4. **Flagging Condition**: Records are flagged for compliance audit if `risk_score >= 0.45` or `rule_violations > 0`.
5. **RAG Knowledge Retrieval**: For flagged records, translates the structured `DetailedEvidenceCard` into date- and jurisdiction-filtered queries to retrieve authoritative statutory chunks (`ComplianceService`).
6. **Grounded LLM Explanation**: Feeds the evidence card and retrieved statutory citations to the grounded LLM explainer (with deterministic fallback) (`ExplanationService`).
7. **Response Aggregation**: Compiles the unified `AnalysisResponse`, persists it in `AnalysisRepository`, and returns it to the client.

---

## 6. Security & Privacy Guarantees

1. **File Upload Security**:
   - Extension whitelist: `.csv`, `.json`, `.parquet`.
   - Rejects binary executables (e.g. `MZ`, `ELF` signatures) and empty files.
   - Filenames are sanitized to prevent directory traversal attacks (`../`).
   - Maximum upload size enforced via `MAX_UPLOAD_SIZE_MB` (default: 50MB).
2. **Zero-PII Logging**:
   - Structured access logger records only `request_id`, HTTP method, path, status code, and duration.
   - Raw request bodies, compensation figures, PAN, bank accounts, and employee names are never written to access logs.
3. **Standardized Error Handling**:
   - API exceptions return uniform JSON envelopes (`{"error": {"code": "...", "message": "...", "request_id": "...", "status_code": ...}}`).
   - Internal stack traces are never exposed in production error responses.
4. **CORS Configuration**:
   - Explicit origin whitelisting via `CORS_ALLOWED_ORIGINS` environment variable.

---

## 7. Scalability & Performance Benchmarks

Performance measured across synthetic batches using the full AI + RAG + LLM pipeline:

| Batch Size | Total Latency | Throughput (records/sec) | Peak Memory Usage |
| :--- | :--- | :--- | :--- |
| **100 records** | 1.417 s | 70.6 rec/s | 1.27 MB |
| **1,000 records** | 5.897 s | 169.6 rec/s | 8.87 MB |
| **10,000 records** | 52.304 s | 191.2 rec/s | 87.61 MB |

### Scalability Strategy for Ultra-Large Uploads (>100k records)
- **In-Memory Limit**: Synchronous REST requests comfortably handle up to ~25,000 records in-memory.
- **Asynchronous Job Abstraction**: The `AnalysisStatus` lifecycle (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`) and `AnalysisRepository` interface are designed for seamless integration with Celery / Redis / PostgreSQL for background processing of multi-million row datasets.
