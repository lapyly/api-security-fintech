from __future__ import annotations

import asyncio
from collections.abc import Sequence

from ..domain.models import AuditEvent


class AuditEventRepository:
    """In-memory append-only repository for audit events."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = asyncio.Lock()

    async def append(self, event: AuditEvent) -> AuditEvent:
        async with self._lock:
            self._events.append(event)
        return event

    async def list_events(self, limit: int | None = None) -> list[AuditEvent]:
        async with self._lock:
            snapshot: Sequence[AuditEvent] = tuple(self._events)
        if limit is not None:
            return list(snapshot[-limit:])
        return list(snapshot)
