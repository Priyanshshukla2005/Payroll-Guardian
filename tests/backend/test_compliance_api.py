"""Unit tests for compliance knowledge search endpoints (Phase 7)."""

import pytest
from fastapi.testclient import TestClient


def test_compliance_search_pf_statute(client: TestClient):
    payload = {
        "query": "EPFO Provident Fund 12 percent basic salary contribution",
        "jurisdiction": "INDIA",
        "payroll_date": "2024-06-01",
        "topic": "PF",
        "top_n": 3,
    }
    response = client.post("/api/v1/compliance/search", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["total_found"] >= 1
    assert any(r["document_id"] == "EPFO_ACT_1952" for r in data["results"])


def test_compliance_search_unknown_jurisdiction(client: TestClient):
    payload = {
        "query": "Professional tax deduction slabs",
        "jurisdiction": "UNKNOWN",
        "payroll_date": "2024-06-01",
    }
    response = client.post("/api/v1/compliance/search", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "JURISDICTION_UNKNOWN"
    assert data["total_found"] == 0
    assert "geographic jurisdiction" in data["no_answer_reason"].lower()
