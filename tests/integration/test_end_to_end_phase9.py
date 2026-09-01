"""Phase 9: Comprehensive End-to-End Happy Path Integration Test Suite.

Verifies the entire lifecycle:
Client Request -> FastAPI Endpoint -> Validation -> Payroll Processing ->
Feature Generation (66 features) -> Hybrid AI Detection -> DetailedEvidenceCard ->
Compliance RAG Retrieval -> Grounded LLM Explanation -> Validator -> Response Schema -> Persistence.
"""

import io
import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.schemas.analysis import AnalysisResponse, AnalysisStatus


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_end_to_end_json_batch_happy_path(client):
    """Test full JSON batch payroll analysis through complete 9-stage pipeline."""
    payload = {
        "payroll_period": "2024-06",
        "jurisdiction": "INDIA",
        "records": [
            # 1. Normal record
            {
                "employee_id": "EMP_NORM_001",
                "payroll_month": "2024-06",
                "department": "Engineering",
                "designation": "Junior",
                "location": "Bengaluru",
                "basic_salary": 50000.0,
                "allowances": 25000.0,
                "gross_salary": 75000.0,
                "net_salary": 68800.0,
                "pf_deduction": 6000.0,  # 12% of 50000 = 6000 (Exact)
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 0.0,
            },
            # 2. Anomalous record: Statutory PF Mismatch
            {
                "employee_id": "EMP_ANOM_PF_002",
                "payroll_month": "2024-06",
                "department": "Finance",
                "designation": "Senior",
                "location": "Mumbai",
                "basic_salary": 100000.0,
                "allowances": 50000.0,
                "gross_salary": 150000.0,
                "net_salary": 148500.0,
                "pf_deduction": 1200.0,  # Expected 12000 -> Mismatch
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 0.0,
            },
            # 3. Anomalous record: Excessive Overtime Outlier
            {
                "employee_id": "EMP_ANOM_OT_003",
                "payroll_month": "2024-06",
                "department": "Operations",
                "designation": "Junior",
                "location": "Delhi-NCR",
                "basic_salary": 30000.0,
                "allowances": 15000.0,
                "gross_salary": 65000.0,
                "net_salary": 60000.0,
                "pf_deduction": 3600.0,
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 75.0,  # Cap is 50-60h -> Excessive
                "salary_change_percentage": 0.0,
            },
        ],
    }

    # 1. Dispatch Request
    resp = client.post("/api/v1/payroll/analyze", json=payload)
    assert resp.status_code == 200, f"Analysis failed: {resp.text}"

    data = resp.json()

    # 2. Verify Top-Level Structure
    assert "request_id" in data
    assert data["request_id"].startswith("req_")
    assert "analysis_id" in data
    assert data["analysis_id"].startswith("anl_")
    assert data["status"] == "COMPLETED"
    assert data["payroll_period"] == "2024-06"
    assert "model_version" in data
    assert data["model_version"] in ("HybridPayrollDetector_V2", "v2", "HybridPayrollDetector_V1")

    # 3. Verify Pipeline Timings Observability
    assert "timings" in data
    timings = data["timings"]
    assert "feature_generation_ms" in timings
    assert "detection_ms" in timings
    assert "rag_ms" in timings
    assert "llm_ms" in timings
    assert "total_ms" in timings
    assert timings["total_ms"] > 0

    # 4. Verify Summary Analytics
    summary = data["summary"]
    assert summary["records_analyzed"] == 3
    assert summary["records_flagged"] >= 2  # At least PF mismatch and OT outlier flagged
    assert summary["critical_risk"] + summary["high_risk"] + summary["medium_risk"] + summary["low_risk"] == 3

    # 5. Verify Anomalies and Grounded Explanations
    anomalies = data["anomalies"]
    flagged_ids = [a["employee_id"] for a in anomalies]
    assert "EMP_ANOM_PF_002" in flagged_ids

    # Find the PF anomaly
    pf_anomaly = next(a for a in anomalies if a["employee_id"] == "EMP_ANOM_PF_002")
    assert pf_anomaly["risk_score"] >= 0.45
    assert "RULE_PF_MISMATCH" in pf_anomaly["rule_violations"]
    assert pf_anomaly["severity"] in ["CRITICAL", "HIGH", "MEDIUM"]
    assert len(pf_anomaly["evidence"]) >= 1

    # Verify RAG compliance block
    compliance = pf_anomaly["compliance"]
    assert compliance["status"] in ["FOUND", "SUCCESS", "NO_RELIABLE_SOURCE_FOUND"]
    if compliance["status"] in ["FOUND", "SUCCESS"]:
        assert len(compliance["sources"]) >= 1
        assert any("EPFO" in s["document_id"] or "PF" in s["document_id"] for s in compliance["sources"])

    # Verify Grounded LLM explanation block
    explanation = pf_anomaly["explanation"]
    assert explanation["title"] is not None
    assert len(explanation["summary"]) > 10
    assert len(explanation["why_flagged"]) >= 1
    assert len(explanation["recommended_actions"]) >= 1
    assert "uncertainty" in explanation

    # 6. Verify Persistence and Retrieval by analysis_id
    anl_id = data["analysis_id"]
    get_resp = client.get(f"/api/v1/payroll/analysis/{anl_id}")
    assert get_resp.status_code == 200
    retrieved_data = get_resp.json()
    assert retrieved_data["analysis_id"] == anl_id
    assert retrieved_data["summary"]["records_analyzed"] == 3


def test_end_to_end_csv_upload_happy_path(client):
    """Test full file upload analysis flow with deterministic CSV data."""
    csv_content = (
        "employee_id,department,designation,location,basic_salary,allowances,gross_salary,net_salary,pf_deduction,working_days,present_days,overtime_hours,salary_change_percentage,payroll_month\n"
        "EMP_CSV_001,Engineering,Junior,Bengaluru,50000,25000,75000,68800,6000,26,26,0,0,2024-06\n"
        "EMP_CSV_002,HR,Senior,Mumbai,90000,40000,130000,128000,1000,26,26,0,0,2024-06\n"
    )

    files = {"file": ("payroll_june_2024.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    resp = client.post("/api/v1/payroll/upload", files=files)
    assert resp.status_code == 200, f"CSV upload failed: {resp.text}"

    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert data["summary"]["records_analyzed"] == 2
    assert data["payroll_period"] == "2024-06"
    assert len(data["anomalies"]) >= 1
