import asyncio
import inspect

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
from home_ai_cluster.core.orchestrator import (
    orchestrate_request,
    orchestrate_request_with_declared_http_remote,
    orchestrate_request_with_declared_remote,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.router import NoMatchingAdapterError


class RecordingAdapter:
    def __init__(
        self,
        name: str,
        capabilities: list[Capability],
        result: ClusterResult,
    ) -> None:
        self._name = name
        self._capabilities = capabilities
        self._result = result
        self.chat_requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return self._name

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return list(self._capabilities)

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        self.chat_requests.append(request)
        return self._result


class FakeRemoteTransport:
    def __init__(self, result: ClusterResult) -> None:
        self._result = result
        self.requests: list[ClusterRequest] = []
        self.declarations: list[RemoteNodeDeclaration] = []

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        self.requests.append(request)
        self.declarations.append(declaration)
        return self._result


def make_request(content: str = "Hello") -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content=content)],
        capability=Capability(name="chat"),
    )


def make_node(capabilities: list[Capability], adapters: list[str]) -> NodeDescription:
    return NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=capabilities,
        adapters=adapters,
    )


def make_remote_declaration(node_id: str = "local") -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id=node_id,
            name=f"{node_id} node",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="chat")],
            adapters=["adapter"],
        ),
        transport_address=f"http://{node_id}.local:8000",
    )


def test_orchestrate_request_returns_selected_adapter_result() -> None:
    result = ClusterResult(content="Hi", adapter="adapter", model="model")
    adapter = RecordingAdapter("adapter", [Capability(name="chat")], result)
    node_registry = NodeRegistry([make_node([Capability(name="chat")], ["adapter"])])
    adapter_registry = AdapterRegistry([adapter])

    actual = asyncio.run(
        orchestrate_request(make_request(), node_registry, adapter_registry)
    )

    assert actual is result


def test_orchestrate_request_passes_request_to_selected_adapter() -> None:
    result = ClusterResult(content="Hi", adapter="adapter")
    adapter = RecordingAdapter("adapter", [Capability(name="chat")], result)
    node_registry = NodeRegistry([make_node([Capability(name="chat")], ["adapter"])])
    adapter_registry = AdapterRegistry([adapter])
    request = make_request("Original prompt")

    asyncio.run(orchestrate_request(request, node_registry, adapter_registry))

    assert adapter.chat_requests == [request]


def test_orchestrate_request_remains_local_only() -> None:
    result = ClusterResult(content="Hi from local", adapter="adapter")
    adapter = RecordingAdapter("adapter", [Capability(name="chat")], result)
    node_registry = NodeRegistry([make_node([Capability(name="chat")], ["adapter"])])
    adapter_registry = AdapterRegistry([adapter])
    request = make_request("Local-only prompt")

    actual = asyncio.run(orchestrate_request(request, node_registry, adapter_registry))

    signature = inspect.signature(orchestrate_request)
    assert list(signature.parameters) == [
        "request",
        "node_registry",
        "adapter_registry",
    ]
    assert actual is result
    assert adapter.chat_requests == [request]


def test_orchestrate_request_with_declared_remote_uses_local_execution() -> None:
    result = ClusterResult(content="Hi from local", adapter="adapter")
    adapter = RecordingAdapter("adapter", [Capability(name="chat")], result)
    node_registry = NodeRegistry([make_node([Capability(name="chat")], ["adapter"])])
    adapter_registry = AdapterRegistry([adapter])
    remote_registry = RemoteNodeDeclarationRegistry([make_remote_declaration("other")])
    remote_transport = FakeRemoteTransport(
        ClusterResult(content="Hi from remote", adapter="remote-adapter")
    )
    request = make_request("Local declared remote path")

    actual = asyncio.run(
        orchestrate_request_with_declared_remote(
            request,
            node_registry,
            adapter_registry,
            remote_registry,
            remote_transport,
        )
    )

    assert actual is result
    assert adapter.chat_requests == [request]
    assert remote_transport.requests == []
    assert remote_transport.declarations == []


def test_orchestrate_request_with_declared_remote_uses_remote_transport() -> None:
    local_result = ClusterResult(content="Hi from local", adapter="adapter")
    remote_result = ClusterResult(content="Hi from remote", adapter="remote-adapter")
    adapter = RecordingAdapter("adapter", [Capability(name="chat")], local_result)
    node_registry = NodeRegistry([make_node([Capability(name="chat")], ["adapter"])])
    adapter_registry = AdapterRegistry([adapter])
    declaration = make_remote_declaration("local")
    remote_registry = RemoteNodeDeclarationRegistry([declaration])
    remote_transport = FakeRemoteTransport(remote_result)
    request = make_request("Remote declared path")

    actual = asyncio.run(
        orchestrate_request_with_declared_remote(
            request,
            node_registry,
            adapter_registry,
            remote_registry,
            remote_transport,
        )
    )

    assert actual is remote_result
    assert adapter.chat_requests == []
    assert remote_transport.requests == [request]
    assert remote_transport.declarations == [declaration]


def test_orchestrate_request_with_declared_http_remote_uses_http_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.core import orchestrator as orchestrator_module

    local_result = ClusterResult(content="Hi from local", adapter="adapter")
    remote_result = ClusterResult(content="Hi from remote", adapter="remote-adapter")
    adapter = RecordingAdapter("adapter", [Capability(name="chat")], local_result)
    node_registry = NodeRegistry([make_node([Capability(name="chat")], ["adapter"])])
    adapter_registry = AdapterRegistry([adapter])
    declaration = make_remote_declaration("local")
    remote_registry = RemoteNodeDeclarationRegistry([declaration])
    request = make_request("Remote declared HTTP path")
    http_client = object()
    clients: list[object] = []
    created_transports: list[FakeRemoteTransport] = []

    class CapturingHttpRemoteTransport(FakeRemoteTransport):
        def __init__(self, client: object) -> None:
            super().__init__(remote_result)
            clients.append(client)
            created_transports.append(self)

    monkeypatch.setattr(
        orchestrator_module,
        "HttpRemoteTransport",
        CapturingHttpRemoteTransport,
    )

    actual = asyncio.run(
        orchestrate_request_with_declared_http_remote(
            request,
            node_registry,
            adapter_registry,
            remote_registry,
            http_client,
        )
    )

    assert actual is remote_result
    assert adapter.chat_requests == []
    assert clients == [http_client]
    assert created_transports[0].requests == [request]
    assert created_transports[0].declarations == [declaration]


def test_orchestrate_request_uses_first_matching_adapter() -> None:
    first = RecordingAdapter(
        "first",
        [Capability(name="chat")],
        ClusterResult(content="first", adapter="first"),
    )
    second = RecordingAdapter(
        "second",
        [Capability(name="chat")],
        ClusterResult(content="second", adapter="second"),
    )
    node_registry = NodeRegistry([make_node([Capability(name="chat")], ["first"])])
    adapter_registry = AdapterRegistry([first, second])

    result = asyncio.run(
        orchestrate_request(make_request(), node_registry, adapter_registry)
    )

    assert result.adapter == "first"
    assert len(first.chat_requests) == 1
    assert second.chat_requests == []


def test_orchestrate_request_propagates_no_matching_adapter_error() -> None:
    adapter = RecordingAdapter(
        "adapter",
        [Capability(name="summarization")],
        ClusterResult(content="", adapter="adapter"),
    )
    node_registry = NodeRegistry(
        [make_node([Capability(name="summarization")], ["adapter"])]
    )
    adapter_registry = AdapterRegistry([adapter])

    with pytest.raises(NoMatchingAdapterError):
        asyncio.run(
            orchestrate_request(make_request(), node_registry, adapter_registry)
        )

    assert adapter.chat_requests == []
