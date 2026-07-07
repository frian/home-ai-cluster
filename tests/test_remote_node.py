import pytest
from pydantic import ValidationError

from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
    build_remote_node_declaration_registry,
)


def make_node(node_id: str = "remote") -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["remote-adapter"],
    )


def make_declaration(node_id: str = "remote") -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node(node_id),
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
