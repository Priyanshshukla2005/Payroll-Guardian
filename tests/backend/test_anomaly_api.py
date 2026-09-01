"""Unit tests for anomaly query and drilldown API endpoints (Phase 7)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def populated_analysis_id(client: TestClient, sample_payroll_records):
    payload = {"records": sample_payroll_records}
    res = client.post("/api/v1/payroll/analyze", json=payload)
    return res.json()["analysis_id"]


def test_list_anomalies_for_analysis(client: TestClient, populated_analysis_id):
    response = client.get(f"/api/v1/anomalies/{populated_analysis_id}")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["employee_id"] == "EMP_TEST_002"
    assert "explanation" in data[0]
    assert "compliance" in data[0]


def test_list_anomalies_with_severity_filter(client: TestClient, populated_analysis_id):
    response = client.get(f"/api/v1/anomalies/{populated_analysis_id}?severity=CRITICAL")
    assert response.status_code == 200
    data = response.json()
    for item in data:
        assert item["severity"] == "CRITICAL"


def test_get_employee_anomaly_detail_success(client: TestClient, populated_analysis_id):
    response = client.get(f"/api/v1/anomalies/{populated_analysis_id}/EMP_TEST_002")
    assert response.status_code == 200

    data = response.json()
    assert data["employee_id"] == "EMP_TEST_002"
    assert data["risk_score"] > 0.45
    assert len(data["evidence"]) >= 1
    assert data["compliance"]["status"] == "FOUND"


def test_get_employee_anomaly_detail_not_flagged(client: TestClient, populated_analysis_id):
    # EMP_TEST_001 was a clean/normal employee record
    response = client.get(f"/api/v1/anomalies/{populated_analysis_id}/EMP_TEST_001")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
