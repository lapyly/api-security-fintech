from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

AUDIT_EVENTS_COUNTER = Counter(
    "audit_events_total",
    "Number of audit events ingested by category and source.",
    labelnames=("category", "source"),
)


def setup_metrics(app: FastAPI) -> None:
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers={"/metrics", "/health"},
    )
    instrumentator.instrument(app)
    instrumentator.expose(app, include_in_schema=False)


def record_audit_event(category: str, source: str) -> None:
    AUDIT_EVENTS_COUNTER.labels(category=category, source=source).inc()
