from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pythonjsonlogger import jsonlogger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


def _configure_json_logger() -> logging.Logger:
    logger = logging.getLogger("api.access")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        request.state.trace_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload"
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; script-src 'none'",
        )
        return response


class AccessLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, logger: logging.Logger, *, service_name: str):
        super().__init__(app)
        self._logger = logger
        self._service_name = service_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - delegated to exception handler
            self._log(request, None, time.perf_counter() - start, exc=exc)
            raise
        duration = time.perf_counter() - start
        self._log(request, response, duration)
        return response

    def _log(
        self,
        request: Request,
        response: Response | None,
        duration: float,
        *,
        exc: Exception | None = None,
    ) -> None:
        request_id = getattr(request.state, "request_id", None)
        payload: dict[str, Any] = {
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "status_code": getattr(response, "status_code", 500),
            "duration_ms": round(duration * 1000, 3),
            "request_id": request_id,
            "client": request.client.host if request.client else None,
            "trace_id": request_id,
            "service": self._service_name,
            "compliance": {
                "regimes": ["gdpr", "pci_dss", "soc2"],
                "data_classification": request.headers.get("x-data-classification", "restricted"),
            },
            "mtls_subject": request.headers.get("x-mtls-client-cn"),
        }
        if exc:
            payload["error"] = str(exc)
            self._logger.error("request_failed", extra=payload)
        else:
            self._logger.info("request_completed", extra=payload)


def _problem_response(
    request: Request,
    status_code: int,
    title: str,
    detail: str | None = None,
    type_: str = "about:blank",
) -> JSONResponse:
    body = {
        "type": type_,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url),
    }
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        body["traceId"] = request_id
    return JSONResponse(body, status_code=status_code, media_type="application/problem+json")


def register_exception_handlers(app: FastAPI) -> None:
    logger = logging.getLogger("api.access")

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return _problem_response(request, exc.status_code, exc.detail or "HTTP Error")

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        detail = exc.errors()
        logger.warning(
            "validation_error",
            extra={
                "errors": detail,
                "path": request.url.path,
                "request_id": getattr(request.state, "request_id", None),
            },
        )
        return _problem_response(
            request,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Validation Error",
            detail=json.dumps(detail),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            extra={
                "path": request.url.path,
                "request_id": getattr(request.state, "request_id", None),
            },
        )
        return _problem_response(request, status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error")


def setup_middleware(app: FastAPI) -> None:
    logger = _configure_json_logger()
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(AccessLogMiddleware, logger=logger, service_name=app.title)
    app.add_middleware(SecurityHeadersMiddleware)
    register_exception_handlers(app)
