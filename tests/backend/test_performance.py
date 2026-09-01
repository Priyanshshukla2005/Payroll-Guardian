"""Performance, throughput, and scalability benchmark tests (Phase 7)."""

import time
import pandas as pd
import pytest
from fastapi.testclient import TestClient


def _generate_synthetic_batch(n_records: int) -> list:
    """Generate n_records synthetic payroll records in memory."""
    records = []
    for i in range(n_records):
        emp_id = f"EMP_PERF_{i:05d}"
        basic = 30000.0 + (i % 50) * 1000.0
        # Inject ~5% anomalies
        is_anom = (i % 20 == 0)
        pf = 1000.0 if is_anom else 0.12 * basic
        gross = basic * 1.5
        net = gross - pf - 200.0

        records.append({
            "employee_id": emp_id,
            "payroll_month": "2024-06",
            "basic_salary": basic,
            "gross_salary": gross,
            "net_salary": net,
            "allowances": basic * 0.5,
            "bonus": 0.0,
            "total_deductions": pf + 200.0,
            "pf_deduction": pf,
            "esi": 0.0,
            "professional_tax": 200.0,
            "working_days": 26,
            "present_days": 26,
            "leave_days": 0,
            "overtime_hours": 0.0,
            "department": "Engineering" if i % 2 == 0 else "Operations",
            "designation": "Staff",
            "location": "KARNATAKA",
        })
    return records


def test_performance_100_records(client: TestClient):
    records_100 = _generate_synthetic_batch(100)
    start = time.perf_counter()
    response = client.post("/api/v1/payroll/analyze", json={"records": records_100})
    duration = time.perf_counter() - start

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["records_analyzed"] == 100

    rps = 100 / duration
    print(f"\n[PERFORMANCE] 100 records: {duration:.3f}s ({rps:.1f} records/sec)")
    assert duration < 5.0  # Must process 100 records well under 5 seconds


def test_performance_1000_records(client: TestClient):
    records_1000 = _generate_synthetic_batch(1000)
    start = time.perf_counter()
    response = client.post("/api/v1/payroll/analyze", json={"records": records_1000})
    duration = time.perf_counter() - start

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["records_analyzed"] == 1000

    rps = 1000 / duration
    print(f"\n[PERFORMANCE] 1,000 records: {duration:.3f}s ({rps:.1f} records/sec)")
    assert duration < 15.0  # Must process 1,000 records well under 15 seconds
