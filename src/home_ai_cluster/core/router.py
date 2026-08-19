"""Minimal capability routing for static Phase 2 orchestration."""

from dataclasses import dataclass

from home_ai_cluster.adapters.base import RuntimeAdapter
from home_ai_cluster.core.models import (
    Capability,
    NodeDescription,
    RoutableRequest,
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


def route_request(
    request: RoutableRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
) -> RoutingDecision:
    """Select the first available node and adapter for the requested capability."""
    nodes = node_registry.nodes_for(request.capability)

    for node in nodes:
        for adapter_name in node_declared_adapter_names(node):
            adapter = adapter_registry.adapter_named(adapter_name)
            if adapter is not None and request.capability in adapter.capabilities():
                return RoutingDecision(
                    node=node,
                    adapter=adapter,
                    capability=request.capability,
                    reason=(
                        "Selected first available node with requested capability "
                        "and matching adapter."
                    ),
                )

    if not nodes:
        raise NoMatchingAdapterError(
            f"No available node provides capability: {request.capability.name}"
        )

    raise NoMatchingAdapterError(
        f"No adapter provides capability on available node: {request.capability.name}"
    )
