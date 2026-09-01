"""Test fixtures and TestClient setup for backend tests (Phase 7)."""

import io
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.dependencies.services import ModelManager
from backend.main import create_app


@pytest.fixture(scope="session")
def app_instance():
    """Create and initialize the FastAPI application."""
    model_mgr = ModelManager.get_instance()
    model_mgr.initialize()
    app = create_app()
    return app


@pytest.fixture(scope="session")
def client(app_instance):
    """Provide a TestClient instance for API tests."""
    with TestClient(app_instance) as c:
        yield c


@pytest.fixture
def sample_payroll_records():
    """Return a list of valid sample payroll dictionaries."""
    return [
        {
            "employee_id": "EMP_TEST_001",
            "payroll_month": "2024-06",
            "basic_salary": 50000.0,
            "gross_salary": 75000.0,
            "net_salary": 68000.0,
            "allowances": 25000.0,
            "bonus": 0.0,
            "total_deductions": 7000.0,
            "pf_deduction": 6000.0,
            "esi": 0.0,
            "professional_tax": 200.0,
            "working_days": 26,
            "present_days": 26,
            "leave_days": 0,
            "overtime_hours": 0.0,
            "department": "Engineering",
            "designation": "Software Engineer",
            "location": "KARNATAKA",
        },
        {
            "employee_id": "EMP_TEST_002",
            "payroll_month": "2024-06",
            "basic_salary": 40000.0,
            "gross_salary": 60000.0,
            "net_salary": 58800.0,
            "allowances": 20000.0,
            "bonus": 0.0,
            "total_deductions": 1200.0,
            "pf_deduction": 1000.0,  # Severe PF Under-deduction anomaly
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


@pytest.fixture
def sample_csv_bytes(sample_payroll_records):
    """Return CSV formatted bytes of sample payroll records."""
    df = pd.DataFrame(sample_payroll_records)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")
