"""Test root app.py startup wrapper and canonical FastAPI app identity."""

import app as root_app_module
from backend.main import app as backend_main_app


def test_root_app_is_canonical_fastapi_instance():
    """Verify that app.py imports and exposes the canonical FastAPI app instance."""
    assert root_app_module.app is backend_main_app
    assert hasattr(root_app_module.app, "routes")
    assert len(root_app_module.app.routes) > 0


def test_root_app_routes_match_api_v1():
    """Verify that all core API routes are registered on the root app instance."""
    route_paths = set(root_app_module.app.openapi()["paths"].keys()) | {
        getattr(root_app_module.app, "docs_url", "/docs"),
        getattr(root_app_module.app, "openapi_url", "/openapi.json"),
    }
    for r in root_app_module.app.routes:
        if hasattr(r, "path"):
            route_paths.add(r.path)

    assert "/" in route_paths
    assert "/docs" in route_paths
    assert "/openapi.json" in route_paths
    assert "/api/v1/health" in route_paths
    assert "/api/v1/payroll/analyze" in route_paths
    assert "/api/v1/payroll/upload" in route_paths
    assert "/api/v1/compliance/search" in route_paths
    assert "/api/v1/assistant/query" in route_paths
