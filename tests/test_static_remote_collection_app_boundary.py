from home_ai_cluster.api.wiring import build_static_remote_collection_wiring
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.main import create_app


class RecordingRemoteTransport:
    async def send(self, request, declaration):
        raise AssertionError("application boundary test must not execute transport")


def make_node(node_id: str) -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["ollama"],
    )


def make_remote(node_id: str, address: str) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node(node_id),
        transport_address=address,
    )


def test_create_app_stores_ordered_static_remote_collection_wiring() -> None:
    first = make_remote("remote-a", "http://remote-a.local:8000")
    second = make_remote("remote-b", "http://remote-b.local:8000")
    wiring = build_static_remote_collection_wiring(
        node_registry=NodeRegistry([make_node("local")]),
        adapter_registry=AdapterRegistry(),
        remote_declarations=[first, second],
        remote_transport=RecordingRemoteTransport(),
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )

    app = create_app(static_remote_collection_wiring=wiring)

    assert app.state.static_remote_collection_wiring is wiring
    assert wiring.remote_registry.list_declarations() == [first, second]
    assert app.state.static_remote_wiring is None
    assert app.state.static_remote_proof_wiring is None


def test_create_app_without_collection_wiring_stores_none() -> None:
    app = create_app()

    assert app.state.static_remote_collection_wiring is None
