"""Unit and integration tests for Asynchronous Large Batch Processing (Phase 10)."""

import time
import pytest
from fastapi.testclient import TestClient

from backend.schemas.analysis import AnalysisStatus
from backend.services.job_manager import JobManager


def test_async_batch_job_submission(client: TestClient, sample_payroll_records):
    """Verify submitting an asynchronous batch analysis returns QUEUED status and job ID."""
    payload = {
        "records": sample_payroll_records,
        "payroll_period": "2024-06",
        "jurisdiction": "INDIA",
    }
    response = client.post("/api/v1/payroll/analyze?async_mode=true", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert data["status"] in ("QUEUED", "RUNNING", "COMPLETED")

    job_id = data["analysis_id"]

    # Poll status until complete (or max 5 seconds)
    completed = False
    for _ in range(25):
        poll_res = client.get(f"/api/v1/payroll/analysis/{job_id}")
        assert poll_res.status_code == 200
        poll_data = poll_res.json()
        if poll_data.get("status") == "COMPLETED" and "summary" in poll_data:
            completed = True
            assert poll_data["summary"]["records_analyzed"] == 2
            break
        time.sleep(0.2)

    assert completed, "Async job did not complete in expected time window."


def test_job_manager_status_nonexistent():
    """Verify JobManager handles non-existent job gracefully."""
    job_mgr = JobManager.get_instance()
    status_data = job_mgr.get_job_status("non_existent_job_12345")
    assert status_data["status"] == "NOT_FOUND"


def test_async_batch_job_failure(monkeypatch, client: TestClient, sample_payroll_records):
    """Verify that when a background task fails, job status transitions to FAILED with error message."""
    from backend.services.analysis_service import AnalysisService

    def mock_failing_analyze(*args, **kwargs):
        raise RuntimeError("Simulated pipeline crash for async failure mode test")

    monkeypatch.setattr(AnalysisService, "analyze_payroll", mock_failing_analyze)

    payload = {
        "records": sample_payroll_records,
        "payroll_period": "2024-06",
        "jurisdiction": "INDIA",
    }
    response = client.post("/api/v1/payroll/analyze?async_mode=true", json=payload)
    assert response.status_code == 200
    job_id = response.json()["analysis_id"]

    failed = False
    for _ in range(25):
        poll_res = client.get(f"/api/v1/payroll/analysis/{job_id}")
        assert poll_res.status_code == 200
        poll_data = poll_res.json()
        if poll_data.get("status") == "FAILED":
            failed = True
            assert "Simulated pipeline crash" in poll_data.get("message", "")
            break
        time.sleep(0.2)

    assert failed, "Async job did not transition to FAILED status upon exception."

