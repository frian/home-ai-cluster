from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.node import (
    node_declared_adapter_names,
    node_supports_capability,
)


def make_node(
    *,
    availability: str = "available",
    healthy: bool = True,
    capabilities: list[Capability] | None = None,
    adapters: list[str] | None = None,
) -> NodeDescription:
    return NodeDescription(
        id="local",
        name="Local node",
        availability=availability,  # type: ignore[arg-type]
        health=NodeHealth(healthy=healthy),
        capabilities=capabilities or [Capability(name="chat")],
        adapters=adapters or ["ollama"],
    )


def test_available_node_with_matching_capability_supports_capability() -> None:
    chat = Capability(name="chat")
    node = make_node(capabilities=[chat])

    assert node_supports_capability(node, chat) is True


def test_unavailable_node_does_not_support_capability() -> None:
    chat = Capability(name="chat")
    node = make_node(availability="unavailable", capabilities=[chat])

    assert node_supports_capability(node, chat) is False


def test_unhealthy_available_node_still_supports_capability() -> None:
    chat = Capability(name="chat")
    node = make_node(healthy=False, capabilities=[chat])

    assert node_supports_capability(node, chat) is True


def test_declared_adapter_names_are_returned_from_node_description() -> None:
    node = make_node(adapters=["ollama", "test"])

    assert node_declared_adapter_names(node) == ["ollama", "test"]


def test_declared_adapter_names_returns_copy() -> None:
    node = make_node(adapters=["ollama"])

    adapter_names = node_declared_adapter_names(node)
    adapter_names.append("mutated")

    assert node.adapters == ["ollama"]
