"""RFC-0144 capability-only projection of active caller routing eligibility."""

from home_ai_cluster.core.models import Capability
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclarationRegistry,
    declared_remote_declarations_for_capability,
)
from home_ai_cluster.core.router import local_routing_decision_for_capability
from home_ai_cluster.core.static_capabilities import ACCEPTED_CAPABILITY_NAMES


def project_caller_routable_capabilities(
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry | None = None,
) -> tuple[str, ...]:
    """Project accepted capabilities with an existing ordinary routing path."""
    projected: list[str] = []
    for name in ACCEPTED_CAPABILITY_NAMES:
        capability = Capability(name=name)
        local = local_routing_decision_for_capability(
            capability, node_registry, adapter_registry
        )
        remote = remote_registry is not None and bool(
            declared_remote_declarations_for_capability(capability, remote_registry)
        )
        if local is not None or remote:
            projected.append(name)
    return tuple(projected)
