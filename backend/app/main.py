"""SAHAYA FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.rate_limit import clear_rate_limits
from app.db.init_db import initialize_database
from app.schemas.common import HealthResponse


logger = logging.getLogger(__name__)


_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_SERVER_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def _error_payload(
    code: str,
    message: str,
    details: list[dict[str, object]] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        }
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        clear_rate_limits()

        if resolved_settings.environment != "test":
            initialize_database()

        yield

    # =========================================================
    # CREATE APPLICATION
    # =========================================================

    application = FastAPI(
        title="SAHAYA API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # =========================================================
    # CORS
    # =========================================================

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # =========================================================
    # VALIDATION ERRORS
    # =========================================================

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = [
            {
                "location": [str(part) for part in error["loc"]],
                "message": str(error["msg"]),
                "type": str(error["type"]),
            }
            for error in exc.errors()
        ]

        return JSONResponse(
            status_code=422,
            content=_error_payload(
                "VALIDATION_ERROR",
                "Request validation failed",
                details,
            ),
        )

    # =========================================================
    # HTTP ERRORS
    # =========================================================

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        status_code = exc.status_code

        if isinstance(exc.detail, dict):
            code = str(
                exc.detail.get("code")
                or _STATUS_CODES.get(
                    status_code,
                    "HTTP_ERROR",
                )
            )

            message = str(
                exc.detail.get("message")
                or "Request failed"
            )

        else:
            code = _STATUS_CODES.get(
                status_code,
                "HTTP_ERROR",
            )

            message = (
                str(exc.detail)
                if status_code < 500
                else "Internal server error"
            )

        return JSONResponse(
            status_code=status_code,
            content=_error_payload(
                code,
                message,
            ),
            headers=getattr(
                exc,
                "headers",
                None,
            ),
        )

    # =========================================================
    # UNEXPECTED ERRORS
    # =========================================================

    @application.exception_handler(Exception)
    async def unexpected_error_handler(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception(
            "Unhandled application error",
            exc_info=exc,
        )

        return JSONResponse(
            status_code=500,
            content=_error_payload(
                "INTERNAL_SERVER_ERROR",
                "Internal server error",
            ),
        )

    # =========================================================
    # API ROUTER
    # =========================================================

    application.include_router(
        api_router,
        prefix="/api/v1",
    )

    # =========================================================
    # HEALTH
    # =========================================================

    @application.get(
        "/health",
        response_model=HealthResponse,
        tags=["health"],
    )
    def root_health() -> HealthResponse:
        """Backward-compatible liveness endpoint."""
        return HealthResponse(status="ok")

    return application


app = create_app()