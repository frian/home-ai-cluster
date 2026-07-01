"""Minimal core orchestration for Phase 1 requests."""

from home_ai_cluster.core.models import ClusterRequest, ClusterResult
from home_ai_cluster.core.registry import AdapterRegistry
from home_ai_cluster.core.router import route_request


async def orchestrate_request(
    request: ClusterRequest,
    registry: AdapterRegistry,
) -> ClusterResult:
    """Route a request to an adapter and return its normalized result."""
    decision = route_request(request, registry)

    return await decision.adapter.chat(request)
