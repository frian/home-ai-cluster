"""Private cancellation policy for accepted routable HTTP requests."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol


class DisconnectAwareRequest(Protocol):
    """The supported ASGI request observation used at the HTTP edge."""

    async def is_disconnected(self) -> bool: ...


async def _wait_for_confirmed_disconnect(request: DisconnectAwareRequest) -> None:
    while not await request.is_disconnected():
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
        raise asyncio.CancelledError

    execution_task = asyncio.create_task(execution())
    disconnect_task = asyncio.create_task(_wait_for_confirmed_disconnect(request))
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

        await _cancel_and_wait(execution_task)
        raise asyncio.CancelledError
    finally:
        await _cancel_and_wait(execution_task)
        await _cancel_and_wait(disconnect_task)
