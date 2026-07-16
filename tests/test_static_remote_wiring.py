import pytest

from home_ai_cluster.api.wiring import (
    StaticRemoteProofWiring,
    StaticRemoteProofWiringError,
    StaticRemoteWiring,
    StaticRemoteWiringError,
    build_static_remote_proof_wiring,
    build_static_remote_wiring,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode


class RecordingAdapter:
    @property
    def name(self) -> str:
        return "recording"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        return RuntimeResult(content="local result", adapter=self.name)


class RecordingRemoteTransport:
    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        return ClusterResult(
            content="remote result",
            adapter="remote",
            node_id=declaration.node.id,
        )


def make_node(node_id: str, adapter_name: str) -> NodeDescription:
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


def test_build_static_remote_wiring_is_proof_neutral() -> None:
    node_registry = NodeRegistry([make_node("local", "recording")])
    adapter_registry = AdapterRegistry([RecordingAdapter()])
    declaration = make_remote_declaration()
    transport = RecordingRemoteTransport()

    wiring = build_static_remote_wiring(
        node_registry=node_registry,
        adapter_registry=adapter_registry,
        remote_declaration=declaration,
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.PREFER_DECLARED_REMOTE,
    )

    assert type(wiring) is StaticRemoteWiring
    assert wiring.node_registry is node_registry
    assert wiring.adapter_registry is adapter_registry
    assert wiring.remote_registry.list_declarations() == [declaration]
    assert wiring.remote_transport is transport
    assert wiring.selection_mode == RoutingCandidateSelectionMode.PREFER_DECLARED_REMOTE


def test_proof_builder_delegates_to_proof_neutral_wiring() -> None:
    wiring = build_static_remote_proof_wiring(
        node_registry=NodeRegistry([make_node("local", "recording")]),
        adapter_registry=AdapterRegistry([RecordingAdapter()]),
        remote_declaration=make_remote_declaration(),
        remote_transport=RecordingRemoteTransport(),
        selection_mode=RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
    )

    assert type(wiring) is StaticRemoteWiring
    assert isinstance(wiring, StaticRemoteProofWiring)
    assert wiring.selection_mode == RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY


def test_proof_names_remain_compatibility_aliases() -> None:
    assert StaticRemoteProofWiring is StaticRemoteWiring
    assert StaticRemoteProofWiringError is StaticRemoteWiringError


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
def test_static_remote_wiring_requires_exactly_one_remote_node(
    remote_registry: RemoteNodeDeclarationRegistry,
) -> None:
    with pytest.raises(
        StaticRemoteWiringError,
        match="exactly one declared remote node",
    ):
        StaticRemoteWiring(
            node_registry=NodeRegistry([make_node("local", "recording")]),
            adapter_registry=AdapterRegistry([RecordingAdapter()]),
            remote_registry=remote_registry,
            remote_transport=RecordingRemoteTransport(),
            selection_mode=RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
        )
