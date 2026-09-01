"""Full end-to-end integration test across API -> Detection -> RAG -> LLM (Phase 7)."""

import pytest
from fastapi.testclient import TestClient


def test_full_pipeline_end_to_end(client: TestClient):
    # 1. Prepare batch containing clean and anomalous employee records
    records = [
        {
            "employee_id": "EMP_INTEG_NORMAL",
            "payroll_month": "2024-06",
            "basic_salary": 45000.0,
            "gross_salary": 65000.0,
            "net_salary": 59400.0,
            "allowances": 20000.0,
            "bonus": 0.0,
            "total_deductions": 5600.0,
            "pf_deduction": 5400.0,  # Exactly 12% of basic
            "esi": 0.0,
            "professional_tax": 200.0,
            "working_days": 26,
            "present_days": 26,
            "leave_days": 0,
            "overtime_hours": 0.0,
            "department": "Engineering",
            "designation": "Staff Engineer",
            "location": "KARNATAKA",
        },
        {
            "employee_id": "EMP_INTEG_PF_ANOMALY",
            "payroll_month": "2024-06",
            "basic_salary": 40000.0,
            "gross_salary": 60000.0,
            "net_salary": 58600.0,
            "allowances": 20000.0,
            "bonus": 0.0,
            "total_deductions": 1400.0,
            "pf_deduction": 1200.0,  # 3% instead of 12% -> Severe statutory anomaly
            "esi": 0.0,
            "professional_tax": 200.0,
            "working_days": 26,
            "present_days": 26,
            "leave_days": 0,
            "overtime_hours": 0.0,
            "department": "Operations",
            "designation": "Associate",
            "location": "MAHARASHTRA",
        },
    ]

    # 2. Execute Batch Analysis
    analyze_res = client.post("/api/v1/payroll/analyze", json={"records": records})
    assert analyze_res.status_code == 200

    data = analyze_res.json()
    assert data["status"] == "COMPLETED"
    assert data["summary"]["records_analyzed"] == 2
    assert data["summary"]["records_flagged"] == 1

    anl_id = data["analysis_id"]
    flagged = data["anomalies"][0]

    assert flagged["employee_id"] == "EMP_INTEG_PF_ANOMALY"
    assert flagged["severity"] in ["HIGH", "CRITICAL"]
    assert "RULE_PF_MISMATCH" in flagged["rule_violations"]
    assert flagged["compliance"]["status"] == "FOUND"
    assert any("EPFO" in c["document_id"] for c in flagged["compliance"]["sources"])
    assert "explanation" in flagged
    assert bool(flagged["explanation"]["summary"])

    # 3. Retrieve Analysis by ID
    get_res = client.get(f"/api/v1/payroll/analysis/{anl_id}")
    assert get_res.status_code == 200
    assert get_res.json()["analysis_id"] == anl_id

    # 4. Drilldown into specific anomaly
    detail_res = client.get(f"/api/v1/anomalies/{anl_id}/EMP_INTEG_PF_ANOMALY")
    assert detail_res.status_code == 200
    assert detail_res.json()["employee_id"] == "EMP_INTEG_PF_ANOMALY"

    # 5. Query Assistant regarding the flagged record
    ask_res = client.post(
        "/api/v1/assistant/query",
        json={
            "question": "Why was EMP_INTEG_PF_ANOMALY flagged?",
            "analysis_id": anl_id,
            "employee_id": "EMP_INTEG_PF_ANOMALY",
        },
    )
    assert ask_res.status_code == 200
    ask_data = ask_res.json()
    assert bool(ask_data["answer"])
    assert len(ask_data["suggested_next_steps"]) >= 1
