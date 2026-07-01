"""Naive capability routing for Phase 1 orchestration."""

from dataclasses import dataclass

from home_ai_cluster.adapters.base import RuntimeAdapter
from home_ai_cluster.core.models import Capability, ClusterRequest
from home_ai_cluster.core.registry import AdapterRegistry


class NoMatchingAdapterError(Exception):
    """Raised when no registered adapter provides the requested capability."""


@dataclass(frozen=True)
class RoutingDecision:
    """A minimal record of which adapter was selected for a request."""

    adapter: RuntimeAdapter
    capability: Capability


def route_request(
    request: ClusterRequest,
    registry: AdapterRegistry,
) -> RoutingDecision:
    """Select the first registered adapter matching the requested capability."""
    adapters = registry.adapters_for(request.capability)

    if not adapters:
        raise NoMatchingAdapterError(
            f"No adapter provides capability: {request.capability.name}"
        )

    return RoutingDecision(adapter=adapters[0], capability=request.capability)
