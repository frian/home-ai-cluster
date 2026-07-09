import asyncio

import httpx
import pytest

from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.api.wiring import (
    StaticRemoteProofWiring,
    StaticRemoteProofWiringError,
    build_static_remote_proof_wiring,
    create_static_local_node_announcement,
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
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
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.main import create_app


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
        return ClusterResult(content="local result", adapter=self.name)


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
        return ClusterResult(content="remote result", adapter="remote")


def make_node(node_id: str, adapter_name: str = "recording") -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=[adapter_name],
    )


def make_remote_declaration() -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node("remote", "remote-adapter"),
        transport_address="http://remote.local:8000",
    )


def post_chat(payload: dict[str, object]) -> httpx.Response:
    async def post() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app())

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.post("/v1/chat", json=payload)

    return asyncio.run(post())


def test_create_static_runtime_adapter_registry_contains_ollama_adapter() -> None:
    registry = create_static_runtime_adapter_registry()

    adapters = registry.list_adapters()

    assert len(adapters) == 1
    assert isinstance(adapters[0], OllamaAdapter)
    assert adapters[0].name == "ollama"
    assert registry.adapters_for(Capability(name="chat")) == adapters


def test_create_static_local_node_announcement_returns_explicit_declaration() -> None:
    announcement = create_static_local_node_announcement()

    assert announcement.id == "local"
    assert announcement.name == "Local node"
    assert announcement.availability == "available"
    assert announcement.health == NodeHealth(healthy=True)
    assert announcement.capabilities == [Capability(name="chat")]
    assert announcement.adapters == ["ollama"]
    assert "models" not in NodeDescription.model_fields


def test_create_static_local_node_registry_contains_static_local_node() -> None:
    registry = create_static_local_node_registry()
    announcement = create_static_local_node_announcement()

    nodes = registry.list_nodes()

    assert len(nodes) == 1
    assert nodes[0] == announcement
    assert nodes[0].model_dump() == {
        "id": "local",
        "name": "Local node",
        "availability": "available",
        "health": {"healthy": True, "reason": None},
        "capabilities": [{"name": "chat"}],
        "adapters": ["ollama"],
    }
    assert "models" not in NodeDescription.model_fields


def test_static_remote_proof_wiring_can_be_constructed_in_memory() -> None:
    adapter = RecordingAdapter()
    transport = RecordingRemoteTransport()
    node_registry = NodeRegistry([make_node("local")])
    adapter_registry = AdapterRegistry([adapter])
    declaration = make_remote_declaration()

    wiring = build_static_remote_proof_wiring(
        node_registry=node_registry,
        adapter_registry=adapter_registry,
        remote_declaration=declaration,
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
    )

    assert wiring.node_registry is node_registry
    assert wiring.adapter_registry is adapter_registry
    assert wiring.remote_registry.list_declarations() == [declaration]
    assert wiring.remote_transport is transport
    assert wiring.selection_mode == RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY


def test_static_remote_proof_wiring_construction_is_inert() -> None:
    adapter = RecordingAdapter()
    transport = RecordingRemoteTransport()

    build_static_remote_proof_wiring(
        node_registry=NodeRegistry([make_node("local")]),
        adapter_registry=AdapterRegistry([adapter]),
        remote_declaration=make_remote_declaration(),
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.PREFER_DECLARED_REMOTE,
    )

    assert adapter.chat_requests == []
    assert transport.requests == []
    assert transport.declarations == []


@pytest.mark.parametrize(
    "remote_registry",
    [
        RemoteNodeDeclarationRegistry(),
        RemoteNodeDeclarationRegistry(
            [
                make_remote_declaration(),
                RemoteNodeDeclaration(
                    node=make_node("other-remote", "remote-adapter"),
                    transport_address="http://other-remote.local:8000",
                ),
            ]
        ),
    ],
)
def test_static_remote_proof_wiring_requires_one_declared_remote_node(
    remote_registry: RemoteNodeDeclarationRegistry,
) -> None:
    with pytest.raises(
        StaticRemoteProofWiringError,
        match="exactly one declared remote node",
    ):
        StaticRemoteProofWiring(
            node_registry=NodeRegistry([make_node("local")]),
            adapter_registry=AdapterRegistry([RecordingAdapter()]),
            remote_registry=remote_registry,
            remote_transport=RecordingRemoteTransport(),
            selection_mode=RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
        )


@pytest.mark.parametrize(
    "field",
    [
        "node_registry",
        "adapter_registry",
        "remote_registry",
        "remote_transport",
        "selection_mode",
    ],
)
def test_static_remote_proof_wiring_requires_complete_dependencies(
    field: str,
) -> None:
    values = {
        "node_registry": NodeRegistry([make_node("local")]),
        "adapter_registry": AdapterRegistry([RecordingAdapter()]),
        "remote_registry": RemoteNodeDeclarationRegistry([make_remote_declaration()]),
        "remote_transport": RecordingRemoteTransport(),
        "selection_mode": RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
    }
    values[field] = None

    with pytest.raises(StaticRemoteProofWiringError, match="requires"):
        StaticRemoteProofWiring(**values)  # type: ignore[arg-type]


def test_chat_endpoint_remains_local_only_without_static_remote_proof_wiring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    adapter = RecordingAdapter()
    transport = RecordingRemoteTransport()

    build_static_remote_proof_wiring(
        node_registry=NodeRegistry([make_node("local")]),
        adapter_registry=AdapterRegistry([adapter]),
        remote_declaration=make_remote_declaration(),
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
    )

    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        lambda: NodeRegistry([make_node("local")]),
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = post_chat(
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": "chat",
        }
    )

    assert response.status_code == 200
    assert response.json()["adapter"] == "recording"
    assert adapter.chat_requests == [
        ClusterRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            capability=Capability(name="chat"),
        )
    ]
    assert transport.requests == []
    assert transport.declarations == []
