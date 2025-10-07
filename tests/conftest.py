from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Generator
from typing import Any

import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the entire pytest session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def freezer(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    """Async-compatible fixture placeholder for future time control utilities."""
    yield
    monkeypatch.undo()


@pytest.fixture
def principal_factory() -> Any:
    from services.transaction_service.presentation.dependencies import Principal

    def _factory(**overrides: Any) -> Principal:
        defaults = {
            "subject": "user-123",
            "scopes": {"transactions:read", "transactions:write", "accounts:read"},
            "roles": {"payments", "risk"},
            "client_id": "web-portal",
        }
        defaults.update(overrides)
        return Principal(**defaults)

    return _factory
