"""Minimal core orchestration for static local requests."""

from home_ai_cluster.core.executor import execute_routing_decision
from home_ai_cluster.core.models import ClusterRequest, ClusterResult
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.router import route_request


async def orchestrate_request(
    request: ClusterRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
) -> ClusterResult:
    """Route a request to an adapter and return its normalized result."""
    decision = route_request(request, node_registry, adapter_registry)

    return await execute_routing_decision(request, decision)
