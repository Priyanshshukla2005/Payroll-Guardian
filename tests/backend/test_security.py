"""Unit tests for file upload security and sanitization (Phase 7)."""

import pytest
from fastapi.testclient import TestClient


def test_reject_unsupported_file_extension(client: TestClient):
    files = {"file": ("malicious_script.sh", b"echo 'hack'", "application/x-sh")}
    response = client.post("/api/v1/payroll/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "unsupported file extension" in data["error"]["message"].lower()


def test_reject_executable_binary_file(client: TestClient):
    fake_exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00"
    files = {"file": ("virus.csv", fake_exe_bytes, "text/csv")}
    response = client.post("/api/v1/payroll/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "binary executables" in data["error"]["message"].lower()


def test_reject_empty_file_upload(client: TestClient):
    files = {"file": ("empty.csv", b"", "text/csv")}
    response = client.post("/api/v1/payroll/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "empty" in data["error"]["message"].lower()


def test_reject_double_extension_upload(client: TestClient):
    """Verify upload with dangerous double extension is rejected."""
    files = {"file": ("payroll.exe.csv", b"emp,salary\n1,5000", "text/csv")}
    response = client.post("/api/v1/payroll/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "suspicious multi-extension" in data["error"]["message"].lower()


def test_production_configuration_rejects_default_secret():
    """Verify that BackendSettings rejects default development secret in production mode."""
    from backend.config.settings import BackendSettings

    with pytest.raises(ValueError, match="SECRET_KEY must be provided via an environment variable"):
        BackendSettings(
            app_env="production",
            secret_key="payroll_guardian_enterprise_secret_key_2026_super_secure_phase10",
        )


def test_production_configuration_rejects_wildcard_cors():
    """Verify that BackendSettings rejects wildcard CORS origin in production mode."""
    from backend.config.settings import BackendSettings

    with pytest.raises(ValueError, match="Wildcard CORS origins"):
        BackendSettings(
            app_env="production",
            secret_key="cryptographically_secure_random_key_production_2026_x",
            cors_allowed_origins=["*"],
        )

