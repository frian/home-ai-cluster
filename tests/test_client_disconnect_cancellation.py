import asyncio
import inspect

import pytest
from fastapi import HTTPException

from home_ai_cluster.api.client_disconnect import run_routable_execution


class DisconnectingRequest:
    def __init__(self) -> None:
        self.disconnected = asyncio.Event()
        self.observer_cancelled = asyncio.Event()

    async def is_disconnected(self) -> bool:
        try:
            await asyncio.sleep(0)
            return self.disconnected.is_set()
        except asyncio.CancelledError:
            self.observer_cancelled.set()
            raise


def test_execution_completion_returns_its_terminal_result_and_cleans_observer() -> None:
    async def run() -> None:
        request = DisconnectingRequest()

        result = await run_routable_execution(request, lambda: immediate_result())

        assert result == "terminal"
        assert all(
            task.get_coro().__qualname__ != "_wait_for_confirmed_disconnect"
            for task in asyncio.all_tasks()
            if task is not asyncio.current_task()
        )

    async def immediate_result() -> str:
        return "terminal"

    asyncio.run(run())


def test_preexisting_disconnect_does_not_create_execution() -> None:
    async def run() -> None:
        request = DisconnectingRequest()
        request.disconnected.set()
        calls = 0

        async def execution() -> str:
            nonlocal calls
            calls += 1
            return "unexpected"

        with pytest.raises(asyncio.CancelledError):
            await run_routable_execution(request, execution)
        assert calls == 0

    asyncio.run(run())


def test_existing_structured_failure_is_a_terminal_result() -> None:
    async def run() -> None:
        request = DisconnectingRequest()
        failure = {"detail": "Runtime adapter unavailable"}

        async def completed_failure() -> dict[str, str]:
            return failure

        result = await run_routable_execution(request, completed_failure)

        assert result is failure

    asyncio.run(run())


def test_execution_exception_preserves_its_exact_identity() -> None:
    async def run() -> None:
        request = DisconnectingRequest()
        expected = ValueError("expected")

        async def execution() -> str:
            raise expected

        with pytest.raises(ValueError) as raised:
            await run_routable_execution(request, execution)
        assert raised.value is expected

    asyncio.run(run())


def test_http_exception_preserves_its_exact_identity_and_semantics() -> None:
    async def run() -> None:
        request = DisconnectingRequest()
        expected = HTTPException(
            status_code=503,
            detail="Runtime adapter unavailable",
            headers={"Retry-After": "1"},
        )

        async def execution() -> str:
            raise expected

        with pytest.raises(HTTPException) as raised:
            await run_routable_execution(request, execution)
        assert raised.value is expected
        assert (raised.value.status_code, raised.value.detail) == (503, expected.detail)
        assert raised.value.headers == {"Retry-After": "1"}
        assert not any(
            task.get_coro().__qualname__ == "_wait_for_confirmed_disconnect"
            for task in asyncio.all_tasks()
            if task is not asyncio.current_task()
        )

    asyncio.run(run())


def test_unexpected_observer_exception_cancels_pending_execution() -> None:
    async def run() -> None:
        execution_started = asyncio.Event()
        execution_cancelled = asyncio.Event()
        expected = RuntimeError("observer failed")

        class BrokenRequest:
            checks = 0

            async def is_disconnected(self) -> bool:
                self.checks += 1
                if self.checks == 1:
                    return False
                raise expected

        async def execution() -> str:
            execution_started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                execution_cancelled.set()
                raise

        with pytest.raises(RuntimeError) as raised:
            await run_routable_execution(BrokenRequest(), execution)
        assert raised.value is expected
        assert execution_started.is_set()
        assert execution_cancelled.is_set()
        assert not any(
            task.get_coro().__qualname__
            in {
                "_wait_for_confirmed_disconnect",
                "execution",
            }
            for task in asyncio.all_tasks()
            if task is not asyncio.current_task()
        )

    asyncio.run(run())


def test_confirmed_disconnect_cancels_pending_execution_without_a_result() -> None:
    async def run() -> None:
        request = DisconnectingRequest()
        started = asyncio.Event()
        cancelled = asyncio.Event()
        calls = 0

        async def pending_local_adapter() -> str:
            nonlocal calls
            calls += 1
            started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        task = asyncio.create_task(
            run_routable_execution(request, pending_local_adapter)
        )
        await started.wait()
        request.disconnected.set()

        with pytest.raises(asyncio.CancelledError):
            await task
        assert cancelled.is_set()
        assert calls == 1

    asyncio.run(run())


def test_terminal_completion_wins_when_disconnect_is_observed_together() -> None:
    async def run() -> None:
        release_execution = asyncio.Event()

        class SimultaneousRequest(DisconnectingRequest):
            checks = 0

            async def is_disconnected(self) -> bool:
                self.checks += 1
                if self.checks == 1:
                    return False
                release_execution.set()
                await asyncio.sleep(0)
                return True

        async def execution() -> str:
            await release_execution.wait()
            return "terminal"

        result = await run_routable_execution(SimultaneousRequest(), execution)

        assert result == "terminal"

    asyncio.run(run())


def test_late_result_after_cancellation_is_discarded() -> None:
    async def run() -> None:
        request = DisconnectingRequest()
        started = asyncio.Event()
        late_result_produced = asyncio.Event()

        async def late_remote_request() -> str:
            started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                late_result_produced.set()
                return "late remote result"

        task = asyncio.create_task(run_routable_execution(request, late_remote_request))
        await started.wait()
        request.disconnected.set()

        with pytest.raises(asyncio.CancelledError):
            await task
        assert late_result_produced.is_set()

    asyncio.run(run())


def test_parent_cancellation_propagates_without_becoming_disconnect_handling() -> None:
    async def run() -> None:
        request = DisconnectingRequest()
        execution_started = asyncio.Event()
        execution_cancelled = asyncio.Event()

        async def pending_execution() -> str:
            execution_started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                execution_cancelled.set()
                raise

        task = asyncio.create_task(run_routable_execution(request, pending_execution))
        await execution_started.wait()
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task
        assert execution_cancelled.is_set()
        assert not request.disconnected.is_set()
        assert all(
            task.get_coro().__qualname__ != "_wait_for_confirmed_disconnect"
            for task in asyncio.all_tasks()
            if task is not asyncio.current_task()
        )

    asyncio.run(run())


def test_only_the_six_accepted_route_families_use_the_shared_policy() -> None:
    from home_ai_cluster.api import openai_compatibility, routes

    route_sources = {
        "/v1/chat": inspect.getsource(routes.chat),
        "/v1/chat/sources": inspect.getsource(routes.source_grounded_chat),
        "/v1/summarize": inspect.getsource(routes.summarize),
        "/v1/classify": inspect.getsource(routes.classify),
        "/internal/cluster/request": inspect.getsource(routes.internal_cluster_request),
        "/v1/chat/completions": inspect.getsource(
            openai_compatibility.chat_completions
        ),
    }

    assert all("run_routable_execution" in source for source in route_sources.values())
    assert "run_routable_execution" not in inspect.getsource(
        routes.internal_cluster_status
    )
