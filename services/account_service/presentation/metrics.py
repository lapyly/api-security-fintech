from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

REQUEST_COMPLIANCE_COUNTER = Counter(
    "account_service_compliance_flags_total",
    "Count of requests touching regulated data scopes.",
    labelnames=("scope",),
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
    async def _compliance_counter(request, call_next):  # type: ignore[no-untyped-def]
        scopes = request.headers.get("x-data-scope")
        if scopes:
            for scope in scopes.split(","):
                REQUEST_COMPLIANCE_COUNTER.labels(scope=scope.strip()).inc()
        return await call_next(request)
