from __future__ import annotations

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def setup_metrics(app: FastAPI) -> None:
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers={"/metrics", "/health"},
    )
    instrumentator.instrument(app)
    instrumentator.expose(app, include_in_schema=False)
