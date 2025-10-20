from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest


# The repository-level pytest shim supplies an ``event_loop`` fixture so the
# tests can run without depending on the external pytest-asyncio plugin.


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
