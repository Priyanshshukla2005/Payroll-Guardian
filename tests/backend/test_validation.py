"""Unit tests for Pydantic input validation and data bounds (Phase 7)."""

import pytest
from fastapi.testclient import TestClient


def test_validation_empty_records_list(client: TestClient):
    payload = {"records": []}
    response = client.post("/api/v1/payroll/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_validation_negative_salary(client: TestClient):
    payload = {
        "records": [
            {
                "employee_id": "EMP_NEG",
                "payroll_month": "2024-06",
                "basic_salary": -5000.0,  # Negative salary invalid
                "gross_salary": 20000.0,
                "net_salary": 18000.0,
            }
        ]
    }
    response = client.post("/api/v1/payroll/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_validation_invalid_working_days_bounds(client: TestClient):
    payload = {
        "records": [
            {
                "employee_id": "EMP_DAYS",
                "payroll_month": "2024-06",
                "basic_salary": 30000.0,
                "gross_salary": 35000.0,
                "net_salary": 32000.0,
                "working_days": 45,  # Exceeds max 31 days
            }
        ]
    }
    response = client.post("/api/v1/payroll/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
