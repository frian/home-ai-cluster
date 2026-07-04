"""Static node boundary helpers."""

from home_ai_cluster.core.models import Capability, NodeDescription


def node_supports_capability(
    node: NodeDescription,
    capability: Capability,
) -> bool:
    """Return whether a static node declares support for a capability."""
    return node.availability == "available" and capability in node.capabilities


def node_declared_adapter_names(node: NodeDescription) -> list[str]:
    """Return adapter names declared by a static node description."""
    return list(node.adapters)
