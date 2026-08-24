import asyncio

import pytest
from fastapi.routing import APIRoute
from starlette.requests import Request

from home_ai_cluster.api.routes import ChatRequest
from home_ai_cluster.core.models import ChatMessage, ClusterResult
from home_ai_cluster.main import create_app


class State:
    def __init__(self, disconnected: bool = False) -> None:
        self.disconnected = disconnected

    async def receive(self) -> dict[str, object]:
        # Direct endpoint invocation already supplies the validated body model;
        # this only gives Request.is_disconnected() deterministic connection state.
        if self.disconnected:
            return {"type": "http.disconnect"}
        return {"type": "http.request", "body": b"", "more_body": False}


def endpoint(app):
    routes = app.routes[-1].original_router.routes
    route = next(
        route
        for route in routes
        if isinstance(route, APIRoute)
        and route.path == "/v1/chat"
        and "POST" in route.methods
    )
    return route.endpoint


def request(app, state):
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/v1/chat",
            "headers": [],
            "app": app,
        },
        receive=state.receive,
    )


def payload():
    return ChatRequest(
        messages=[ChatMessage(role="user", content="Hello")], capability="chat"
    )


@pytest.mark.parametrize(
    "initial,parent", [(False, False), (True, False), (False, True)]
)
def test_registered_chat_cancellation(monkeypatch, initial, parent):
    async def run():
        from home_ai_cluster.api import routes

        app, state, started, cancelled = (
            create_app(),
            State(initial),
            asyncio.Event(),
            asyncio.Event(),
        )
        calls = 0

        async def execute(*_):
            nonlocal calls
            calls += 1
            started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        monkeypatch.setattr(routes, "handle_chat_cluster_request", execute)
        task = asyncio.create_task(endpoint(app)(payload(), request(app, state)))
        if initial:
            with pytest.raises(asyncio.CancelledError):
                await task
            assert calls == 0
        else:
            await started.wait()
            if parent:
                task.cancel()
            else:
                state.disconnected = True
            with pytest.raises(asyncio.CancelledError):
                await task
            assert cancelled.is_set()

    asyncio.run(run())


def test_registered_chat_returns_terminal_result(monkeypatch):
    async def run():
        from home_ai_cluster.api import routes

        app, state = create_app(), State()
        expected = ClusterResult(content="Hello", adapter="test", node_id="local")

        async def execute(*_):
            return expected

        monkeypatch.setattr(routes, "handle_chat_cluster_request", execute)
        assert await endpoint(app)(payload(), request(app, state)) is expected

    asyncio.run(run())
