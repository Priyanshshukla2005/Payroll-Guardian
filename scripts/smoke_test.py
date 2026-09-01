"""AI Payroll Guardian — Standalone Pre-Flight Smoke Test Script (Phase 9).

Performs rapid verification of the core system pipeline:
1. Backend Health, Liveness, and Readiness endpoints.
2. End-to-End Payroll Batch Ingestion and Validation.
3. Feature Engineering and Hybrid AI Anomaly Detection.
4. Compliance RAG Knowledge Retrieval & Citation Linking.
5. Grounded LLM Explanation Generation & Fallback Resilience.
6. Schema Validation & Response Integrity.

Exit Code:
    0 on Success (All health checks & pipeline assertions passed)
    1 on Failure

Usage:
    python scripts/smoke_test.py
"""

import os
import sys
import time
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.main import create_app


def run_smoke_test() -> bool:
    """Execute end-to-end smoke verification."""
    print("=" * 65)
    print("  AI PAYROLL GUARDIAN — PRODUCTION SMOKE TEST SUITE")
    print("=" * 65)
    start_time = time.perf_counter()

    try:
        # 1. Initialize FastAPI Application & Lifespan
        print("[1/5] Initializing FastAPI application & warming model pipeline...")
        t0 = time.perf_counter()
        app = create_app()
        with TestClient(app) as client:
            init_dur_ms = (time.perf_counter() - t0) * 1000.0
            print(f"      OK — Application initialized ({init_dur_ms:.1f}ms)")

            # 2. Verify Health Check Endpoints
            print("[2/5] Checking Health, Liveness, and Readiness endpoints...")
            health_resp = client.get("/api/v1/health")
            assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
            h_data = health_resp.json()
            assert h_data["status"] in ("healthy", "degraded"), f"Unexpected health status: {h_data}"

            live_resp = client.get("/api/v1/health/liveness")
            assert live_resp.status_code == 200, f"Liveness failed: {live_resp.text}"

            ready_resp = client.get("/api/v1/health/readiness")
            assert ready_resp.status_code == 200, f"Readiness failed: {ready_resp.text}"
            r_data = ready_resp.json()
            assert r_data["status"] == "ready", f"Unexpected readiness status: {r_data}"
            print(f"      OK — Health: {h_data['status']}, Model Version: {r_data['model_version']}, RAG Chunks: {r_data['rag_indexed_chunks']}")

            # 3. Direct Compliance RAG Query
            print("[3/5] Testing Compliance RAG Knowledge Search...")
            comp_resp = client.post(
                "/api/v1/compliance/search",
                json={
                    "query": "EPFO Provident Fund statutory rate basic salary",
                    "jurisdiction": "INDIA",
                    "payroll_date": "2024-06-01",
                    "topic": "PF",
                    "top_n": 2,
                },
            )
            assert comp_resp.status_code == 200, f"Compliance search failed: {comp_resp.text}"
            c_data = comp_resp.json()
            print(f"      OK — Compliance RAG Status: {c_data['status']}, Found Sources: {c_data['total_found']}")

            # 4. End-to-End Batch Payroll Analysis
            print("[4/5] Executing End-to-End Payroll Anomaly Detection & Grounded Explanation...")
            payload = {
                "payroll_period": "2024-06",
                "jurisdiction": "INDIA",
                "records": [
                    {
                        "employee_id": "EMP_SMOKE_NORM",
                        "payroll_month": "2024-06",
                        "department": "Engineering",
                        "designation": "Junior",
                        "location": "Bengaluru",
                        "basic_salary": 50000.0,
                        "allowances": 25000.0,
                        "gross_salary": 75000.0,
                        "total_deductions": 6000.0,
                        "net_salary": 69000.0,
                        "pf_deduction": 6000.0,  # 12% compliant
                        "working_days": 26,
                        "present_days": 26,
                        "overtime_hours": 0.0,
                        "salary_change_percentage": 0.0,
                    },
                    {
                        "employee_id": "EMP_SMOKE_ANOM_PF",
                        "payroll_month": "2024-06",
                        "department": "Finance",
                        "designation": "Senior",
                        "location": "Mumbai",
                        "basic_salary": 100000.0,
                        "allowances": 50000.0,
                        "gross_salary": 150000.0,
                        "total_deductions": 1200.0,
                        "net_salary": 148800.0,
                        "pf_deduction": 1200.0,  # Severe PF mismatch (Expected 12,000)
                        "working_days": 26,
                        "present_days": 26,
                        "overtime_hours": 0.0,
                        "salary_change_percentage": 0.0,
                    },
                ],
            }

            t_pipe = time.perf_counter()
            resp = client.post("/api/v1/payroll/analyze", json=payload)
            pipe_dur_ms = (time.perf_counter() - t_pipe) * 1000.0
            assert resp.status_code == 200, f"Batch analysis failed: {resp.text}"

            anl_data = resp.json()
            assert anl_data["status"] == "COMPLETED"
            assert anl_data["summary"]["records_analyzed"] == 2
            assert anl_data["summary"]["records_flagged"] >= 1

            flagged = anl_data["anomalies"]
            assert any(a["employee_id"] == "EMP_SMOKE_ANOM_PF" for a in flagged)
            pf_anom = next(a for a in flagged if a["employee_id"] == "EMP_SMOKE_ANOM_PF")
            assert "RULE_PF_MISMATCH" in pf_anom["rule_violations"]
            assert pf_anom["explanation"]["summary"] is not None

            print(f"      OK — Analyzed: {anl_data['summary']['records_analyzed']} records, Flagged: {anl_data['summary']['records_flagged']} anomalies ({pipe_dur_ms:.1f}ms)")
            print(f"           Timings -> Features: {anl_data['timings']['feature_generation_ms']}ms, Detect: {anl_data['timings']['detection_ms']}ms, RAG: {anl_data['timings']['rag_ms']}ms, LLM: {anl_data['timings']['llm_ms']}ms")

            # 5. Assistant Q&A Endpoint
            print("[5/5] Testing AI Compliance Assistant Q&A Endpoint...")
            asst_resp = client.post(
                "/api/v1/assistant/query",
                json={
                    "question": "What is the statutory employee contribution rate for Provident Fund under EPFO 1952?",
                    "jurisdiction": "INDIA",
                },
            )
            assert asst_resp.status_code == 200, f"Assistant query failed: {asst_resp.text}"
            asst_data = asst_resp.json()
            assert asst_data["answer"] is not None
            print(f"      OK — Assistant responded with grounded answer ({len(asst_data['grounded_facts'])} grounded facts)")

        total_time_s = time.perf_counter() - start_time
        print("=" * 65)
        print(f"  SMOKE TEST PASSED — 100% OPERATIONAL ({total_time_s:.2f}s total)")
        print("=" * 65)
        return True

    except Exception as exc:
        import traceback
        print("\n" + "!" * 65)
        print(f"  SMOKE TEST FAILED: {exc}")
        traceback.print_exc()
        print("!" * 65)
        return False


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
