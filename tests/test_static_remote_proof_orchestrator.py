import asyncio

import pytest

from home_ai_cluster.api.proof_orchestrator import (
    NoSelectedStaticProofCandidateError,
    orchestrate_static_remote_proof,
)
from home_ai_cluster.api.wiring import build_static_remote_proof_wiring
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
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode


class RecordingAdapter:
    def __init__(self) -> None:
        self.chat_requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return "recording"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        self.chat_requests.append(request)
        return ClusterResult(
            content="local result", adapter=self.name, node_id="adapter-result"
        )


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
        return ClusterResult(
            content="remote result", adapter="remote", node_id="remote-response"
        )


def make_request(capability: str = "chat") -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name=capability),
    )


def make_node(
    node_id: str,
    adapter_name: str,
    capability: str = "chat",
) -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name=capability)],
        adapters=[adapter_name],
    )


def make_remote_declaration(capability: str = "chat") -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node("remote", "remote-adapter", capability),
        transport_address="http://remote.local:8000",
    )


def make_wiring(
    mode: RoutingCandidateSelectionMode,
    *,
    local_capability: str = "chat",
    remote_capability: str = "chat",
) -> tuple[object, RecordingAdapter, RecordingRemoteTransport]:
    adapter = RecordingAdapter()
    transport = RecordingRemoteTransport()
    local_node = make_node("local", adapter.name, local_capability)
    wiring = build_static_remote_proof_wiring(
        node_registry=NodeRegistry([local_node]),
        adapter_registry=AdapterRegistry([adapter]),
        remote_declaration=make_remote_declaration(remote_capability),
        remote_transport=transport,
        selection_mode=mode,
    )
    return wiring, adapter, transport


def test_local_only_selects_and_executes_local_candidate() -> None:
    wiring, adapter, transport = make_wiring(RoutingCandidateSelectionMode.LOCAL_ONLY)
    request = make_request()

    result = asyncio.run(orchestrate_static_remote_proof(request, wiring))

    assert result.adapter == "recording"
    assert adapter.chat_requests == [request]
    assert transport.requests == []
    assert transport.declarations == []


def test_declared_remote_only_selects_and_executes_remote_candidate() -> None:
    wiring, adapter, transport = make_wiring(
        RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY
    )
    request = make_request()

    result = asyncio.run(orchestrate_static_remote_proof(request, wiring))

    assert result.adapter == "remote"
    assert adapter.chat_requests == []
    assert transport.requests == [request]
    assert transport.declarations == wiring.remote_registry.list_declarations()


def test_prefer_local_is_deterministic_selection_not_runtime_fallback() -> None:
    wiring, adapter, transport = make_wiring(RoutingCandidateSelectionMode.PREFER_LOCAL)

    result = asyncio.run(orchestrate_static_remote_proof(make_request(), wiring))

    assert result.adapter == "recording"
    assert len(adapter.chat_requests) == 1
    assert transport.requests == []


def test_prefer_declared_remote_is_deterministic_selection() -> None:
    wiring, adapter, transport = make_wiring(
        RoutingCandidateSelectionMode.PREFER_DECLARED_REMOTE
    )

    result = asyncio.run(orchestrate_static_remote_proof(make_request(), wiring))

    assert result.adapter == "remote"
    assert adapter.chat_requests == []
    assert len(transport.requests) == 1


def test_missing_candidate_fails_explicitly() -> None:
    wiring, adapter, transport = make_wiring(
        RoutingCandidateSelectionMode.LOCAL_ONLY,
        local_capability="code",
        remote_capability="vision",
    )

    with pytest.raises(
        NoSelectedStaticProofCandidateError,
        match="produced no routing candidate",
    ):
        asyncio.run(orchestrate_static_remote_proof(make_request(), wiring))

    assert adapter.chat_requests == []
    assert transport.requests == []
