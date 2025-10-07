from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

FAILED_LOGIN_COUNTER = Counter(
    "auth_service_failed_logins_total",
    "Count of failed authentication attempts grouped by client.",
    labelnames=("client_id",),
)


def setup_metrics(app: FastAPI) -> None:
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers={"/metrics", "/health"},
    )
    instrumentator.instrument(app)
    instrumentator.expose(app, include_in_schema=False)

    @app.middleware("http")
    async def _failed_login_counter(request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        if request.url.path.startswith("/auth/") and response.status_code in {401, 403}:
            FAILED_LOGIN_COUNTER.labels(
                client_id=request.headers.get("x-client-id", "unknown")
            ).inc()
        return response
