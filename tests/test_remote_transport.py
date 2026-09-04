import asyncio
import inspect
import json
from typing import get_type_hints

import httpx
import pytest

from home_ai_cluster.adapters.base import (
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    ApplicationStatus,
    Capability,
    ChatMessage,
    ClassifyRequest,
    ClassifyResult,
    ClusterRequest,
    ClusterResult,
    ClusterStatusNode,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
    RuntimeStatus,
    SourceGroundedChatRequest,
    SourceGroundedChatResult,
    SummarizeRequest,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.remote_transport import (
    REMOTE_STATUS_TIMEOUT_SECONDS,
    HttpRemoteStatusTransport,
    HttpRemoteTransport,
    RemoteExecutionPermissionDeniedError,
    RemoteTransport,
    RemoteTransportError,
    internal_cluster_request_body,
    internal_cluster_request_url,
    internal_cluster_status_url,
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
            node_id="remote-response",
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

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        user_messages = [
            message.content for message in request.messages if message.role == "user"
        ]
        content = user_messages[-1] if user_messages else request.messages[-1].content

        return RuntimeResult(content=content, adapter=self.name)


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
    *,
    node_id: str = "remote",
) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id=node_id,
            name="Remote node",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="chat")],
            adapters=["remote-adapter"],
        ),
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


async def _observe_remote(
    transport: HttpRemoteStatusTransport,
    declaration: RemoteNodeDeclaration,
) -> ClusterStatusNode:
    return await transport.observe(declaration)


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
    result = ClusterResult(
        content="Hello from remote", adapter="remote-adapter", node_id="remote-response"
    )
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
    assert hints["request"] == (
        ClusterRequest | SummarizeRequest | ClassifyRequest | SourceGroundedChatRequest
    )
    assert hints["declaration"] is RemoteNodeDeclaration
    assert hints["return"] == ClusterResult | ClassifyResult | SourceGroundedChatResult


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


def test_internal_cluster_status_url_uses_declared_normalized_address() -> None:
    declaration = make_declaration("http://remote-node.local:8000/")

    assert internal_cluster_status_url(declaration) == (
        "http://remote-node.local:8000/internal/cluster/status"
    )


def test_http_remote_status_transport_gets_one_status_endpoint_without_body() -> None:
    captured_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"runtime_status": "available"})

    async def run() -> ClusterStatusNode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await _observe_remote(
                HttpRemoteStatusTransport(client),
                make_declaration(node_id="cluster-owned-remote"),
            )

    result = asyncio.run(run())

    assert result == ClusterStatusNode(
        node_id="cluster-owned-remote",
        application_status=ApplicationStatus.REACHABLE,
        runtime_status=RuntimeStatus.AVAILABLE,
    )
    assert len(captured_requests) == 1
    assert captured_requests[0].method == "GET"
    assert captured_requests[0].url.path == "/internal/cluster/status"
    assert captured_requests[0].content == b""


def test_http_remote_status_transport_uses_fixed_timeout() -> None:
    captured_timeout: list[float] = []

    class CapturingClient:
        async def get(
            self,
            _: str,
            *,
            timeout: float,
        ) -> httpx.Response:
            captured_timeout.append(timeout)
            return httpx.Response(200, json={"runtime_status": "available"})

    result = asyncio.run(
        _observe_remote(
            HttpRemoteStatusTransport(CapturingClient()),  # type: ignore[arg-type]
            make_declaration(),
        )
    )

    assert REMOTE_STATUS_TIMEOUT_SECONDS == 5.0
    assert captured_timeout == [REMOTE_STATUS_TIMEOUT_SECONDS]
    assert result.runtime_status == RuntimeStatus.AVAILABLE


@pytest.mark.parametrize(
    "runtime_status",
    ["available", "unavailable", "observation-failed"],
)
def test_http_remote_status_transport_keeps_valid_remote_statuses_reachable(
    runtime_status: str,
) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"runtime_status": runtime_status})

    async def run() -> ClusterStatusNode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await _observe_remote(
                HttpRemoteStatusTransport(client),
                make_declaration(),
            )

    result = asyncio.run(run())

    assert result.application_status == ApplicationStatus.REACHABLE
    assert result.runtime_status == runtime_status


@pytest.mark.parametrize(
    "error_type",
    [httpx.ConnectError, httpx.ConnectTimeout],
)
def test_http_remote_status_transport_maps_connection_failures_to_unreachable(
    error_type: type[httpx.HTTPError],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error_type(
            "private-host credentials=secret",
            request=request,
        )

    async def run() -> ClusterStatusNode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await _observe_remote(
                HttpRemoteStatusTransport(client),
                make_declaration("http://private-host:8000"),
            )

    result = asyncio.run(run())

    assert result.application_status == ApplicationStatus.UNREACHABLE
    assert result.runtime_status == RuntimeStatus.UNKNOWN
    assert "private-host" not in result.model_dump_json()
    assert "secret" not in result.model_dump_json()


@pytest.mark.parametrize(
    "error_type",
    [httpx.ReadTimeout, httpx.ReadError, httpx.RemoteProtocolError],
)
def test_http_remote_status_transport_maps_completed_request_failures(
    error_type: type[httpx.HTTPError],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error_type("request failed", request=request)

    async def run() -> ClusterStatusNode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await _observe_remote(
                HttpRemoteStatusTransport(client),
                make_declaration(),
            )

    result = asyncio.run(run())

    assert result.application_status == ApplicationStatus.REQUEST_FAILED
    assert result.runtime_status == RuntimeStatus.UNKNOWN


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(503, json={"detail": "private failure"}),
        httpx.Response(200, content=b"not valid json"),
        httpx.Response(200, json={}),
        httpx.Response(200, json={"runtime_status": "available", "extra": "x"}),
        httpx.Response(200, json={"runtime_status": "unexpected"}),
        httpx.Response(200, json={"runtime_status": "unknown"}),
        httpx.Response(200, json={"runtime_status": 1}),
    ],
)
def test_http_remote_status_transport_rejects_invalid_protocol_response(
    response: httpx.Response,
) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return response

    async def run() -> ClusterStatusNode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await _observe_remote(
                HttpRemoteStatusTransport(client),
                make_declaration(),
            )

    result = asyncio.run(run())

    assert result.application_status == ApplicationStatus.INVALID_RESPONSE
    assert result.runtime_status == RuntimeStatus.UNKNOWN
    assert "private failure" not in result.model_dump_json()


def test_http_remote_status_transport_observes_one_remote_once_without_retries() -> (
    None
):
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise httpx.ConnectError("unreachable", request=request)

    async def run() -> ClusterStatusNode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await _observe_remote(
                HttpRemoteStatusTransport(client),
                make_declaration(),
            )

    result = asyncio.run(run())

    assert result.application_status == ApplicationStatus.UNREACHABLE
    assert len(requests) == 1


def test_http_remote_transport_posts_normalized_cluster_request() -> None:
    captured_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            200,
            json={
                "content": "Hello from HTTP",
                "adapter": "remote-adapter",
                "node_id": "receiving-local-node",
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
        content="Hello from HTTP",
        adapter="remote-adapter",
        node_id="receiving-local-node",
    )
    assert len(captured_requests) == 1
    assert captured_requests[0].method == "POST"
    assert str(captured_requests[0].url) == (
        "http://remote-node.local:8000/internal/cluster/request"
    )
    assert json.loads(captured_requests[0].content) == {
        "kind": "chat",
        "request": {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": {"name": "chat"},
            "constraints": {
                "local_only": True,
                "prefer_fast_response": False,
                "min_context_size": None,
            },
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
                "node_id": "receiving-local-node",
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
        node_id="receiving-local-node",
    )


def test_internal_cluster_request_body_serializes_summarize_exactly() -> None:
    request = SummarizeRequest(text="  Source\n</source>  ")

    assert internal_cluster_request_body(request) == {
        "kind": "summarize",
        "request": {
            "text": "  Source\n</source>  ",
            "constraints": {
                "local_only": True,
                "prefer_fast_response": False,
                "min_context_size": None,
            },
        },
    }


def test_internal_cluster_request_body_serializes_classify_exactly() -> None:
    request = ClassifyRequest(
        text="  Source étiquette  ", labels=["invoice", "Invoice", " invoice"]
    )

    assert internal_cluster_request_body(request) == {
        "kind": "classify",
        "request": {
            "text": "  Source étiquette  ",
            "labels": ["invoice", "Invoice", " invoice"],
        },
    }


def test_http_remote_transport_validates_classify_result_by_request_type() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"selected_label": "invoice", "node_id": "receiver-local"},
        )

    async def run() -> ClassifyResult:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await HttpRemoteTransport(client).send(  # type: ignore[return-value]
                ClassifyRequest(text="Source", labels=["invoice", "personal"]),
                make_declaration(),
            )

    assert asyncio.run(run()) == ClassifyResult(
        selected_label="invoice", node_id="receiver-local"
    )


def test_http_remote_transport_preserves_runtime_unavailable_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            json={
                "detail": "private-host secret-token private-model unavailable",
            },
        )

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with httpx.AsyncClient(transport=transport) as client:
            await HttpRemoteTransport(client).send(
                make_request(),
                make_declaration(),
            )

    with pytest.raises(RuntimeAdapterUnavailableError) as raised:
        asyncio.run(run())

    assert str(raised.value) == "Runtime adapter unavailable"
    for sensitive_value in ("private-host", "secret-token", "private-model"):
        assert sensitive_value not in str(raised.value)


def test_http_remote_transport_keeps_other_http_failure_as_transport_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="private receiver failure")

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await HttpRemoteTransport(client).send(make_request(), make_declaration())

    with pytest.raises(RemoteTransportError) as raised:
        asyncio.run(run())

    assert str(raised.value) == "HTTP remote transport could not send request"


@pytest.mark.parametrize(
    ("response", "is_refusal"),
    [
        (httpx.Response(409, json={"detail": "execution-permission-denied"}), True),
        (
            httpx.Response(409, json={"detail": "execution-permission-denied", "x": 1}),
            False,
        ),
        (httpx.Response(409, json={"detail": "other"}), False),
        (httpx.Response(409, json={}), False),
        (httpx.Response(409, content=b"not-json"), False),
        (httpx.Response(500, json={"detail": "execution-permission-denied"}), False),
    ],
)
def test_http_remote_transport_only_recognizes_exact_permission_refusal(
    response: httpx.Response, is_refusal: bool
) -> None:
    async def run() -> None:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: response)
        ) as client:
            await HttpRemoteTransport(client).send(make_request(), make_declaration())

    if is_refusal:
        with pytest.raises(RemoteExecutionPermissionDeniedError):
            asyncio.run(run())
    else:
        with pytest.raises(RemoteTransportError):
            asyncio.run(run())


def test_http_remote_transport_maps_connection_failure_without_sensitive_details() -> (
    None
):
    private_address = "http://private-remote.example:8000"
    request_body = "private request body"
    captured_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        raise httpx.ConnectError(
            f"connection failed for {private_address}: {request_body}",
            request=request,
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await HttpRemoteTransport(client).send(
                make_request(),
                make_declaration(private_address),
            )

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError) as raised:
        asyncio.run(run())

    assert str(raised.value) == (
        "Remote connection unavailable before request transmission"
    )
    assert isinstance(raised.value.__cause__, httpx.ConnectError)
    assert private_address not in str(raised.value)
    assert "private-remote.example" not in str(raised.value)
    assert request_body not in str(raised.value)
    assert captured_requests[0].url == httpx.URL(
        f"{private_address}/internal/cluster/request"
    )


def test_http_remote_transport_keeps_read_failure_as_transport_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadError("read failed", request=request)

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await HttpRemoteTransport(client).send(
                make_request(),
                make_declaration(),
            )

    with pytest.raises(RemoteTransportError) as raised:
        asyncio.run(run())

    assert str(raised.value) == "HTTP remote transport could not send request"
    assert isinstance(raised.value.__cause__, httpx.ReadError)


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
    assert result == ClusterResult(
        content="Hello over ASGI", adapter="test", node_id="local"
    )
    assert captured_requests == [
        ("POST", "/internal/cluster/request", "declared-remote.test")
    ]
