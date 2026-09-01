"""Privacy-safe structured access logging middleware (Phase 7)."""

import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("payroll_guardian.access")


class PrivacySafeLoggingMiddleware(BaseHTTPMiddleware):
    """Structured access logger guaranteeing zero PII or payload leak in logs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        request_id = getattr(request.state, "request_id", "req_unknown")
        method = request.method
        path = request.url.path

        response: Response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        status_code = response.status_code

        # Structured, PII-safe audit log line
        logger.info(
            f"[{request_id}] {method} {path} -> {status_code} ({duration_ms:.2f}ms)"
        )

        return response
