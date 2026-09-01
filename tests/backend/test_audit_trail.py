"""Unit and integration tests for Audit Trail and Compliance Timeline (Phase 10)."""

import pytest
from fastapi.testclient import TestClient

from backend.database.repository import DatabaseAuditRepository


def test_audit_event_logging_and_query():
    """Verify logging and querying immutable audit events."""
    repo = DatabaseAuditRepository()

    event = repo.log_event(
        event_type="PAYROLL_UPLOADED",
        analysis_id="anl_audit_test_001",
        actor_id="test_admin",
        metadata={"filename": "test_payroll.csv", "rows": 50},
        request_id="req_audit_001",
    )
    assert event.event_id.startswith("evt_")
    assert event.event_type == "PAYROLL_UPLOADED"

    timeline = repo.get_events_for_analysis("anl_audit_test_001")
    assert len(timeline) >= 1
    assert timeline[0]["event_type"] == "PAYROLL_UPLOADED"
    assert timeline[0]["actor_id"] == "test_admin"


def test_audit_api_endpoints(client: TestClient):
    """Verify GET /api/v1/audit/events and GET /api/v1/audit/analysis/{id}."""
    # 1. List platform events
    res = client.get("/api/v1/audit/events?limit=10")
    assert res.status_code == 200
    events = res.json()
    assert isinstance(events, list)

    # 2. Get events for demo analysis
    demo_res = client.get("/api/v1/audit/analysis/anl_demo_202406")
    assert demo_res.status_code == 200
    assert isinstance(demo_res.json(), list)
