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
from home_ai_cluster.core.orchestrator import orchestrate_request
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    DECLARED_REMOTE_ROUTING_REASON,
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.router import NoMatchingAdapterError, route_request
from home_ai_cluster.core.routing_candidates import (
    LocalRoutingCandidate,
    RoutingCandidates,
    routing_candidates_for_request,
)


class RecordingAdapter:
    def __init__(
        self,
        name: str,
        capabilities: list[Capability],
        result: ClusterResult | None = None,
    ) -> None:
        self._name = name
        self._capabilities = capabilities
        self._result = result or ClusterResult(content="Hello", adapter=name)
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


class RecordingRemoteTransport:
    def __init__(self) -> None:
        self.requests: list[ClusterRequest] = []
        self.declarations: list[RemoteNodeDeclaration] = []

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        self.requests.append(request)
        self.declarations.append(declaration)
        return ClusterResult(content="Remote hello", adapter="remote")


def make_request(capability: Capability | None = None) -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=capability or Capability(name="chat"),
    )


def make_node(
    node_id: str,
    capabilities: list[Capability],
    adapters: list[str],
    availability: str = "available",
) -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability=availability,  # type: ignore[arg-type]
        health=NodeHealth(healthy=availability == "available"),
        capabilities=capabilities,
        adapters=adapters,
    )


def make_declaration(
    node_id: str = "remote",
    capability: Capability | None = None,
    adapters: list[str] | None = None,
) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node(
            node_id,
            [capability or Capability(name="chat")],
            adapters or ["remote-adapter"],
        ),
        transport_address=f"http://{node_id}.local:8000",
    )


def test_helper_returns_local_candidate_when_local_adapter_matches() -> None:
    chat = Capability(name="chat")
    adapter = RecordingAdapter("local-adapter", [chat])
    node = make_node("local", [chat], ["local-adapter"])

    candidates = routing_candidates_for_request(
        make_request(chat),
        NodeRegistry([node]),
        AdapterRegistry([adapter]),
        RemoteNodeDeclarationRegistry(),
    )

    assert isinstance(candidates, RoutingCandidates)
    assert candidates.local is not None
    assert isinstance(candidates.local, LocalRoutingCandidate)
    assert candidates.local.decision.node is node
    assert candidates.local.decision.adapter is adapter
    assert candidates.local.decision.capability == chat


def test_helper_returns_declared_remote_candidate_when_eligible() -> None:
    chat = Capability(name="chat")
    declaration = make_declaration(capability=chat)

    candidates = routing_candidates_for_request(
        make_request(chat),
        NodeRegistry(),
        AdapterRegistry(),
        RemoteNodeDeclarationRegistry([declaration]),
    )

    assert candidates.local is None
    assert candidates.declared_remote is not None
    assert candidates.declared_remote.node is declaration.node
    assert candidates.declared_remote.declaration is declaration
    assert candidates.declared_remote.capability == chat
    assert candidates.declared_remote.reason == DECLARED_REMOTE_ROUTING_REASON


def test_helper_can_return_local_and_declared_remote_candidates() -> None:
    chat = Capability(name="chat")
    adapter = RecordingAdapter("local-adapter", [chat])
    node = make_node("local", [chat], ["local-adapter"])
    declaration = make_declaration(capability=chat)

    candidates = routing_candidates_for_request(
        make_request(chat),
        NodeRegistry([node]),
        AdapterRegistry([adapter]),
        RemoteNodeDeclarationRegistry([declaration]),
    )

    assert candidates.local is not None
    assert candidates.local.decision.node is node
    assert candidates.local.decision.adapter is adapter
    assert candidates.declared_remote is not None
    assert candidates.declared_remote.declaration is declaration


def test_helper_preserves_declared_remote_candidate_when_local_routing_fails() -> None:
    chat = Capability(name="chat")
    node = make_node("local", [chat], ["missing-local-adapter"])
    declaration = make_declaration(capability=chat)

    candidates = routing_candidates_for_request(
        make_request(chat),
        NodeRegistry([node]),
        AdapterRegistry(),
        RemoteNodeDeclarationRegistry([declaration]),
    )

    assert candidates.local is None
    assert candidates.declared_remote is not None
    assert candidates.declared_remote.declaration is declaration


def test_helper_does_not_require_remote_adapter_name_to_resolve_locally() -> None:
    chat = Capability(name="chat")
    declaration = make_declaration(
        capability=chat,
        adapters=["declared-remote-only-adapter"],
    )

    candidates = routing_candidates_for_request(
        make_request(chat),
        NodeRegistry(),
        AdapterRegistry(),
        RemoteNodeDeclarationRegistry([declaration]),
    )

    assert candidates.local is None
    assert candidates.declared_remote is not None
    assert candidates.declared_remote.declaration is declaration


def test_helper_does_not_execute_local_adapters() -> None:
    chat = Capability(name="chat")
    adapter = RecordingAdapter("local-adapter", [chat])
    node = make_node("local", [chat], ["local-adapter"])

    routing_candidates_for_request(
        make_request(chat),
        NodeRegistry([node]),
        AdapterRegistry([adapter]),
        RemoteNodeDeclarationRegistry(),
    )

    assert adapter.chat_requests == []


def test_helper_does_not_call_remote_transports() -> None:
    transport = RecordingRemoteTransport()
    signature = inspect.signature(routing_candidates_for_request)

    routing_candidates_for_request(
        make_request(),
        NodeRegistry(),
        AdapterRegistry(),
        RemoteNodeDeclarationRegistry([make_declaration()]),
    )

    assert "remote_transport" not in signature.parameters
    assert transport.requests == []
    assert transport.declarations == []


def test_helper_does_not_change_orchestrate_request_signature_or_behavior() -> None:
    chat = Capability(name="chat")
    result = ClusterResult(content="Hi", adapter="local-adapter")
    adapter = RecordingAdapter("local-adapter", [chat], result)
    node = make_node("local", [chat], ["local-adapter"])

    actual = asyncio.run(
        orchestrate_request(
            make_request(chat),
            NodeRegistry([node]),
            AdapterRegistry([adapter]),
        )
    )

    assert list(inspect.signature(orchestrate_request).parameters) == [
        "request",
        "node_registry",
        "adapter_registry",
    ]
    assert actual is result
    assert adapter.chat_requests == [make_request(chat)]


def test_helper_does_not_change_route_request_signature_or_behavior() -> None:
    chat = Capability(name="chat")
    node = make_node("local", [chat], ["missing-local-adapter"])

    assert list(inspect.signature(route_request).parameters) == [
        "request",
        "node_registry",
        "adapter_registry",
    ]
    with pytest.raises(
        NoMatchingAdapterError,
        match="No adapter provides capability on available node: chat",
    ):
        route_request(make_request(chat), NodeRegistry([node]), AdapterRegistry())
