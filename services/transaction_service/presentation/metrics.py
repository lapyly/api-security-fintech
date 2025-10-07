from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

TRANSACTION_VOLUME_COUNTER = Counter(
    "transaction_service_submissions_total",
    "Number of transaction submissions processed.",
    labelnames=("status",),
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
    async def _transaction_volume(request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        if request.url.path.startswith("/transactions") and request.method == "POST":
            status = "success" if response.status_code < 400 else "failed"
            TRANSACTION_VOLUME_COUNTER.labels(status=status).inc()
        return response
