"""Standardized global exception handlers for FastAPI (Phase 7)."""

import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("payroll_guardian.errors")


def register_exception_handlers(app: FastAPI) -> None:
    """Bind standardized error response handlers to the FastAPI application."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "req_unknown")
        error_code = f"HTTP_{exc.status_code}"
        if exc.status_code == 400:
            error_code = "BAD_REQUEST"
        elif exc.status_code == 404:
            error_code = "RESOURCE_NOT_FOUND"
        elif exc.status_code == 413:
            error_code = "PAYLOAD_TOO_LARGE"
        elif exc.status_code == 503:
            error_code = "SERVICE_UNAVAILABLE"

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": error_code,
                    "message": str(exc.detail),
                    "request_id": request_id,
                    "status_code": exc.status_code,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "req_unknown")
        # Format errors safely without leaking internal code pointers
        clean_errors = []
        for err in exc.errors():
            loc = " -> ".join([str(x) for x in err.get("loc", [])])
            msg = err.get("msg", "Validation error")
            clean_errors.append(f"{loc}: {msg}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Input validation failed for one or more fields.",
                    "details": clean_errors,
                    "request_id": request_id,
                    "status_code": 422,
                }
            },
        )

    @app.exception_handler(RuntimeError)
    async def runtime_exception_handler(request: Request, exc: RuntimeError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "req_unknown")
        exc_str = str(exc)
        if "AI_DETECTOR_UNAVAILABLE" in exc_str:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": {
                        "code": "AI_DETECTOR_UNAVAILABLE",
                        "message": "AI anomaly detector model is unavailable or corrupted.",
                        "request_id": request_id,
                        "status_code": 503,
                    }
                },
            )
        logger.error(f"[{request_id}] Runtime Exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred while processing the payroll request.",
                    "request_id": request_id,
                    "status_code": 500,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "req_unknown")
        logger.error(f"[{request_id}] Unhandled Exception: {exc}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred while processing the payroll request.",
                    "request_id": request_id,
                    "status_code": 500,
                }
            },
        )
