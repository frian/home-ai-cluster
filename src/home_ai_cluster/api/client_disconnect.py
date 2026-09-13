"""Private cancellation policy for accepted routable HTTP requests."""

import asyncio
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Protocol


class DisconnectAwareRequest(Protocol):
    """The supported ASGI request observation used at the HTTP edge."""

    async def is_disconnected(self) -> bool: ...


class ConfirmedClientDisconnect(Exception):
    """Private signal that this HTTP boundary has already abandoned its client."""


@dataclass
class _CancellationState:
    won: bool = False


_cancellation_state: ContextVar[_CancellationState | None] = ContextVar(
    "hac_cancellation_state", default=None
)


def cancellation_has_won() -> bool:
    """Expose only the current HTTP cancellation result to owned work."""
    state = _cancellation_state.get()
    return state is not None and state.won


async def _wait_for_confirmed_disconnect(
    request: DisconnectAwareRequest,
    stop: asyncio.Event,
) -> None:
    while True:
        if stop.is_set():
            return
        if await request.is_disconnected():
            return
        if stop.is_set():
            return
        # This is an observer, not a deadline. Yield without spinning while the
        # request remains connected.
        await asyncio.sleep(0.01)


async def _cancel_and_wait(task: asyncio.Task[object]) -> None:
    if not task.done():
        task.cancel()
    try:
        await task
    except BaseException:
        pass


async def run_routable_execution[Result](
    request: DisconnectAwareRequest,
    execution: Callable[[], Awaitable[Result]],
) -> Result:
    """Own one routable execution until it or confirmed disconnect wins."""
    if await request.is_disconnected():
        raise ConfirmedClientDisconnect

    state = _CancellationState()
    token = _cancellation_state.set(state)
    execution_task = asyncio.create_task(execution())
    stop_observer = asyncio.Event()
    disconnect_task = asyncio.create_task(
        _wait_for_confirmed_disconnect(request, stop_observer)
    )
    try:
        done, _ = await asyncio.wait(
            {execution_task, disconnect_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        if execution_task in done:
            return await execution_task

        observer_error = disconnect_task.exception()
        if observer_error is not None:
            raise observer_error

        # A terminal execution result has priority if both states become visible
        # together, before cancellation is issued.
        if execution_task.done():
            return await execution_task

        state.won = True
        await _cancel_and_wait(execution_task)
        raise ConfirmedClientDisconnect
    finally:
        stop_observer.set()
        await _cancel_and_wait(execution_task)
        await _cancel_and_wait(disconnect_task)
        _cancellation_state.reset(token)
