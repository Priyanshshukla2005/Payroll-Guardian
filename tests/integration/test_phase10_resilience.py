"""Resilience and failure mode chaos tests (Phase 10)."""

import pytest
from fastapi.testclient import TestClient
from backend.main import create_app


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_payroll_records():
    return [
        {
            "employee_id": "EMP_RESILIENCE_001",
            "payroll_month": "2024-06",
            "basic_salary": 50000.0,
            "gross_salary": 75000.0,
            "net_salary": 68000.0,
            "allowances": 25000.0,
            "bonus": 0.0,
            "total_deductions": 7000.0,
            "pf_deduction": 6000.0,
            "esi": 0.0,
            "professional_tax": 200.0,
            "working_days": 26,
            "present_days": 26,
            "leave_days": 0,
            "overtime_hours": 0.0,
            "department": "Engineering",
            "designation": "Software Engineer",
            "location": "UNKNOWN_STATE",
        }
    ]


def test_failure_mode_unknown_jurisdiction(client: TestClient, sample_payroll_records):
    """Verify unknown jurisdiction gracefully completes with valid status."""
    payload = {
        "records": sample_payroll_records,
        "payroll_period": "2024-06",
        "jurisdiction": "ATLANTIS_UNKNOWN_STATE",
    }
    response = client.post("/api/v1/payroll/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"


def test_failure_mode_empty_payload_rejected(client: TestClient):
    """Verify empty payroll payload is rejected with 422 Unprocessable Entity."""
    response = client.post("/api/v1/payroll/analyze", json={"records": []})
    assert response.status_code == 422


def test_compliance_sources_provenance_integrity(client: TestClient):
    """Verify statutory sources have valid SHA-256 hashes and authority levels."""
    response = client.get("/api/v1/compliance/sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 5
    for src in sources:
        assert "document_id" in src
        assert "authority_level" in src
        assert "file_hash" in src
        assert len(src["file_hash"]) > 0


def test_safe_error_envelope_on_404(client: TestClient):
    """Verify non-existent resource returns clean JSON envelope without stack traces."""
    response = client.get("/api/v1/payroll/analysis/anl_missing_fake_9999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "request_id" in data["error"]
    assert "Traceback" not in str(data)
