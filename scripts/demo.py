"""AI Payroll Guardian — Interactive & Automated System Demo (Phase 9).

Executes a live walkthrough of the end-to-end intelligence stack:
Synthetic Data -> 66 Features -> Hybrid AI Detection -> Evidence Card ->
Compliance RAG -> Grounded LLM Audit Explanation -> Assistant Q&A.

Runs 100% locally with zero paid API keys required.

Usage:
    python scripts/demo.py
"""

import json
import sys
import time
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.main import create_app


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def print_section(title: str):
    print(f"\n--- [ {title} ] " + "-" * (55 - len(title)))


def run_demo():
    """Execute complete end-to-end system demo."""
    print_banner("AI Payroll Guardian — Comprehensive System Demo")
    print("  Stack: FastAPI + 66-Feature ML + Hybrid Detector + Compliance RAG + Grounded LLM")
    print("  Provider: Grounded Deterministic Engine (Zero external LLM API cost)")

    app = create_app()

    with TestClient(app) as client:
        # Step 1: Health & Readiness
        print_section("1. System Readiness & Health")
        ready_res = client.get("/api/v1/health/readiness").json()
        print(f"  Status: {ready_res['status'].upper()}")
        print(f"  Active ML Model: {ready_res['model_version']}")
        print(f"  Indexed Regulatory Chunks: {ready_res['rag_indexed_chunks']} statutory sections")
        print(f"  LLM Provider: {ready_res['llm_provider']}")

        # Step 2: Batch Analysis of 4 Representative Cases
        print_section("2. Ingesting Multi-Scenario Payroll Batch (4 Employees)")
        demo_payload = {
            "payroll_period": "2024-06",
            "jurisdiction": "INDIA",
            "records": [
                # Case 1: Normal Compliant Employee
                {
                    "employee_id": "EMP_001_CLEAN",
                    "payroll_month": "2024-06",
                    "department": "Engineering",
                    "designation": "Senior",
                    "location": "Bengaluru",
                    "basic_salary": 120000.0,
                    "allowances": 60000.0,
                    "gross_salary": 180000.0,
                    "total_deductions": 14400.0,
                    "net_salary": 165600.0,
                    "pf_deduction": 14400.0,  # Exactly 12% of 120,000
                    "working_days": 26,
                    "present_days": 26,
                    "overtime_hours": 0.0,
                    "salary_change_percentage": 0.0,
                },
                # Case 2: Statutory PF Under-Deduction
                {
                    "employee_id": "EMP_002_PF_MISMATCH",
                    "payroll_month": "2024-06",
                    "department": "Finance",
                    "designation": "Manager",
                    "location": "Mumbai",
                    "basic_salary": 150000.0,
                    "allowances": 75000.0,
                    "gross_salary": 225000.0,
                    "total_deductions": 1800.0,
                    "net_salary": 223200.0,
                    "pf_deduction": 1800.0,  # Expected 18,000 (Severe under-deduction)
                    "working_days": 26,
                    "present_days": 26,
                    "overtime_hours": 0.0,
                    "salary_change_percentage": 0.0,
                },
                # Case 3: 300% Sudden Salary Spike
                {
                    "employee_id": "EMP_003_SALARY_SPIKE",
                    "payroll_month": "2024-06",
                    "department": "Sales",
                    "designation": "Junior",
                    "location": "Delhi-NCR",
                    "basic_salary": 180000.0,  # Junior typical is ~35k
                    "allowances": 90000.0,
                    "gross_salary": 270000.0,
                    "total_deductions": 21600.0,
                    "net_salary": 248400.0,
                    "pf_deduction": 21600.0,
                    "working_days": 26,
                    "present_days": 26,
                    "overtime_hours": 0.0,
                    "salary_change_percentage": 3.0,  # 300% sudden increase
                },
                # Case 4: Compound Violations (Attendance Bounds + Overtime Cap)
                {
                    "employee_id": "EMP_004_COMPOUND_VIOLATIONS",
                    "payroll_month": "2024-06",
                    "department": "Operations",
                    "designation": "Junior",
                    "location": "Chennai",
                    "basic_salary": 35000.0,
                    "allowances": 15000.0,
                    "gross_salary": 50000.0,
                    "total_deductions": 500.0,
                    "net_salary": 49500.0,
                    "pf_deduction": 500.0,  # PF mismatch
                    "working_days": 20,
                    "present_days": 26,  # Impossible attendance (present > working)
                    "overtime_hours": 75.0,  # Exceeds monthly overtime cap
                    "salary_change_percentage": 0.0,
                },
            ],
        }

        t_start = time.perf_counter()
        analysis_resp = client.post("/api/v1/payroll/analyze", json=demo_payload)
        total_dur_ms = (time.perf_counter() - t_start) * 1000.0
        data = analysis_resp.json()

        print(f"  Analysis ID: {data['analysis_id']}")
        print(f"  Records Processed: {data['summary']['records_analyzed']}")
        print(f"  Anomalies Flagged: {data['summary']['records_flagged']}")
        print(f"  Total Duration: {total_dur_ms:.1f}ms")
        print(f"  Pipeline Timings:")
        print(f"    - 66-Feature Generation: {data['timings']['feature_generation_ms']}ms")
        print(f"    - Hybrid ML & Rule Detection: {data['timings']['detection_ms']}ms")
        print(f"    - RAG Knowledge Retrieval: {data['timings']['rag_ms']}ms")
        print(f"    - Grounded LLM Explanation: {data['timings']['llm_ms']}ms")

        # Step 3: Inspect Detected Anomalies
        print_section("3. Detailed Anomaly Evidence & Statutory Citations")
        for anom in data["anomalies"]:
            print(f"\n  >> EMPLOYEE: {anom['employee_id']} ({anom['designation']}, {anom['department']})")
            print(f"     Risk Score: {anom['risk_score']:.2f} | Severity: [{anom['severity']}]")
            print(f"     Anomaly Types: {', '.join(anom['anomaly_types'])}")
            if anom["rule_violations"]:
                print(f"     Rule Violations: {', '.join(anom['rule_violations'])}")

            print("     Key Evidence Signals:")
            for ev in anom["evidence"][:2]:
                print(f"       * {ev}")

            comp = anom["compliance"]
            print(f"     Compliance RAG Status: {comp['status']}")
            if comp["sources"]:
                for src in comp["sources"]:
                    print(f"       [STATUTE] {src['document_id']} ({src['authority_level']}) -> {src['citation']}")

            expl = anom["explanation"]
            print(f"     AI Audit Explanation:")
            print(f"       Summary: {expl['summary']}")
            print(f"       Recommended Action: {', '.join(expl['recommended_actions'])}")

        # Step 4: Live Compliance Assistant Q&A
        print_section("4. Live AI Compliance Assistant Q&A")
        questions = [
            "What is the statutory Provident Fund contribution formula under EPFO Act 1952?",
            "What is the maximum overtime threshold permitted per month under Factories Act?",
        ]

        for q in questions:
            print(f"\n  [USER QUESTION]: {q}")
            asst_resp = client.post("/api/v1/assistant/query", json={"question": q, "jurisdiction": "INDIA"}).json()
            print(f"  [AI ASSISTANT ANSWER]: {asst_resp['answer']}")
            if asst_resp["citations"]:
                print(f"  [CITATIONS]: {', '.join(c['citation'] for c in asst_resp['citations'])}")

        print_banner("Demo Complete — All Intelligence Layers Verified")


if __name__ == "__main__":
    run_demo()
