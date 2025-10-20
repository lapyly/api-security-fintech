from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable
from typing import Any, Callable

import pytest


_DEFAULT_ASYNCIO_MODE = "auto"


def pytest_addoption(parser: Any) -> None:  # pragma: no cover - exercised via integration tests
    group = parser.getgroup("asyncio")
    group.addoption(
        "--asyncio-mode",
        action="store",
        dest="asyncio_mode_cli",
        default=None,
        help="Compatibility shim for pytest-asyncio's --asyncio-mode option.",
    )
    parser.addini(
        "asyncio_mode",
        "Compatibility shim for pytest-asyncio's asyncio_mode setting.",
        default=_DEFAULT_ASYNCIO_MODE,
    )


def pytest_configure(config: Any) -> None:
    config.addinivalue_line(
        "markers",
        "asyncio: mark a test as requiring an asyncio event loop",
    )


@pytest.fixture
def event_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        yield loop
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        asyncio.set_event_loop(None)
        loop.close()


def _should_run_async(pyfuncitem: pytest.Function) -> bool:
    if inspect.iscoroutinefunction(pyfuncitem.obj):
        return True
    return pyfuncitem.get_closest_marker("asyncio") is not None


def _call_in_loop(
    loop: asyncio.AbstractEventLoop,
    coro_func: Callable[..., Awaitable[Any]],
    kwargs: dict[str, Any],
) -> Any:
    return loop.run_until_complete(coro_func(**kwargs))


def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    if not _should_run_async(pyfuncitem):
        return None

    loop = pyfuncitem.funcargs.get("event_loop")
    owns_loop = loop is None

    if owns_loop:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        _call_in_loop(loop, pyfuncitem.obj, pyfuncitem.funcargs)
    finally:
        if owns_loop and loop is not None:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                asyncio.set_event_loop(None)
                loop.close()

    return True
