"""Execution helper for selected routing decisions."""

from home_ai_cluster.core.models import ClusterRequest, ClusterResult
from home_ai_cluster.core.router import RoutingDecision


async def execute_local_routing_decision(
    request: ClusterRequest,
    decision: RoutingDecision,
) -> ClusterResult:
    """Execute the selected local adapter for a routing decision."""
    return await decision.adapter.chat(request)


async def execute_routing_decision(
    request: ClusterRequest,
    decision: RoutingDecision,
) -> ClusterResult:
    """Execute a routing decision using the current local execution path."""
    return await execute_local_routing_decision(request, decision)
