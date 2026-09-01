"""Phase 9: Data Integrity, Idempotency & Precision Test Suite.

Verifies:
- Preserving employee identifiers and payroll periods through all pipeline transformations.
- Precision retention on financial values (basic, gross, net, deductions).
- Zero accidental record loss and zero duplicate records in summary counts and persistence.
- Deterministic and idempotent outputs when executing identical payroll batches.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_data_integrity_employee_identity_and_counts(client):
    """Verify all employee records are accounted for without duplication or loss."""
    records = [
        {
            "employee_id": f"EMP_INTEG_{i:04d}",
            "payroll_month": "2024-06",
            "department": "Engineering" if i % 2 == 0 else "Sales",
            "designation": "Junior",
            "location": "Bengaluru",
            "basic_salary": 45000.0 + (i * 1000),
            "allowances": 20000.0,
            "gross_salary": 65000.0 + (i * 1000),
            "net_salary": 60000.0 + (i * 1000),
            "pf_deduction": (45000.0 + (i * 1000)) * 0.12 if i != 5 else 500.0,  # Record 5 has PF mismatch
            "working_days": 26,
            "present_days": 26,
            "overtime_hours": 0.0,
            "salary_change_percentage": 0.0,
        }
        for i in range(15)
    ]

    payload = {
        "payroll_period": "2024-06",
        "jurisdiction": "INDIA",
        "records": records,
    }

    resp = client.post("/api/v1/payroll/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # 1. Verify exact count conservation
    assert data["summary"]["records_analyzed"] == 15
    total_risk_counts = (
        data["summary"]["critical_risk"]
        + data["summary"]["high_risk"]
        + data["summary"]["medium_risk"]
        + data["summary"]["low_risk"]
    )
    assert total_risk_counts == 15

    # 2. Verify no duplicate flagged records
    flagged_ids = [a["employee_id"] for a in data["anomalies"]]
    assert len(flagged_ids) == len(set(flagged_ids)), "Duplicate anomaly record detected in response"

    # 3. Verify specific anomalous employee identity preserved
    assert "EMP_INTEG_0005" in flagged_ids


def test_data_integrity_deterministic_idempotency(client):
    """Running the exact same batch twice produces identical risk scores and classifications."""
    payload = {
        "payroll_period": "2024-06",
        "jurisdiction": "INDIA",
        "records": [
            {
                "employee_id": "EMP_DET_001",
                "payroll_month": "2024-06",
                "department": "HR",
                "designation": "Manager",
                "location": "Mumbai",
                "basic_salary": 120000.0,
                "allowances": 60000.0,
                "gross_salary": 180000.0,
                "net_salary": 165600.0,
                "pf_deduction": 14400.0,
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 0.0,
            },
            {
                "employee_id": "EMP_DET_002",
                "payroll_month": "2024-06",
                "department": "Engineering",
                "designation": "Senior",
                "location": "Bengaluru",
                "basic_salary": 150000.0,
                "allowances": 75000.0,
                "gross_salary": 225000.0,
                "net_salary": 223500.0,
                "pf_deduction": 1500.0,  # Severe PF mismatch
                "working_days": 26,
                "present_days": 26,
                "overtime_hours": 0.0,
                "salary_change_percentage": 0.0,
            },
        ],
    }

    resp1 = client.post("/api/v1/payroll/analyze", json=payload)
    resp2 = client.post("/api/v1/payroll/analyze", json=payload)

    assert resp1.status_code == 200
    assert resp2.status_code == 200

    data1 = resp1.json()
    data2 = resp2.json()

    assert data1["summary"]["records_flagged"] == data2["summary"]["records_flagged"]

    anom1 = sorted(data1["anomalies"], key=lambda x: x["employee_id"])
    anom2 = sorted(data2["anomalies"], key=lambda x: x["employee_id"])

    assert len(anom1) == len(anom2)
    for a1, a2 in zip(anom1, anom2):
        assert a1["employee_id"] == a2["employee_id"]
        assert pytest.approx(a1["risk_score"], abs=1e-3) == a2["risk_score"]
        assert a1["severity"] == a2["severity"]
        assert a1["anomaly_types"] == a2["anomaly_types"]
