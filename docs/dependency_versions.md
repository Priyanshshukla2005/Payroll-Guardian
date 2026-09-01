# Dependency Versions & Technology Stack (Phase 9)

This document records the exact runtime dependency versions, environments, and toolchains for AI Payroll Guardian.

---

## 1. System Runtime Environments

| Environment | Version | Purpose |
| :--- | :--- | :--- |
| **Python** | `3.11.9` | Primary backend, ML inference, RAG retrieval & LLM pipeline |
| **Node.js** | `v20.x` / `v22.x` | Frontend React development and production asset compilation |
| **Operating System** | Windows / Linux (Docker) | Host environment & container runtime |

---

## 2. Core Python Dependencies

| Package | Version | Purpose |
| :--- | :--- | :--- |
| `fastapi` | `0.116.2` | High-performance asynchronous REST API framework |
| `pydantic` | `2.11.2` | Strict data validation, schema enforcement & serialization |
| `uvicorn` | `0.36.0` | Production ASGI web server |
| `starlette` | `0.46.2` | Core ASGI toolkit, middleware & exception handling |
| `scikit-learn` | `1.8.0` | Preprocessing pipelines, Isolation Forest, TF-IDF vectorization |
| `pandas` | `2.1.2` | High-performance tabular data ingestion and manipulation |
| `numpy` | `1.26.1` | Vector math, matrix algebra, and array operations |
| `torch` | `2.5.1` | Neural autoencoder anomaly detection & PyTorch tensor ops |
| `xgboost` | `2.1.0` | Supervised gradient boosting classifier & feature ranking |
| `lightgbm` | `4.3.0` | Light gradient boosting tree model |
| `pyarrow` | `15.0.0` | Parquet columnar serialization and streaming dataset I/O |
| `joblib` | `1.4.2` | Optimized artifact serialization and model persistence |
| `pytest` | `9.1.1` | Automated regression, unit, and integration testing |
| `httpx` | `0.28.1` | Asynchronous HTTP client & TestClient backend |
| `python-multipart` | `0.0.20` | Secure multipart file upload parser for CSV/Parquet |

---

## 3. Frontend Dependencies (React & TypeScript)

| Package | Version | Purpose |
| :--- | :--- | :--- |
| `react` | `^18.3.1` | Component-based UI library |
| `react-dom` | `^18.3.1` | React DOM rendering engine |
| `react-router-dom` | `^6.28.0` | Single-page application client routing |
| `typescript` | `~5.6.2` | Static type safety and contract compilation |
| `vite` | `^5.4.10` | Next-generation frontend build tool and dev server |
| `vitest` | `^2.1.4` | Vite-native unit testing runner |
| `lucide-react` | `^0.475.0` | Accessible, modern iconography |
| `recharts` | `^2.13.3` | Interactive chart and risk visualizer |
| `tailwindcss` | `^3.4.15` | Modern utility CSS framework |
| `tailwind-merge` | `^2.5.4` | Class merge utility |
| `clsx` | `^2.1.1` | Conditional className constructor |

---

## 4. Stability & Upgrade Guidance

- **Python Ecosystem**: PyTorch and scikit-learn models are tightly coupled with feature pipeline pickles (`hybrid_detector_v2.joblib`). Upgrades to `scikit-learn` or `joblib` must be accompanied by retraining and verifying artifact unpickling aliases via `_register_legacy_unpickle_aliases()`.
- **FastAPI / Starlette**: Deprecation warning for `HTTP_422_UNPROCESSABLE_ENTITY` vs `HTTP_422_UNPROCESSABLE_CONTENT` is managed gracefully.
- **Frontend Ecosystem**: Zero TypeScript errors during `npm run build` (`tsc && vite build`).
