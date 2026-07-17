from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    DeclaredRemoteRoutingCandidate,
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.routing_candidates import (
    RoutingCandidates,
    routing_candidates_for_request,
)


def make_request() -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
    )


def make_declaration(node_id: str) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id=node_id,
            name=f"{node_id} node",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="chat")],
            adapters=["remote-adapter"],
        ),
        transport_address=f"http://{node_id}.local:8000",
    )


def make_candidate(node_id: str) -> DeclaredRemoteRoutingCandidate:
    declaration = make_declaration(node_id)
    return DeclaredRemoteRoutingCandidate(
        node=declaration.node,
        declaration=declaration,
        capability=Capability(name="chat"),
        reason="test candidate",
    )


def test_routing_candidates_retain_ordered_remote_collection() -> None:
    first = make_declaration("remote-a")
    second = make_declaration("remote-b")
    candidates = routing_candidates_for_request(
        make_request(),
        NodeRegistry(),
        AdapterRegistry(),
        RemoteNodeDeclarationRegistry([first, second]),
    )

    assert [candidate.declaration for candidate in candidates.declared_remotes] == [
        first,
        second,
    ]
    assert candidates.declared_remote is candidates.declared_remotes[0]


def test_routing_candidates_retain_empty_remote_collection() -> None:
    candidates = routing_candidates_for_request(
        make_request(),
        NodeRegistry(),
        AdapterRegistry(),
        RemoteNodeDeclarationRegistry(),
    )

    assert candidates.declared_remotes == ()
    assert candidates.declared_remote is None


def test_legacy_single_remote_construction_populates_collection() -> None:
    first = make_candidate("remote-a")
    candidates = RoutingCandidates(local=None, declared_remote=first)

    assert candidates.declared_remote is first
    assert candidates.declared_remotes == (first,)


def test_collection_construction_sets_first_candidate_compatibility_field() -> None:
    first = make_candidate("remote-a")
    second = make_candidate("remote-b")
    candidates = RoutingCandidates(
        local=None,
        declared_remote=None,
        declared_remotes=(first, second),
    )

    assert candidates.declared_remote is first
    assert candidates.declared_remotes == (first, second)
