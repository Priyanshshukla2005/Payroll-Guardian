"""Unit tests for health, liveness, and readiness endpoints (Phase 7)."""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert data["docs"] == "/docs"
    assert "/api/v1/health" in data["health"]


def test_health_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["services"]["ai"] == "available"
    assert data["services"]["rag"] == "available"
    assert data["services"]["llm"] == "available"


def test_liveness_endpoint(client: TestClient):
    response = client.get("/api/v1/health/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"


def test_readiness_endpoint(client: TestClient):
    response = client.get("/api/v1/health/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["model_version"] == "v2"
    assert data["rag_indexed_chunks"] > 0


def test_direct_live_endpoint(client: TestClient):
    """Verify GET /api/v1/live returns live status."""
    response = client.get("/api/v1/live")
    assert response.status_code == 200
    assert response.json()["status"] == "live"


def test_direct_ready_endpoint(client: TestClient):
    """Verify GET /api/v1/ready returns ready status."""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_failure_returns_503(monkeypatch, client: TestClient):
    """Verify that if a critical service is unavailable, readiness probe returns 503."""
    import backend.api.health as health_module

    monkeypatch.setattr(health_module, "check_db_health", lambda: "unavailable")

    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unready"
    assert data["database"] == "disconnected"

