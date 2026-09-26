"""Minimal capability routing for static Phase 2 orchestration."""

from dataclasses import dataclass

from home_ai_cluster.adapters.base import RuntimeAdapter
from home_ai_cluster.core.models import (
    Capability,
    LocalRoutableRequest,
    NodeDescription,
)
from home_ai_cluster.core.node import node_declared_adapter_names
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry


class NoMatchingAdapterError(Exception):
    """Raised when no registered adapter provides the requested capability."""


@dataclass(frozen=True)
class RoutingDecision:
    """A minimal record of which node and adapter were selected."""

    node: NodeDescription
    adapter: RuntimeAdapter
    capability: Capability
    reason: str


def local_routing_decision_for_capability(
    capability: Capability,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
) -> RoutingDecision | None:
    """Return the existing local candidate decision without executing it."""
    nodes = node_registry.nodes_for(capability)

    bound_adapter = adapter_registry.bound_adapter_for(capability)
    if bound_adapter is not None and nodes:
        return RoutingDecision(
            node=nodes[0],
            adapter=bound_adapter,
            capability=capability,
            reason="Selected local adapter bound to requested capability.",
        )

    if adapter_registry.has_local_capability_bindings:
        return None

    for node in nodes:
        for adapter_name in node_declared_adapter_names(node):
            adapter = adapter_registry.adapter_named(adapter_name)
            if adapter is not None and capability in adapter.capabilities():
                return RoutingDecision(
                    node=node,
                    adapter=adapter,
                    capability=capability,
                    reason=(
                        "Selected first available node with requested capability "
                        "and matching adapter."
                    ),
                )

    return None


def route_request(
    request: LocalRoutableRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
) -> RoutingDecision:
    """Select the first available node and adapter for the requested capability."""
    decision = local_routing_decision_for_capability(
        request.capability, node_registry, adapter_registry
    )
    if decision is not None:
        return decision

    if adapter_registry.has_local_capability_bindings:
        raise NoMatchingAdapterError(
            f"No bound adapter provides capability: {request.capability.name}"
        )

    if not node_registry.nodes_for(request.capability):
        raise NoMatchingAdapterError(
            f"No available node provides capability: {request.capability.name}"
        )

    raise NoMatchingAdapterError(
        f"No adapter provides capability on available node: {request.capability.name}"
    )
