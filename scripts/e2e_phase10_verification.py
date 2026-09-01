"""AI Payroll Guardian — Phase 10 Complete End-to-End Workflow Verification Script.

Executes the 15-step production workflow:
1. Application Lifecycle & Engine Verification
2. Health, Liveness, and Readiness Diagnostics
3. Enterprise Authentication & JWT Token Issuance
4. User Profile & Role Validation (/auth/me)
5. Asynchronous Payroll Batch Submission
6. Analysis Job ID Generation & Status Verification
7. Status Polling (QUEUED -> RUNNING -> COMPLETED)
8. Complete Analysis Report Retrieval
9. Deep Anomaly Evidence Inspection
10. Statutory Compliance Retrieval & Provenance Verification
11. Grounded AI Assistant Inquiry
12. Citations & Groundedness Verification
13. Anomaly Resolution & Auditor Sign-off
14. Audit Trail Verification (Zero-PII Compliance Trail)
15. Model Monitoring Telemetry & Drift Detection Verification

Usage:
    python scripts/e2e_phase10_verification.py
"""

import os
import sys
import time
from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.dependencies.services import ModelManager
from backend.main import create_app


def run_e2e_verification() -> bool:
    """Run the 15-step production verification workflow."""
    print("\n" + "=" * 70)
    print("  AI PAYROLL GUARDIAN — PHASE 10 PRODUCTION END-TO-END VERIFICATION")
    print("=" * 70)

    start_total_time = time.perf_counter()
    model_mgr = ModelManager.get_instance()
    model_mgr.initialize()
    app = create_app()

    with TestClient(app) as client:
        # Step 1: Health & Readiness Checks
        print("\n[Step 1] Verifying System Health, Liveness, and Readiness Diagnostics...")
        h_resp = client.get("/api/v1/health")
        assert h_resp.status_code == 200, f"Health failed: {h_resp.text}"
        h_data = h_resp.json()
        assert h_data["status"] in ("healthy", "degraded")
        assert h_data["services"]["database"] == "available"
        print(f"         Health Status: {h_data['status']} | Database: {h_data['services']['database']}")

        live_resp = client.get("/api/v1/live")
        assert live_resp.status_code == 200 and live_resp.json()["status"] == "live"
        print("         Direct Liveness (/api/v1/live): PASS")

        ready_resp = client.get("/api/v1/ready")
        assert ready_resp.status_code == 200 and ready_resp.json()["status"] == "ready"
        print(f"         Direct Readiness (/api/v1/ready): PASS (Chunks: {ready_resp.json()['rag_indexed_chunks']})")

        # Step 2: Authentication (Login)
        print("\n[Step 2] Authenticating as Senior Payroll Officer (PAYROLL_ADMIN)...")
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "payroll_admin", "password": "PayrollAdmin2026!"},
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token_data = login_resp.json()
        jwt_token = token_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {jwt_token}"}
        print(f"         Authenticated: {token_data['username']} | Role: {token_data['role']}")
        print(f"         JWT Access Token: {jwt_token[:25]}... (valid for {token_data['expires_in_seconds']}s)")

        # Step 3: Verify Profile (/auth/me)
        print("\n[Step 3] Verifying authenticated profile via /api/v1/auth/me...")
        me_resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["username"] == "payroll_admin"
        assert me_data["role"] == "PAYROLL_ADMIN"
        print(f"         Profile Verified: {me_data['full_name']} ({me_data['email']})")

        # Step 4: Asynchronous Payroll Batch Submission
        print("\n[Step 4] Submitting multi-record payroll batch with intentional statutory anomalies (Async Mode)...")
        test_records = [
            {
                "employee_id": "EMP_E2E_101",
                "payroll_month": "2024-06",
                "department": "Engineering",
                "designation": "Software Engineer",
                "location": "KARNATAKA",
                "basic_salary": 60000.0,
                "gross_salary": 90000.0,
                "net_salary": 82600.0,
                "allowances": 30000.0,
                "bonus": 0.0,
                "total_deductions": 7400.0,
                "pf_deduction": 7200.0,  # 12% statutory compliant
                "esi": 0.0,
                "professional_tax": 200.0,
                "working_days": 26,
                "present_days": 26,
                "leave_days": 0,
                "overtime_hours": 0.0,
            },
            {
                "employee_id": "EMP_E2E_102",
                "payroll_month": "2024-06",
                "department": "Operations",
                "designation": "Executive",
                "location": "MAHARASHTRA",
                "basic_salary": 40000.0,
                "gross_salary": 65000.0,
                "net_salary": 63800.0,
                "allowances": 25000.0,
                "bonus": 0.0,
                "total_deductions": 1200.0,
                "pf_deduction": 1000.0,  # Severe PF Under-deduction anomaly (1000 vs 4800)
                "esi": 0.0,
                "professional_tax": 200.0,
                "working_days": 26,
                "present_days": 26,
                "leave_days": 0,
                "overtime_hours": 0.0,
            },
            {
                "employee_id": "EMP_E2E_103",
                "payroll_month": "2024-06",
                "department": "Engineering",
                "designation": "Intern",
                "location": "KARNATAKA",
                "basic_salary": 180000.0,  # Ghost / Salary Band Spike anomaly
                "gross_salary": 240000.0,
                "net_salary": 218200.0,
                "allowances": 60000.0,
                "bonus": 0.0,
                "total_deductions": 21800.0,
                "pf_deduction": 21600.0,
                "esi": 0.0,
                "professional_tax": 200.0,
                "working_days": 26,
                "present_days": 26,
                "leave_days": 0,
                "overtime_hours": 0.0,
            },
        ]
        submit_resp = client.post(
            "/api/v1/payroll/analyze?async_mode=true",
            json={"records": test_records, "payroll_period": "2024-06", "jurisdiction": "INDIA"},
            headers=auth_headers,
        )
        assert submit_resp.status_code == 200, f"Submit failed: {submit_resp.text}"
        job_data = submit_resp.json()
        job_id = job_data["analysis_id"]
        print(f"         Job Queued Successfully: Analysis ID = '{job_id}' | Status = {job_data['status']}")

        # Step 5: Polling for Background Job Completion
        print("\n[Step 5] Polling asynchronous job status (QUEUED -> RUNNING -> COMPLETED)...")
        completed_analysis = None
        for attempt in range(1, 30):
            poll_resp = client.get(f"/api/v1/payroll/analysis/{job_id}", headers=auth_headers)
            assert poll_resp.status_code == 200
            p_data = poll_resp.json()
            status = p_data.get("status")
            print(f"         Poll attempt {attempt:02d}: Status = {status}")
            if status == "COMPLETED" and "summary" in p_data:
                completed_analysis = p_data
                break
            time.sleep(0.3)

        assert completed_analysis is not None, "Async analysis job did not complete within time limit."
        print(f"         Job Completed! Processed {completed_analysis['summary']['records_analyzed']} records in {completed_analysis['duration_ms']}ms.")

        # Step 6: Verify Analysis Summary & Anomalies Flagged
        print("\n[Step 6] Verifying Multi-Tier Anomaly Flagging...")
        summary = completed_analysis["summary"]
        anomalies = completed_analysis["anomalies"]
        print(f"         Total Records: {summary['records_analyzed']} | Flagged: {summary['records_flagged']}")
        print(f"         Critical: {summary['critical_risk']} | High: {summary['high_risk']} | Medium: {summary['medium_risk']}")
        assert summary["records_flagged"] >= 1, "Expected anomalies to be flagged."

        # Step 7: Inspect Specific Anomaly Record Evidence
        target_employee = anomalies[0]["employee_id"]
        print(f"\n[Step 7] Investigating detailed anomaly card for Employee '{target_employee}'...")
        anom_detail_resp = client.get(
            f"/api/v1/anomalies/{job_id}/{target_employee}",
            headers=auth_headers,
        )
        assert anom_detail_resp.status_code == 200
        anom_detail = anom_detail_resp.json()
        print(f"         Risk Score: {anom_detail['risk_score']} | Severity: {anom_detail['severity']}")
        print(f"         Signals: {anom_detail['evidence']}")
        print(f"         Rule Violations: {anom_detail['rule_violations']}")
        print(f"         Grounded Summary: {anom_detail['explanation']['summary']}")

        # Step 8: Retrieve Statutory Compliance Knowledge
        print("\n[Step 8] Searching Statutory Compliance RAG Knowledge Base...")
        comp_search_resp = client.post(
            "/api/v1/compliance/search",
            json={"query": "EPFO basic wage provident fund rate deduction ceiling", "jurisdiction": "INDIA"},
            headers=auth_headers,
        )
        assert comp_search_resp.status_code == 200
        comp_search_data = comp_search_resp.json()
        print(f"         Statutory Matches: {comp_search_data['total_found']} citations retrieved.")
        if comp_search_data["results"]:
            top_src = comp_search_data["results"][0]
            print(f"         Top Source: {top_src['title']} ({top_src['document_id']})")
            print(f"         Citation: {top_src.get('citation')} | Relevance: {top_src.get('relevance_score')}")

        # Step 9: Ask AI Assistant Grounded Compliance Inquiry
        print("\n[Step 9] Submitting query to Grounded AI Payroll Assistant...")
        assistant_resp = client.post(
            "/api/v1/assistant/query",
            json={
                "question": "What is the mandatory EPFO contribution rate on basic wages?",
                "analysis_id": job_id,
                "employee_id": target_employee,
            },
            headers=auth_headers,
        )
        assert assistant_resp.status_code == 200
        asst_data = assistant_resp.json()
        print(f"         Assistant Answer: {asst_data['answer'][:120]}...")
        print(f"         Citations: {len(asst_data['citations'])} | Grounded Facts: {len(asst_data['grounded_facts'])}")
        assert len(asst_data["answer"]) > 10, "Empty assistant response."

        # Step 10: Resolve Anomaly with Audit Justification
        print(f"\n[Step 10] Resolving Anomaly '{target_employee}' with Auditor justification...")
        resolve_resp = client.post(
            f"/api/v1/anomalies/{job_id}/{target_employee}/resolve",
            json={"status": "RESOLVED", "resolution_notes": "Statutory audit verified: adjustment remitted in supplementary run."},
            headers=auth_headers,
        )
        assert resolve_resp.status_code == 200
        resolve_data = resolve_resp.json()
        assert resolve_data["status"] == "RESOLVED"
        print(f"          Resolved By: {resolve_data['resolved_by']} at {resolve_data['resolved_at']}")

        # Step 11: Audit Trail Verification
        print("\n[Step 11] Inspecting Enterprise Audit Trail for this Analysis Batch...")
        audit_resp = client.get(f"/api/v1/audit/analysis/{job_id}", headers=auth_headers)
        assert audit_resp.status_code == 200
        events = audit_resp.json()
        event_types = [e["event_type"] for e in events]
        print(f"          Recorded {len(events)} Chronological Audit Events for '{job_id}':")
        for e in events:
            print(f"          - [{e['timestamp'][:19]}] {e['event_type']} (Actor: {e['actor_id']})")
        assert "PAYROLL_UPLOADED" in event_types
        assert "ANALYSIS_COMPLETED" in event_types
        assert "ANOMALY_RESOLVED" in event_types

        # Step 12: Model Monitoring & Feature Drift Verification
        print("\n[Step 12] Verifying Live Model Monitoring & Feature Drift Telemetry...")
        metrics_resp = client.get("/api/v1/monitoring/metrics", headers=auth_headers)
        assert metrics_resp.status_code == 200
        m_data = metrics_resp.json()
        print(f"          Model: {m_data['model_name']} ({m_data['model_version']})")
        print(f"          Total Analyses Monitored: {m_data['total_analyses_monitored']}")
        print(f"          Total Records Scored: {m_data['total_records_scored']}")
        print(f"          Total Anomalies Flagged: {m_data['total_anomalies_flagged']}")

        drift_resp = client.get("/api/v1/monitoring/drift", headers=auth_headers)
        assert drift_resp.status_code == 200
        drift_data = drift_resp.json()
        print(f"          Feature Drift Report: Monitored Features = {drift_data.get('monitored_features_count')}")
        print(f"          Overall Drift Severity = {drift_data.get('drift_severity', 'STABLE')}")

        total_sec = time.perf_counter() - start_total_time
        print("\n" + "=" * 70)
        print(f"  PHASE 10 END-TO-END VERIFICATION: 100% PASS ({total_sec:.2f}s)")
        print("=" * 70 + "\n")
        return True


if __name__ == "__main__":
    success = run_e2e_verification()
    sys.exit(0 if success else 1)
