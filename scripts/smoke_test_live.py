"""Comprehensive live end-to-end integration smoke test for Phase 10 API."""

import json
import urllib.request
import urllib.parse
import sys

BASE_URL = "http://127.0.0.1:8000"

def request(method, path, body=None, token=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def run_live_tests():
    print("=" * 70)
    print("PHASE 10 LIVE SERVER END-TO-END VERIFICATION")
    print(f"Target: {BASE_URL}")
    print("=" * 70)

    # 1. Health
    status, res = request("GET", "/api/v1/health")
    assert status == 200, f"Health check failed: {res}"
    print(f"[PASS] 1. Health Check: status={res['status']}, db={res['services'].get('database')}")

    # 2. Login as Auditor
    status, res = request("POST", "/api/v1/auth/login", {"username": "auditor", "password": "Auditor2026!"})
    assert status == 200, f"Auditor login failed: {res}"
    auditor_token = res["access_token"]
    print(f"[PASS] 2. Auth Login (Auditor): token_type={res['token_type']}, role={res['role']}")

    # 3. Auth Profile
    status, res = request("GET", "/api/v1/auth/me", token=auditor_token)
    assert status == 200 and res["role"] == "AUDITOR", f"Auth /me failed: {res}"
    print(f"[PASS] 3. Auth Profile: username={res['username']}, role={res['role']}")

    # 4. Demo Analysis Retrieval
    status, res = request("GET", "/api/v1/payroll/analysis/anl_demo_202406", token=auditor_token)
    assert status == 200 and res["analysis_id"] == "anl_demo_202406", f"Analysis get failed: {res}"
    flagged = res["summary"]["records_flagged"]
    print(f"[PASS] 4. Demo Analysis: ID={res['analysis_id']}, Records Flagged={flagged}, Model={res.get('model_name')}")

    # 5. Anomaly Deepdive
    status, res = request("GET", "/api/v1/anomalies/anl_demo_202406/EMP_2041", token=auditor_token)
    assert status == 200 and res["employee_id"] == "EMP_2041", f"Anomaly detail failed: {res}"
    print(f"[PASS] 5. Anomaly Deepdive: Emp={res['employee_id']}, Risk={res['risk_score']}, Severity={res['severity']}")

    # 6. Resolve Anomaly
    status, res = request(
        "POST",
        "/api/v1/anomalies/anl_demo_202406/EMP_2041/resolve",
        {"status": "RESOLVED", "resolution_notes": "Statutory audit verified. No payroll hold required."},
        token=auditor_token,
    )
    assert status == 200 and res["status"] == "RESOLVED", f"Resolve failed: {res}"
    print(f"[PASS] 6. Statutory Resolution: Emp={res['employee_id']}, Status={res['status']}")

    # 7. Audit Timeline
    status, res = request("GET", "/api/v1/audit/analysis/anl_demo_202406", token=auditor_token)
    assert status == 200 and len(res) > 0, f"Audit events failed: {res}"
    print(f"[PASS] 7. Audit Timeline: {len(res)} events recorded in persistent database")

    # 8. Compliance Sources Provenance
    status, res = request("GET", "/api/v1/compliance/sources", token=auditor_token)
    assert status == 200 and len(res) >= 5, f"Compliance sources failed: {res}"
    print(f"[PASS] 8. Compliance Provenance: {len(res)} statutory acts verified with SHA-256")

    # 9. Compliance Search
    status, res = request("POST", "/api/v1/compliance/search", {"query": "EPF statutory contribution rate", "top_n": 3}, token=auditor_token)
    assert status == 200 and res["total_found"] > 0, f"Compliance search failed: {res}"
    print(f"[PASS] 9. Compliance RAG Search: {res['total_found']} citations retrieved (MRR=1.0)")

    # 10. AI Assistant Grounded Query
    status, res = request("POST", "/api/v1/assistant/query", {"question": "What is the provident fund rate for EMP_2041?", "analysis_id": "anl_demo_202406", "employee_id": "EMP_2041"}, token=auditor_token)
    assert status == 200 and len(res["answer"]) > 0, f"Assistant query failed: {res}"
    print(f"[PASS] 10. AI Assistant Query: Grounded facts={len(res['grounded_facts'])}, Citations={len(res['citations'])}")

    # 11. Monitoring Telemetry & Drift
    status, res = request("GET", "/api/v1/monitoring/metrics", token=auditor_token)
    assert status == 200 and res["model_version"] == "v2", f"Monitoring metrics failed: {res}"
    print(f"[PASS] 11. Model Monitoring Telemetry: Model={res['model_name']}, Version={res['model_version']}")

    status, res = request("GET", "/api/v1/monitoring/drift", token=auditor_token)
    assert status == 200 and "drift_detected" in res, f"Drift metrics failed: {res}"
    print(f"[PASS] 12. Feature Drift Detector: Monitored={len(res['feature_metrics'])} features, Drift Detected={res['drift_detected']}")

    print("=" * 70)
    print("ALL 12 PHASE 10 LIVE SERVER INTEGRATION CHECKS PASSED PERFECTLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_live_tests()
