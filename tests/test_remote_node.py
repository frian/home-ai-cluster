import pytest
from pydantic import ValidationError

from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration


def make_node() -> NodeDescription:
    return NodeDescription(
        id="remote",
        name="Remote node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["remote-adapter"],
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
