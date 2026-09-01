"""Unit tests for standardized error response structures (Phase 7)."""

import pytest
from fastapi.testclient import TestClient


def test_standardized_404_error_format(client: TestClient):
    response = client.get("/api/v1/payroll/analysis/anl_missing_404")
    assert response.status_code == 404
    data = response.json()

    assert "error" in data
    err = data["error"]
    assert err["code"] == "RESOURCE_NOT_FOUND"
    assert "not found" in err["message"].lower()
    assert "request_id" in err
    assert err["status_code"] == 404


def test_standardized_422_error_format(client: TestClient):
    response = client.post("/api/v1/payroll/analyze", json={"invalid_key": 123})
    assert response.status_code == 422
    data = response.json()

    assert "error" in data
    err = data["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert "request_id" in err
    assert err["status_code"] == 422
    assert "details" in err
