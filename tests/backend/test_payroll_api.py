"""Unit tests for payroll ingestion and analysis API endpoints (Phase 7)."""

import io
import json
import pytest
from fastapi.testclient import TestClient


def test_analyze_payroll_json_batch(client: TestClient, sample_payroll_records):
    payload = {
        "records": sample_payroll_records,
        "payroll_period": "2024-06",
        "jurisdiction": "INDIA",
    }
    response = client.post("/api/v1/payroll/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "request_id" in data
    assert "analysis_id" in data
    assert data["status"] == "COMPLETED"
    assert data["summary"]["records_analyzed"] == 2
    assert data["summary"]["records_flagged"] >= 1

    # Verify second record (PF Mismatch) was flagged
    flagged_ids = [a["employee_id"] for a in data["anomalies"]]
    assert "EMP_TEST_002" in flagged_ids


def test_analyze_payroll_csv_upload(client: TestClient, sample_csv_bytes):
    files = {"file": ("test_payroll.csv", sample_csv_bytes, "text/csv")}
    response = client.post("/api/v1/payroll/upload", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["summary"]["records_analyzed"] == 2
    assert "anomalies" in data
    assert len(data["anomalies"]) >= 1


def test_analyze_payroll_json_upload(client: TestClient, sample_payroll_records):
    json_bytes = json.dumps(sample_payroll_records).encode("utf-8")
    files = {"file": ("test_payroll.json", json_bytes, "application/json")}
    response = client.post("/api/v1/payroll/upload", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["summary"]["records_analyzed"] == 2


def test_get_analysis_by_id_success(client: TestClient, sample_payroll_records):
    # 1. Create analysis
    payload = {"records": sample_payroll_records}
    post_res = client.post("/api/v1/payroll/analyze", json=payload)
    analysis_id = post_res.json()["analysis_id"]

    # 2. Retrieve analysis
    get_res = client.get(f"/api/v1/payroll/analysis/{analysis_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["analysis_id"] == analysis_id
    assert data["summary"]["records_analyzed"] == 2


def test_get_analysis_by_id_not_found(client: TestClient):
    response = client.get("/api/v1/payroll/analysis/anl_nonexistent_99999")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
