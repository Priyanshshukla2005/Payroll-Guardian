"""Unit and integration tests for Authentication API and JWT token lifecycle (Phase 10)."""

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from backend.auth.rbac import UserRole
from backend.auth.security import create_access_token


def test_auth_login_valid_admin(client: TestClient):
    """Verify valid login returns signed JWT access token and correct role metadata."""
    payload = {"username": "admin", "password": "AdminPassword2026!"}
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "ADMIN"
    assert data["username"] == "admin"
    assert data["expires_in_seconds"] > 0


def test_auth_login_all_roles(client: TestClient):
    """Verify default seeded credentials for all 4 enterprise roles."""
    roles_credentials = [
        ("admin", "AdminPassword2026!", "ADMIN"),
        ("payroll_admin", "PayrollAdmin2026!", "PAYROLL_ADMIN"),
        ("auditor", "Auditor2026!", "AUDITOR"),
        ("viewer", "Viewer2026!", "VIEWER"),
    ]
    for username, password, expected_role in roles_credentials:
        res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert res.status_code == 200
        assert res.json()["role"] == expected_role


def test_auth_login_invalid_password(client: TestClient):
    """Verify invalid password returns 401 Unauthorized."""
    payload = {"username": "admin", "password": "WrongPassword!"}
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    err = response.json().get("error", response.json())
    assert "Invalid username or password" in str(err)


def test_auth_login_unknown_user(client: TestClient):
    """Verify non-existent user returns 401 Unauthorized."""
    payload = {"username": "non_existent_user_999", "password": "AnyPassword!"}
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


def test_auth_me_endpoint_with_valid_token(client: TestClient):
    """Verify /api/v1/auth/me returns authenticated user profile."""
    # 1. Login
    login_res = client.post("/api/v1/auth/login", json={"username": "payroll_admin", "password": "PayrollAdmin2026!"})
    token = login_res.json()["access_token"]

    # 2. Get profile
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "payroll_admin"
    assert data["role"] == "PAYROLL_ADMIN"
    assert data["is_active"] is True


def test_auth_me_missing_token_returns_401(client: TestClient):
    """Verify /api/v1/auth/me rejects requests missing the Authorization header."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_auth_expired_token_rejected(client: TestClient):
    """Verify expired JWT tokens are rejected with 401 Unauthorized."""
    # Create expired token (-10 minutes)
    expired_token = create_access_token(
        {"sub": "admin", "role": "ADMIN", "email": "admin@payrollguardian.internal"},
        expires_delta=timedelta(minutes=-10),
    )
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    err = res.json().get("error", res.json())
    assert "expired" in str(err).lower() or "invalid" in str(err).lower()


def test_auth_refresh_token(client: TestClient):
    """Verify refreshing an active access token."""
    login_res = client.post("/api/v1/auth/login", json={"username": "auditor", "password": "Auditor2026!"})
    token = login_res.json()["access_token"]

    refresh_res = client.post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {token}"})
    assert refresh_res.status_code == 200
    new_token_data = refresh_res.json()
    assert "access_token" in new_token_data
    assert new_token_data["role"] == "AUDITOR"
