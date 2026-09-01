"""Request ID tracking middleware for distributed traceability (Phase 7)."""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates a unique Request-ID for each incoming HTTP request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Check incoming X-Request-ID header or generate new UUID4
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex}"

        # Bind to request state
        request.state.request_id = request_id

        # Process request
        response: Response = await call_next(request)

        # Set response header
        response.headers["X-Request-ID"] = request_id
        return response
