"""Comprehensive integration tests for Authentication, JWT Security, and RBAC (Phase 10)."""

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from backend.auth.rbac import UserRole
from backend.auth.security import create_access_token
from backend.dependencies.services import ModelManager
from backend.main import create_app


@pytest.fixture(scope="module")
def auth_client():
    """Create a clean TestClient for auth tests."""
    model_mgr = ModelManager.get_instance()
    model_mgr.initialize()
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_auth_login_success_all_roles(auth_client: TestClient):
    """Verify login success, token generation, and role assignment across all 4 roles."""
    roles = [
        ("admin", "AdminPassword2026!", UserRole.ADMIN),
        ("payroll_admin", "PayrollAdmin2026!", UserRole.PAYROLL_ADMIN),
        ("auditor", "Auditor2026!", UserRole.AUDITOR),
        ("viewer", "Viewer2026!", UserRole.VIEWER),
    ]
    for username, password, expected_role in roles:
        response = auth_client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        assert response.status_code == 200, f"Login failed for {username}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == expected_role.value
        assert data["username"] == username
        assert data["expires_in_seconds"] > 0


def test_auth_login_wrong_password_rejected(auth_client: TestClient):
    """Verify wrong password returns HTTP 401 Unauthorized."""
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "IncorrectPassword123!"},
    )
    assert response.status_code == 401
    err = response.json().get("error", response.json())
    assert "Invalid username or password" in str(err)


def test_auth_login_unknown_user_rejected(auth_client: TestClient):
    """Verify unknown username returns HTTP 401 Unauthorized."""
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "ghost_user_9999", "password": "AnyPassword!"},
    )
    assert response.status_code == 401


def test_auth_expired_jwt_rejected(auth_client: TestClient):
    """Verify expired JWT tokens are strictly rejected with HTTP 401."""
    expired_token = create_access_token(
        {"sub": "admin", "role": "ADMIN", "email": "admin@payrollguardian.internal"},
        expires_delta=timedelta(minutes=-30),
    )
    response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


def test_auth_invalid_jwt_signature_rejected(auth_client: TestClient):
    """Verify malformed or forged JWT tokens are strictly rejected with HTTP 401."""
    forged_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.fake_signature_hash_here"
    response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged_token}"},
    )
    assert response.status_code == 401


def test_auth_missing_token_on_protected_endpoint(auth_client: TestClient):
    """Verify unauthenticated call to strictly authenticated endpoint returns HTTP 401."""
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_auth_token_refresh_flow(auth_client: TestClient):
    """Verify active session refresh returns new valid access token."""
    login_res = auth_client.post(
        "/api/v1/auth/login",
        json={"username": "payroll_admin", "password": "PayrollAdmin2026!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    refresh_res = auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert data["role"] == "PAYROLL_ADMIN"


def test_rbac_viewer_blocked_from_mutating_actions(auth_client: TestClient):
    """Verify VIEWER role receives 403 Forbidden when attempting payroll uploads or anomaly resolution."""
    viewer_token = create_access_token({
        "sub": "test_viewer",
        "role": "VIEWER",
        "email": "viewer@test.internal",
    })

    # Attempt upload -> 403
    upload_res = auth_client.post(
        "/api/v1/payroll/analyze",
        json={"records": [{"employee_id": "EMP_01", "basic_salary": 50000.0}]},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert upload_res.status_code == 403

    # Attempt resolve anomaly -> 403
    resolve_res = auth_client.post(
        "/api/v1/anomalies/anl_demo_202406/EMP_2041/resolve",
        json={"status": "RESOLVED", "resolution_notes": "Attempted viewer resolution"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resolve_res.status_code == 403


def test_rbac_auditor_authorized_to_review_and_resolve(auth_client: TestClient):
    """Verify AUDITOR role is authorized to view analysis and resolve anomalies."""
    auditor_token = create_access_token({
        "sub": "test_auditor",
        "role": "AUDITOR",
        "email": "auditor@test.internal",
    })

    # View analysis -> 200
    view_res = auth_client.get(
        "/api/v1/payroll/analysis/anl_demo_202406",
        headers={"Authorization": f"Bearer {auditor_token}"},
    )
    assert view_res.status_code == 200

    # Resolve anomaly -> 200
    resolve_res = auth_client.post(
        "/api/v1/anomalies/anl_demo_202406/EMP_2041/resolve",
        json={"status": "RESOLVED", "resolution_notes": "Statutory audit approved."},
        headers={"Authorization": f"Bearer {auditor_token}"},
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"


def test_role_escalation_attempt_prevented(auth_client: TestClient):
    """Verify user cannot escalate their role by injecting a different role in login payload."""
    login_res = auth_client.post(
        "/api/v1/auth/login",
        json={
            "username": "viewer",
            "password": "Viewer2026!",
            "role": "ADMIN",  # Attempted escalation
        },
    )
    assert login_res.status_code == 200
    # Role MUST remain VIEWER as persisted in database, ignoring user injection
    assert login_res.json()["role"] == "VIEWER"
