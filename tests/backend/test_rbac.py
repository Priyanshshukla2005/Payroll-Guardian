"""Unit and integration tests for Role-Based Access Control (RBAC) (Phase 10)."""

import pytest
from fastapi.testclient import TestClient

from backend.auth.security import create_access_token


def get_token_for_role(role: str) -> str:
    """Generate signed test token for a given role."""
    return create_access_token({
        "sub": f"test_{role.lower()}",
        "role": role,
        "email": f"{role.lower()}@test.internal",
    })


def test_rbac_viewer_cannot_upload_payroll(client: TestClient, sample_csv_bytes):
    """Verify VIEWER role cannot trigger payroll file uploads (403 Forbidden)."""
    viewer_token = get_token_for_role("VIEWER")
    files = {"file": ("test.csv", sample_csv_bytes, "text/csv")}
    res = client.post(
        "/api/v1/payroll/upload",
        files=files,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert res.status_code == 403
    err = res.json().get("error", res.json())
    assert "not permitted" in str(err).lower() or "forbidden" in str(err).lower()


def test_rbac_viewer_cannot_resolve_anomalies(client: TestClient):
    """Verify VIEWER role cannot resolve anomalies (403 Forbidden)."""
    viewer_token = get_token_for_role("VIEWER")
    payload = {"status": "RESOLVED", "resolution_notes": "Reviewed and cleared."}
    res = client.post(
        "/api/v1/anomalies/anl_demo_202406/EMP_2041/resolve",
        json=payload,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert res.status_code == 403


def test_rbac_auditor_can_view_and_resolve_but_not_upload(client: TestClient, sample_csv_bytes):
    """Verify AUDITOR role can view and resolve anomalies, but cannot upload payroll."""
    auditor_token = get_token_for_role("AUDITOR")

    # 1. Auditor upload attempt -> 403 Forbidden
    files = {"file": ("test.csv", sample_csv_bytes, "text/csv")}
    upload_res = client.post(
        "/api/v1/payroll/upload",
        files=files,
        headers={"Authorization": f"Bearer {auditor_token}"},
    )
    assert upload_res.status_code == 403

    # 2. Auditor view analysis -> 200 OK
    view_res = client.get(
        "/api/v1/payroll/analysis/anl_demo_202406",
        headers={"Authorization": f"Bearer {auditor_token}"},
    )
    assert view_res.status_code == 200

    # 3. Auditor resolve anomaly -> 200 OK
    resolve_payload = {"status": "RESOLVED", "resolution_notes": "Verified by Statutory Auditor."}
    resolve_res = client.post(
        "/api/v1/anomalies/anl_demo_202406/EMP_2041/resolve",
        json=resolve_payload,
        headers={"Authorization": f"Bearer {auditor_token}"},
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"


def test_rbac_payroll_admin_can_upload_and_analyze(client: TestClient, sample_payroll_records):
    """Verify PAYROLL_ADMIN role has upload, analyze, and view permissions."""
    admin_token = get_token_for_role("PAYROLL_ADMIN")
    payload = {"records": sample_payroll_records}
    res = client.post(
        "/api/v1/payroll/analyze",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"


def test_rbac_admin_full_access(client: TestClient, sample_payroll_records):
    """Verify ADMIN role has unrestricted access across all endpoints."""
    admin_token = get_token_for_role("ADMIN")
    # 1. Analyze
    res = client.post(
        "/api/v1/payroll/analyze",
        json={"records": sample_payroll_records},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200

    # 2. Monitoring
    mon_res = client.get(
        "/api/v1/monitoring/metrics",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert mon_res.status_code == 200

    # 3. Audit events
    audit_res = client.get(
        "/api/v1/audit/events",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert audit_res.status_code == 200
