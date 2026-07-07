import asyncio
import inspect
import json
from typing import get_type_hints

import httpx
import pytest

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.remote_transport import (
    HttpRemoteTransport,
    RemoteTransport,
    RemoteTransportError,
    internal_cluster_request_url,
)
from home_ai_cluster.main import create_app


class FakeRemoteTransport:
    def __init__(
        self,
        result: ClusterResult | None = None,
        error: RemoteTransportError | None = None,
    ) -> None:
        self._result = result or ClusterResult(
            content="remote result",
            adapter="remote-adapter",
        )
        self._error = error
        self.requests: list[ClusterRequest] = []
        self.declarations: list[RemoteNodeDeclaration] = []
        self.transport_addresses: list[str] = []
        self.nodes: list[NodeDescription] = []

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        self.requests.append(request)
        self.declarations.append(declaration)
        self.transport_addresses.append(declaration.transport_address)
        self.nodes.append(declaration.node)

        if self._error is not None:
            raise self._error

        return self._result


class TestChatAdapter:
    @property
    def name(self) -> str:
        return "test"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        user_messages = [
            message.content for message in request.messages if message.role == "user"
        ]
        content = user_messages[-1] if user_messages else request.messages[-1].content

        return ClusterResult(content=content, adapter=self.name)


def make_request() -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
    )


def make_node() -> NodeDescription:
    return NodeDescription(
        id="remote",
        name="Remote node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["remote-adapter"],
    )


def make_test_node() -> NodeDescription:
    return NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["test"],
    )


def make_declaration(
    transport_address: str = "http://remote-node.local:8000",
) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node(),
        transport_address=transport_address,
    )


def create_test_adapter_registry() -> AdapterRegistry:
    return AdapterRegistry([TestChatAdapter()])


def create_test_node_registry() -> NodeRegistry:
    return NodeRegistry([make_test_node()])


async def _send_remote(
    transport: RemoteTransport,
    request: ClusterRequest,
    declaration: RemoteNodeDeclaration,
) -> ClusterResult:
    return await transport.send(request, declaration)


def test_remote_transport_receives_exact_cluster_request_object() -> None:
    transport = FakeRemoteTransport()
    request = make_request()
    declaration = make_declaration()

    asyncio.run(_send_remote(transport, request, declaration))

    assert transport.requests == [request]
    assert transport.requests[0] is request


def test_remote_transport_receives_exact_remote_node_declaration_object() -> None:
    transport = FakeRemoteTransport()
    request = make_request()
    declaration = make_declaration()

    asyncio.run(_send_remote(transport, request, declaration))

    assert transport.declarations == [declaration]
    assert transport.declarations[0] is declaration


def test_remote_transport_can_access_declaration_transport_address() -> None:
    transport = FakeRemoteTransport()
    declaration = make_declaration()

    asyncio.run(_send_remote(transport, make_request(), declaration))

    assert transport.transport_addresses == ["http://remote-node.local:8000"]


def test_remote_transport_can_access_declaration_node() -> None:
    transport = FakeRemoteTransport()
    declaration = make_declaration()

    asyncio.run(_send_remote(transport, make_request(), declaration))

    assert transport.nodes == [declaration.node]
    assert transport.nodes[0] is declaration.node


def test_remote_transport_returns_cluster_result() -> None:
    result = ClusterResult(content="Hello from remote", adapter="remote-adapter")
    transport = FakeRemoteTransport(result=result)

    actual = asyncio.run(_send_remote(transport, make_request(), make_declaration()))

    assert actual is result


def test_remote_transport_can_raise_normalized_transport_error() -> None:
    error = RemoteTransportError("remote transport failed")
    transport = FakeRemoteTransport(error=error)

    with pytest.raises(RemoteTransportError) as raised:
        asyncio.run(_send_remote(transport, make_request(), make_declaration()))

    assert raised.value is error


def test_remote_transport_interface_uses_normalized_cluster_objects() -> None:
    signature = inspect.signature(RemoteTransport.send)
    hints = get_type_hints(RemoteTransport.send)

    assert list(signature.parameters) == ["self", "request", "declaration"]
    assert hints["request"] is ClusterRequest
    assert hints["declaration"] is RemoteNodeDeclaration
    assert hints["return"] is ClusterResult


def test_internal_cluster_request_url_uses_declaration_transport_address() -> None:
    declaration = make_declaration("http://remote-node.local:8000")

    assert internal_cluster_request_url(declaration) == (
        "http://remote-node.local:8000/internal/cluster/request"
    )


def test_internal_cluster_request_url_ignores_trailing_slash() -> None:
    declaration = make_declaration("http://remote-node.local:8000/")

    assert internal_cluster_request_url(declaration) == (
        "http://remote-node.local:8000/internal/cluster/request"
    )


def test_http_remote_transport_posts_normalized_cluster_request() -> None:
    captured_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            200,
            json={"content": "Hello from HTTP", "adapter": "remote-adapter"},
        )

    transport = httpx.MockTransport(handler)

    async def run() -> ClusterResult:
        async with httpx.AsyncClient(transport=transport) as client:
            return await HttpRemoteTransport(client).send(
                make_request(),
                make_declaration(),
            )

    result = asyncio.run(run())

    assert result == ClusterResult(
        content="Hello from HTTP",
        adapter="remote-adapter",
    )
    assert len(captured_requests) == 1
    assert captured_requests[0].method == "POST"
    assert str(captured_requests[0].url) == (
        "http://remote-node.local:8000/internal/cluster/request"
    )
    assert json.loads(captured_requests[0].content) == {
        "messages": [{"role": "user", "content": "Hello"}],
        "capability": {"name": "chat"},
        "constraints": {
            "local_only": True,
            "prefer_fast_response": False,
            "min_context_size": None,
        },
    }


def test_http_remote_transport_returns_normalized_cluster_result() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "content": "Hello",
                "adapter": "remote-adapter",
                "model": "model",
            },
        )

    transport = httpx.MockTransport(handler)

    async def run() -> ClusterResult:
        async with httpx.AsyncClient(transport=transport) as client:
            return await HttpRemoteTransport(client).send(
                make_request(),
                make_declaration(),
            )

    result = asyncio.run(run())

    assert result == ClusterResult(
        content="Hello",
        adapter="remote-adapter",
        model="model",
    )


def test_http_remote_transport_raises_normalized_error_for_http_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "unavailable"})

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with httpx.AsyncClient(transport=transport) as client:
            await HttpRemoteTransport(client).send(
                make_request(),
                make_declaration(),
            )

    with pytest.raises(RemoteTransportError) as raised:
        asyncio.run(run())

    assert str(raised.value) == "HTTP remote transport could not send request"


def test_http_remote_transport_raises_normalized_error_for_invalid_result() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"content": "missing adapter"})

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with httpx.AsyncClient(transport=transport) as client:
            await HttpRemoteTransport(client).send(
                make_request(),
                make_declaration(),
            )

    with pytest.raises(RemoteTransportError) as raised:
        asyncio.run(run())

    assert str(raised.value) == "HTTP remote transport returned invalid result"


def test_http_remote_transport_can_call_internal_cluster_request_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        create_test_adapter_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_test_node_registry,
    )
    request = ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello over ASGI")],
        capability=Capability(name="chat"),
    )
    declared_address = "http://declared-remote.test"
    declaration = RemoteNodeDeclaration(
        node=make_node(),
        transport_address=declared_address,
    )
    app = create_app()
    captured_requests: list[tuple[str, str, str | None]] = []

    @app.middleware("http")
    async def capture_internal_request(request, call_next):
        captured_requests.append(
            (
                request.method,
                request.url.path,
                request.headers.get("host"),
            )
        )
        return await call_next(request)

    async def run() -> ClusterResult:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url=declared_address,
        ) as client:
            return await HttpRemoteTransport(client).send(request, declaration)

    result = asyncio.run(run())

    assert isinstance(result, ClusterResult)
    assert result == ClusterResult(content="Hello over ASGI", adapter="test")
    assert captured_requests == [
        ("POST", "/internal/cluster/request", "declared-remote.test")
    ]
