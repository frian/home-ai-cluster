from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.remote_node import (
    DECLARED_REMOTE_ROUTING_REASON,
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
    declared_remote_routing_candidate_for_request,
    declared_remote_routing_candidates_for_request,
)


def make_request() -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
    )


def make_declaration(
    node_id: str,
    capability_name: str = "chat",
) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id=node_id,
            name=f"{node_id} node",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name=capability_name)],
            adapters=["remote-adapter"],
        ),
        transport_address=f"http://{node_id}.local:8000",
    )


def test_discovers_all_eligible_remote_candidates_in_declaration_order() -> None:
    first = make_declaration("remote-a")
    ignored = make_declaration("embedding-only", "embedding")
    second = make_declaration("remote-b")

    candidates = declared_remote_routing_candidates_for_request(
        make_request(),
        RemoteNodeDeclarationRegistry([first, ignored, second]),
    )

    assert [candidate.declaration for candidate in candidates] == [first, second]
    assert [candidate.node.id for candidate in candidates] == [
        "remote-a",
        "remote-b",
    ]
    assert all(
        candidate.capability == Capability(name="chat") for candidate in candidates
    )
    assert all(
        candidate.reason == DECLARED_REMOTE_ROUTING_REASON
        for candidate in candidates
    )


def test_discovers_no_candidates_when_none_are_eligible() -> None:
    candidates = declared_remote_routing_candidates_for_request(
        make_request(),
        RemoteNodeDeclarationRegistry([make_declaration("embedding", "embedding")]),
    )

    assert candidates == []


def test_single_candidate_helper_remains_first_candidate_seam() -> None:
    first = make_declaration("remote-a")
    second = make_declaration("remote-b")
    registry = RemoteNodeDeclarationRegistry([first, second])

    selected = declared_remote_routing_candidate_for_request(
        make_request(),
        registry,
    )
    candidates = declared_remote_routing_candidates_for_request(
        make_request(),
        registry,
    )

    assert selected == candidates[0]
    assert selected is not None
    assert selected.declaration is first
