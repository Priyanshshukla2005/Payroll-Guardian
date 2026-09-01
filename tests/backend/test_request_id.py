"""Unit tests for Request-ID propagation and header tracing (Phase 7)."""

import pytest
from fastapi.testclient import TestClient


def test_request_id_generated_automatically(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")


def test_custom_request_id_propagated(client: TestClient):
    custom_id = "req_custom_trace_987654321"
    response = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


def test_request_id_in_analysis_response(client: TestClient, sample_payroll_records):
    custom_id = "req_audit_batch_202406"
    payload = {"records": sample_payroll_records}
    response = client.post(
        "/api/v1/payroll/analyze",
        json=payload,
        headers={"X-Request-ID": custom_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == custom_id
