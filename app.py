"""Root-Level Startup Wrapper for AI Payroll Guardian FastAPI Service.

This module acts as the single user-facing entrypoint to launch the canonical
FastAPI application located in `backend.main`.

Usage:
    python app.py
"""

import os
import sys
from pathlib import Path
import uvicorn

# Ensure repository root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import settings
from backend.main import app

# Export canonical FastAPI app instance for ASGI servers
__all__ = ["app"]


def main():
    """Launch Uvicorn server with environment-aware defaults."""
    host = os.getenv("API_HOST", settings.api_host if hasattr(settings, "api_host") else "0.0.0.0")
    port = int(os.getenv("API_PORT", str(settings.api_port if hasattr(settings, "api_port") else 8000)))
    reload = os.getenv("APP_RELOAD", "true").lower() in ("true", "1", "yes")

    print(f"\n========================================================")
    print(f"  AI PAYROLL GUARDIAN — FASTAPI SERVICE")
    print(f"  Host: http://{host}:{port}")
    print(f"  API Docs: http://localhost:{port}/docs")
    print(f"  Health Check: http://localhost:{port}/api/v1/health")
    print(f"  Live Reload: {reload}")
    print(f"========================================================\n")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
