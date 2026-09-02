import asyncio
import json

import pytest
from fastapi.routing import APIRoute
from starlette.requests import Request

from home_ai_cluster.api.client_disconnect import ConfirmedClientDisconnect
from home_ai_cluster.api.openai_compatibility import compatibility_router
from home_ai_cluster.api.routes import ChatRequest
from home_ai_cluster.api.wiring import LocalAppComposition
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClassifyResult,
    ClusterResult,
    NodeDescription,
    NodeHealth,
    SourceGroundedChatResult,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
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


class BodyFirstState(State):
    """Provide one endpoint-owned JSON body, then probe-only connection state."""

    def __init__(self, body: object) -> None:
        super().__init__()
        self._body = json.dumps(body).encode()
        self._body_consumed = False

    async def receive(self) -> dict[str, object]:
        if not self._body_consumed:
            self._body_consumed = True
            return {"type": "http.request", "body": self._body, "more_body": False}
        # Endpoints consume one body message; later probes expose connection state.
        return await super().receive()

    def send_disconnect(self) -> None:
        self.disconnected = True


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

        async def execute(*_, **__):
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
            with pytest.raises(ConfirmedClientDisconnect):
                await task
            assert calls == 0
        else:
            await started.wait()
            if parent:
                task.cancel()
            else:
                state.disconnected = True
            expected = asyncio.CancelledError if parent else ConfirmedClientDisconnect
            with pytest.raises(expected):
                await task
            assert cancelled.is_set()

    asyncio.run(run())


def test_registered_chat_returns_terminal_result(monkeypatch):
    async def run():
        from home_ai_cluster.api import routes

        app, state = create_app(), State()
        expected = ClusterResult(content="Hello", adapter="test", node_id="local")

        async def execute(*_, **__):
            return expected

        monkeypatch.setattr(routes, "handle_chat_cluster_request", execute)
        assert await endpoint(app)(payload(), request(app, state)) is expected

    asyncio.run(run())


def sources_payload():
    return {
        "question": "What does the evidence say?",
        "sources": [
            {
                "title": "First",
                "url": "https://example.test/first",
                "content": "First evidence",
            },
            {
                "title": "Second",
                "url": "https://example.test/second",
                "content": "Second evidence",
            },
        ],
    }


def sources_endpoint(app):
    routes = app.routes[-1].original_router.routes
    return next(
        route.endpoint
        for route in routes
        if isinstance(route, APIRoute)
        and route.path == "/v1/chat/sources"
        and "POST" in route.methods
    )


def test_registered_sources_returns_terminal_result(monkeypatch):
    async def run():
        from home_ai_cluster.api import routes

        app, state = create_app(), BodyFirstState(sources_payload())
        calls = 0

        async def execute(request, *_):
            nonlocal calls
            calls += 1
            return SourceGroundedChatResult(
                content="Answer",
                sources=request.sources,
                adapter="test",
                node_id="local",
            )

        monkeypatch.setattr(routes, "handle_chat_cluster_request", execute)
        result = await sources_endpoint(app)(request(app, state))
        assert (
            result.content == "Answer"
            and result.adapter == "test"
            and result.node_id == "local"
        )
        assert [source.title for source in result.sources] == [
            "First",
            "Second",
        ] and calls == 1

    asyncio.run(run())


def test_registered_sources_disconnect_cancels_execution(monkeypatch):
    async def run():
        from home_ai_cluster.api import routes

        app, state = create_app(), BodyFirstState(sources_payload())
        started, cancelled = asyncio.Event(), asyncio.Event()

        async def execute(*_, **__):
            started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        monkeypatch.setattr(routes, "handle_chat_cluster_request", execute)
        task = asyncio.create_task(sources_endpoint(app)(request(app, state)))
        await asyncio.wait_for(started.wait(), 1)
        state.send_disconnect()
        with pytest.raises(ConfirmedClientDisconnect):
            await task
        assert cancelled.is_set()

    asyncio.run(run())


def summarize_endpoint(app):
    routes = app.routes[-1].original_router.routes
    return next(
        route.endpoint
        for route in routes
        if isinstance(route, APIRoute)
        and route.path == "/v1/summarize"
        and "POST" in route.methods
    )


def test_registered_summarize_returns_terminal_result(monkeypatch):
    async def run():
        from home_ai_cluster.api import routes

        app, state, calls = create_app(), BodyFirstState({"text": "Source"}), 0
        expected = ClusterResult(content="Summary", adapter="test", node_id="local")

        async def execute(*_, **__):
            nonlocal calls
            calls += 1
            return expected

        monkeypatch.setattr(routes, "handle_summarize_cluster_request", execute)
        assert await summarize_endpoint(app)(request(app, state)) is expected
        assert calls == 1

    asyncio.run(run())


def test_registered_summarize_disconnect_cancels_execution(monkeypatch):
    async def run():
        from home_ai_cluster.api import routes

        app, state = create_app(), BodyFirstState({"text": "Source"})
        started, cancelled = asyncio.Event(), asyncio.Event()

        async def execute(*_, **__):
            started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        monkeypatch.setattr(routes, "handle_summarize_cluster_request", execute)
        task = asyncio.create_task(summarize_endpoint(app)(request(app, state)))
        try:
            await asyncio.wait_for(started.wait(), 1)
            state.send_disconnect()
            with pytest.raises(ConfirmedClientDisconnect):
                await task
            assert cancelled.is_set()
        finally:
            if not task.done():
                task.cancel()
            if not task.cancelled():
                try:
                    await task
                except (asyncio.CancelledError, ConfirmedClientDisconnect):
                    pass

    asyncio.run(run())


def classify_endpoint(app):
    routes = app.routes[-1].original_router.routes
    return next(
        route.endpoint
        for route in routes
        if isinstance(route, APIRoute)
        and route.path == "/v1/classify"
        and "POST" in route.methods
    )


def test_registered_classify_returns_terminal_result(monkeypatch):
    async def run():
        from home_ai_cluster.api import routes

        app, state, calls = (
            create_app(),
            BodyFirstState({"text": "Source", "labels": ["invoice", "personal"]}),
            0,
        )
        expected = ClassifyResult(selected_label="invoice", node_id="local")

        async def execute(*_, **__):
            nonlocal calls
            calls += 1
            return expected

        monkeypatch.setattr(routes, "handle_classify_cluster_request", execute)
        assert await classify_endpoint(app)(request(app, state)) is expected
        assert calls == 1

    asyncio.run(run())


def test_registered_classify_disconnect_cancels_execution(monkeypatch):
    async def run():
        from home_ai_cluster.api import routes

        app, state = (
            create_app(),
            BodyFirstState({"text": "Source", "labels": ["invoice", "personal"]}),
        )
        started, cancelled = asyncio.Event(), asyncio.Event()

        async def execute(*_, **__):
            started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        monkeypatch.setattr(routes, "handle_classify_cluster_request", execute)
        task = asyncio.create_task(classify_endpoint(app)(request(app, state)))
        try:
            await asyncio.wait_for(started.wait(), 1)
            state.send_disconnect()
            with pytest.raises(ConfirmedClientDisconnect):
                await task
            assert cancelled.is_set()
        finally:
            if not task.done():
                task.cancel()
            if not task.cancelled():
                try:
                    await task
                except (asyncio.CancelledError, ConfirmedClientDisconnect):
                    pass

    asyncio.run(run())


def internal_endpoint(app):
    routes = app.routes[-1].original_router.routes
    return next(
        route.endpoint
        for route in routes
        if isinstance(route, APIRoute)
        and route.path == "/internal/cluster/request"
        and "POST" in route.methods
    )


def internal_body():
    return {
        "kind": "chat",
        "request": {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": {"name": "chat"},
            "constraints": {"local_only": True},
        },
    }


def test_registered_internal_returns_terminal_result(monkeypatch):
    async def run():
        from home_ai_cluster.api import routes

        app, state, calls = create_app(), BodyFirstState(internal_body()), 0
        expected = ClusterResult(content="Answer", adapter="test", node_id="local")

        async def execute(*_, **__):
            nonlocal calls
            calls += 1
            return expected

        monkeypatch.setattr(routes, "handle_static_local_cluster_request", execute)
        assert await internal_endpoint(app)(request(app, state)) is expected
        assert calls == 1

    asyncio.run(run())


def test_registered_internal_disconnect_cancels_execution(monkeypatch):
    async def run():
        from home_ai_cluster.api import routes

        app, state = create_app(), BodyFirstState(internal_body())
        started, cancelled = asyncio.Event(), asyncio.Event()

        async def execute(*_, **__):
            started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        monkeypatch.setattr(routes, "handle_static_local_cluster_request", execute)
        task = asyncio.create_task(internal_endpoint(app)(request(app, state)))
        try:
            await asyncio.wait_for(started.wait(), 1)
            state.send_disconnect()
            with pytest.raises(ConfirmedClientDisconnect):
                await task
            assert cancelled.is_set()
        finally:
            if not task.done():
                task.cancel()
            if not task.cancelled():
                try:
                    await task
                except (asyncio.CancelledError, ConfirmedClientDisconnect):
                    pass

    asyncio.run(run())


def completions_endpoint(app):
    app.include_router(compatibility_router)
    routes = app.routes[-1].original_router.routes
    return next(
        route.endpoint
        for route in routes
        if isinstance(route, APIRoute)
        and route.path == "/v1/chat/completions"
        and "POST" in route.methods
    )


def completions_body():
    return {
        "model": "home-ai-cluster",
        "messages": [{"role": "user", "content": "Hello"}],
    }


def test_registered_completions_returns_translated_result(monkeypatch):
    async def run():
        from home_ai_cluster.api import openai_compatibility

        app, state, calls = create_app(), BodyFirstState(completions_body()), 0

        async def execute(request, **_):
            nonlocal calls
            calls += 1
            assert (
                request.capability.name == "chat"
                and request.messages[-1].content == "Hello"
            )
            return ClusterResult(
                content="Answer", adapter="test", model="actual", node_id="local"
            )

        monkeypatch.setattr(
            openai_compatibility, "handle_chat_cluster_request", execute
        )
        response = await completions_endpoint(app)(request(app, state))
        assert (
            response.status_code == 200
            and response.body.find(b'"content":"Answer"') >= 0
            and calls == 1
        )

    asyncio.run(run())


def test_registered_completions_disconnect_cancels_execution(monkeypatch):
    async def run():
        from home_ai_cluster.api import openai_compatibility

        app, state = create_app(), BodyFirstState(completions_body())
        started, cancelled, cleaned = asyncio.Event(), asyncio.Event(), asyncio.Event()
        calls = 0

        async def execute(*_, **__):
            nonlocal calls
            calls += 1
            started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                cancelled.set()
                raise
            finally:
                cleaned.set()

        monkeypatch.setattr(
            openai_compatibility, "handle_chat_cluster_request", execute
        )
        task = asyncio.create_task(completions_endpoint(app)(request(app, state)))
        try:
            await asyncio.wait_for(started.wait(), 1)
            state.send_disconnect()
            with pytest.raises(ConfirmedClientDisconnect):
                await task
            assert calls == 1 and cancelled.is_set() and cleaned.is_set()
        finally:
            if not task.done():
                task.cancel()
            if not task.cancelled():
                try:
                    await task
                except (asyncio.CancelledError, ConfirmedClientDisconnect):
                    pass

    asyncio.run(run())


def test_registered_chat_local_adapter_cancellation():
    async def run():
        class Adapter:
            name = "controlled"

            def __init__(self):
                self.calls = 0
                self.request = None
                self.entered = asyncio.Event()
                self.cancelled = asyncio.Event()
                self.cleaned = asyncio.Event()

            def health(self):
                return AdapterHealth(available=True)

            def capabilities(self):
                return [Capability(name="chat")]

            async def chat(self, request):
                self.calls += 1
                self.request = request
                self.entered.set()
                try:
                    await asyncio.Future()
                except asyncio.CancelledError:
                    self.cancelled.set()
                    raise
                finally:
                    self.cleaned.set()

        adapter = Adapter()
        node = NodeDescription(
            id="local",
            name="Local",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="chat")],
            adapters=[adapter.name],
        )
        composition = LocalAppComposition(
            NodeRegistry([node]), AdapterRegistry([adapter])
        )
        app, state = create_app(local_app_composition=composition), State()
        task = asyncio.create_task(endpoint(app)(payload(), request(app, state)))
        try:
            await asyncio.wait_for(adapter.entered.wait(), 1)
            state.disconnected = True
            with pytest.raises(ConfirmedClientDisconnect):
                await task
            assert (
                adapter.calls == 1
                and adapter.cancelled.is_set()
                and adapter.cleaned.is_set()
            )
            assert (
                adapter.request.capability.name == "chat"
                and adapter.request.messages[-1].content == "Hello"
            )
        finally:
            if not task.done():
                task.cancel()
            if not task.cancelled():
                try:
                    await task
                except (asyncio.CancelledError, ConfirmedClientDisconnect):
                    pass

    asyncio.run(run())


def test_confirmed_disconnect_is_contained_by_the_asgi_application(monkeypatch):
    async def run():
        from home_ai_cluster.api import routes

        app, state = (
            create_app(),
            BodyFirstState(
                {
                    "messages": [{"role": "user", "content": "Hello"}],
                    "capability": "chat",
                }
            ),
        )
        started, cancelled = asyncio.Event(), asyncio.Event()
        sent: list[dict[str, object]] = []

        async def execute(*_, **__):
            started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        async def send(message: dict[str, object]) -> None:
            sent.append(message)

        monkeypatch.setattr(routes, "handle_chat_cluster_request", execute)
        task = asyncio.create_task(
            app(
                {
                    "type": "http",
                    "asgi": {"version": "3.0"},
                    "http_version": "1.1",
                    "method": "POST",
                    "scheme": "http",
                    "path": "/v1/chat",
                    "raw_path": b"/v1/chat",
                    "query_string": b"",
                    "headers": [(b"content-type", b"application/json")],
                    "client": ("testclient", 1),
                    "server": ("testserver", 80),
                },
                state.receive,
                send,
            )
        )
        await asyncio.wait_for(started.wait(), 1)
        state.send_disconnect()
        await task

        assert cancelled.is_set()
        assert sent == []

    asyncio.run(run())
