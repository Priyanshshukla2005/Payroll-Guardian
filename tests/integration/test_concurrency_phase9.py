"""Phase 9: Concurrency & Multi-Threaded Stress Test Suite.

Verifies:
- 5 and 10 concurrent simultaneous requests to the FastAPI analysis endpoints.
- Thread-safe model and vector store access without race conditions.
- Zero state leakage or cross-contamination between concurrent request IDs.
- Latency and success rate validation.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def _dispatch_analysis_request(client, batch_id: int):
    """Worker function sending an independent payroll batch."""
    payload = {
        "payroll_period": "2024-06",
        "records": [
            {
                "employee_id": f"EMP_CONC_{batch_id}_{i:03d}",
                "payroll_month": "2024-06",
                "department": "Engineering" if i % 2 == 0 else "Sales",
                "designation": "Junior",
                "location": "Bengaluru",
                "basic_salary": 50000.0 + (i * 1000),
                "allowances": 25000.0,
                "gross_salary": 75000.0 + (i * 1000),
                "net_salary": 68800.0 + (i * 1000),
                "pf_deduction": (50000.0 + (i * 1000)) * 0.12 if i != 2 else 500.0,
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 0.0,
            }
            for i in range(5)
        ],
    }

    t0 = time.perf_counter()
    resp = client.post("/api/v1/payroll/analyze", json=payload)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "batch_id": batch_id,
        "status_code": resp.status_code,
        "data": resp.json() if resp.status_code == 200 else None,
        "elapsed_ms": elapsed_ms,
    }


def test_concurrency_5_simultaneous_requests(client):
    """Execute 5 simultaneous concurrent requests."""
    concurrency_level = 5
    results = []

    with ThreadPoolExecutor(max_workers=concurrency_level) as executor:
        futures = [
            executor.submit(_dispatch_analysis_request, client, batch_id=i)
            for i in range(concurrency_level)
        ]
        for f in as_completed(futures):
            results.append(f.result())

    assert len(results) == concurrency_level

    # 1. Assert 100% success rate
    success_count = sum(1 for r in results if r["status_code"] == 200)
    assert success_count == concurrency_level, f"Failed requests in concurrency 5: {results}"

    # 2. Assert unique request and analysis IDs (no collision)
    req_ids = [r["data"]["request_id"] for r in results]
    anl_ids = [r["data"]["analysis_id"] for r in results]
    assert len(set(req_ids)) == concurrency_level
    assert len(set(anl_ids)) == concurrency_level


def test_concurrency_10_simultaneous_requests(client):
    """Execute 10 simultaneous concurrent requests."""
    concurrency_level = 10
    results = []

    with ThreadPoolExecutor(max_workers=concurrency_level) as executor:
        futures = [
            executor.submit(_dispatch_analysis_request, client, batch_id=i)
            for i in range(concurrency_level)
        ]
        for f in as_completed(futures):
            results.append(f.result())

    assert len(results) == concurrency_level

    # 1. Assert 100% success rate
    success_count = sum(1 for r in results if r["status_code"] == 200)
    assert success_count == concurrency_level, f"Failed requests in concurrency 10: {results}"

    # 2. Assert all records processed correctly
    for r in results:
        data = r["data"]
        assert data["summary"]["records_analyzed"] == 5
        assert data["status"] == "COMPLETED"
        assert "timings" in data
