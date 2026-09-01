"""Unit and integration tests for Model Monitoring and Drift Telemetry API (Phase 10)."""

import pytest
from fastapi.testclient import TestClient


def test_monitoring_metrics_endpoint(client: TestClient):
    """Verify GET /api/v1/monitoring/metrics returns telemetry and versioning metadata."""
    response = client.get("/api/v1/monitoring/metrics")
    assert response.status_code == 200
    data = response.json()

    assert data["model_name"] == "HybridPayrollDetector_v2"
    assert data["model_version"] == "v2"
    assert data["model_threshold"] == 0.45
    assert data["feature_schema_version"] == "features_v1"
    assert data["rag_knowledge_version"] == "rag_2024_06"
    assert "metrics" in data
    assert "severity_counts" in data["metrics"]


def test_monitoring_drift_endpoint(client: TestClient):
    """Verify GET /api/v1/monitoring/drift returns drift assessment."""
    response = client.get("/api/v1/monitoring/drift")
    assert response.status_code == 200
    data = response.json()
    assert "drift_detected" in data
    assert "feature_metrics" in data
