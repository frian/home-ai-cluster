import inspect

import pytest
from pydantic import ValidationError

from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.remote_node import (
    DECLARED_REMOTE_ROUTING_REASON,
    DeclaredRemoteRoutingCandidate,
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
    build_remote_node_declaration_registry,
    declared_remote_declarations_for_request,
    declared_remote_routing_candidate_for_request,
)


def make_request(capability: Capability | None = None) -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=capability or Capability(name="chat"),
    )


def make_node(
    node_id: str = "remote",
    capabilities: list[Capability] | None = None,
    availability: str = "available",
    adapters: list[str] | None = None,
) -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability=availability,  # type: ignore[arg-type]
        health=NodeHealth(healthy=True),
        capabilities=capabilities or [Capability(name="chat")],
        adapters=adapters or ["remote-adapter"],
    )


def make_declaration(
    node_id: str = "remote",
    capabilities: list[Capability] | None = None,
    availability: str = "available",
    adapters: list[str] | None = None,
) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node(
            node_id,
            capabilities=capabilities,
            availability=availability,
            adapters=adapters,
        ),
        transport_address=f"http://{node_id}.local:8000",
    )


def test_remote_node_declaration_wraps_node_and_transport_address() -> None:
    node = make_node()
    declaration = RemoteNodeDeclaration(
        node=node,
        transport_address="http://remote-node.local:8000",
    )

    assert declaration.node == node
    assert declaration.transport_address == "http://remote-node.local:8000"


def test_remote_node_declaration_preserves_exact_node_object() -> None:
    node = make_node()

    declaration = RemoteNodeDeclaration(
        node=node,
        transport_address="http://remote-node.local:8000",
    )

    assert declaration.node is node


def test_remote_node_declaration_stores_transport_address_exactly() -> None:
    address = "  http://remote-node.local:8000/internal  "

    declaration = RemoteNodeDeclaration(
        node=make_node(),
        transport_address=address,
    )

    assert declaration.transport_address == address


def test_remote_node_declaration_rejects_empty_transport_address() -> None:
    with pytest.raises(ValidationError):
        RemoteNodeDeclaration(node=make_node(), transport_address="")


def test_node_description_does_not_gain_transport_address_or_address() -> None:
    assert "transport_address" not in NodeDescription.model_fields
    assert "address" not in NodeDescription.model_fields


def test_remote_node_declaration_does_not_imply_routing_or_transport_behavior() -> None:
    declaration = RemoteNodeDeclaration(
        node=make_node(),
        transport_address="http://remote-node.local:8000",
    )

    assert not hasattr(declaration, "route")
    assert not hasattr(declaration, "send")
    assert not hasattr(declaration, "register")
    assert not hasattr(declaration, "discover")


def test_empty_remote_node_declaration_registry_returns_empty_list() -> None:
    registry = RemoteNodeDeclarationRegistry()

    assert registry.list_declarations() == []


def test_remote_node_declaration_registry_preserves_order() -> None:
    first = make_declaration("first")
    second = make_declaration("second")

    registry = RemoteNodeDeclarationRegistry([first, second])

    assert registry.list_declarations() == [first, second]


def test_remote_node_declaration_registry_list_declarations_returns_copy() -> None:
    declaration = make_declaration()
    registry = RemoteNodeDeclarationRegistry([declaration])

    declarations = registry.list_declarations()
    declarations.append(make_declaration("mutated"))

    assert registry.list_declarations() == [declaration]


def test_remote_node_declaration_registry_returns_declaration_by_node_id() -> None:
    first = make_declaration("first")
    second = make_declaration("second")
    registry = RemoteNodeDeclarationRegistry([first, second])

    assert registry.declaration_for_node_id("second") is second


def test_remote_node_declaration_registry_returns_none_for_unknown_node_id() -> None:
    registry = RemoteNodeDeclarationRegistry([make_declaration("known")])

    assert registry.declaration_for_node_id("unknown") is None


def test_remote_node_declaration_registry_lookup_does_not_imply_behavior() -> None:
    declaration = make_declaration()
    registry = RemoteNodeDeclarationRegistry([declaration])

    found = registry.declaration_for_node_id("remote")

    assert found is declaration
    assert not hasattr(registry, "route")
    assert not hasattr(registry, "send")
    assert not hasattr(registry, "register")
    assert not hasattr(registry, "discover")
    assert not hasattr(registry, "connect")


def test_build_remote_node_declaration_registry_uses_explicit_declarations() -> None:
    first = make_declaration("first")
    second = make_declaration("second")

    registry = build_remote_node_declaration_registry([first, second])

    assert registry.list_declarations() == [first, second]


def test_built_remote_node_declaration_registry_matches_manual_registry() -> None:
    first = make_declaration("first")
    second = make_declaration("second")

    built_registry = build_remote_node_declaration_registry((first, second))
    manual_registry = RemoteNodeDeclarationRegistry([first, second])

    assert built_registry.list_declarations() == manual_registry.list_declarations()
    assert built_registry.declaration_for_node_id("second") is second
    assert built_registry.declaration_for_node_id(
        "second"
    ) is manual_registry.declaration_for_node_id("second")
    assert built_registry.declaration_for_node_id("unknown") is None


def test_build_remote_node_declaration_registry_does_not_imply_external_sources() -> (
    None
):
    registry = build_remote_node_declaration_registry([make_declaration()])

    assert not hasattr(registry, "load")
    assert not hasattr(registry, "load_config")
    assert not hasattr(registry, "load_environment")
    assert not hasattr(registry, "discover")
    assert not hasattr(registry, "persist")
    assert not hasattr(registry, "register")
    assert not hasattr(registry, "route")
    assert not hasattr(registry, "chat")


def test_declared_remote_declarations_for_request_returns_available_match() -> None:
    declaration = make_declaration()
    registry = RemoteNodeDeclarationRegistry([declaration])

    eligible = declared_remote_declarations_for_request(make_request(), registry)

    assert eligible == [declaration]


def test_declared_remote_declarations_for_request_ignores_missing_capability() -> None:
    declaration = make_declaration(
        capabilities=[Capability(name="embedding")],
    )
    registry = RemoteNodeDeclarationRegistry([declaration])

    eligible = declared_remote_declarations_for_request(make_request(), registry)

    assert eligible == []


def test_declared_remote_declarations_for_request_ignores_unknown_declaration() -> None:
    declaration = make_declaration(availability="unknown")
    registry = RemoteNodeDeclarationRegistry([declaration])

    eligible = declared_remote_declarations_for_request(make_request(), registry)

    assert eligible == []


def test_declared_remote_declarations_for_request_ignores_unavailable_declaration() -> (
    None
):
    declaration = make_declaration(availability="unavailable")
    registry = RemoteNodeDeclarationRegistry([declaration])

    eligible = declared_remote_declarations_for_request(make_request(), registry)

    assert eligible == []


def test_declared_remote_declarations_for_request_does_not_require_local_adapter() -> (
    None
):
    declaration = make_declaration(adapters=["remote-only-adapter"])
    registry = RemoteNodeDeclarationRegistry([declaration])

    eligible = declared_remote_declarations_for_request(make_request(), registry)

    assert eligible == [declaration]


def test_declared_remote_declarations_for_request_preserves_declaration_order() -> None:
    first = make_declaration("first")
    ignored = make_declaration(
        "ignored",
        capabilities=[Capability(name="embedding")],
    )
    second = make_declaration("second")
    registry = RemoteNodeDeclarationRegistry([first, ignored, second])

    eligible = declared_remote_declarations_for_request(make_request(), registry)

    assert eligible == [first, second]


def test_declared_remote_routing_candidate_selects_first_eligible_declaration() -> None:
    ignored = make_declaration(
        "ignored",
        capabilities=[Capability(name="embedding")],
    )
    selected = make_declaration("selected")
    later = make_declaration("later")
    registry = RemoteNodeDeclarationRegistry([ignored, selected, later])

    candidate = declared_remote_routing_candidate_for_request(make_request(), registry)

    assert candidate == DeclaredRemoteRoutingCandidate(
        node=selected.node,
        declaration=selected,
        capability=Capability(name="chat"),
        reason=DECLARED_REMOTE_ROUTING_REASON,
    )


def test_declared_remote_routing_candidate_includes_declaration_node() -> None:
    declaration = make_declaration()
    registry = RemoteNodeDeclarationRegistry([declaration])

    candidate = declared_remote_routing_candidate_for_request(make_request(), registry)

    assert candidate is not None
    assert candidate.node is declaration.node


def test_declared_remote_routing_candidate_includes_selected_declaration() -> None:
    declaration = make_declaration()
    registry = RemoteNodeDeclarationRegistry([declaration])

    candidate = declared_remote_routing_candidate_for_request(make_request(), registry)

    assert candidate is not None
    assert candidate.declaration is declaration


def test_declared_remote_routing_candidate_includes_requested_capability() -> None:
    capability = Capability(name="chat")
    registry = RemoteNodeDeclarationRegistry([make_declaration()])

    candidate = declared_remote_routing_candidate_for_request(
        make_request(capability),
        registry,
    )

    assert candidate is not None
    assert candidate.capability == capability


def test_declared_remote_routing_candidate_reason_names_remote_eligibility() -> None:
    registry = RemoteNodeDeclarationRegistry([make_declaration()])

    candidate = declared_remote_routing_candidate_for_request(make_request(), registry)

    assert candidate is not None
    assert "declared remote routing eligibility" in candidate.reason


def test_declared_remote_routing_candidate_returns_none_for_missing_capability() -> (
    None
):
    declaration = make_declaration(
        capabilities=[Capability(name="embedding")],
    )
    registry = RemoteNodeDeclarationRegistry([declaration])

    candidate = declared_remote_routing_candidate_for_request(make_request(), registry)

    assert candidate is None


def test_declared_remote_routing_candidate_ignores_unknown_and_unavailable() -> None:
    unknown = make_declaration("unknown", availability="unknown")
    unavailable = make_declaration("unavailable", availability="unavailable")
    available = make_declaration("available")
    registry = RemoteNodeDeclarationRegistry([unknown, unavailable, available])

    candidate = declared_remote_routing_candidate_for_request(make_request(), registry)

    assert candidate is not None
    assert candidate.declaration is available


def test_declared_remote_routing_candidate_does_not_require_local_adapter() -> None:
    declaration = make_declaration(adapters=["remote-only-adapter"])
    registry = RemoteNodeDeclarationRegistry([declaration])

    candidate = declared_remote_routing_candidate_for_request(make_request(), registry)

    signature = inspect.signature(declared_remote_routing_candidate_for_request)
    assert list(signature.parameters) == ["request", "remote_registry"]
    assert candidate is not None
    assert candidate.declaration is declaration


def test_declared_remote_routing_candidate_preserves_declaration_order() -> None:
    first = make_declaration("first")
    second = make_declaration("second")
    registry = RemoteNodeDeclarationRegistry([first, second])

    candidate = declared_remote_routing_candidate_for_request(make_request(), registry)

    assert candidate is not None
    assert candidate.declaration is first
