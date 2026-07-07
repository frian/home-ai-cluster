"""Minimal core orchestration for static local requests."""

import httpx

from home_ai_cluster.core.executor import (
    execute_declared_routing_decision,
    execute_routing_decision,
)
from home_ai_cluster.core.models import ClusterRequest, ClusterResult
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclarationRegistry
from home_ai_cluster.core.remote_transport import HttpRemoteTransport, RemoteTransport
from home_ai_cluster.core.router import route_request


async def orchestrate_request(
    request: ClusterRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
) -> ClusterResult:
    """Route a request to an adapter and return its normalized result."""
    decision = route_request(request, node_registry, adapter_registry)

    return await execute_routing_decision(request, decision)


async def orchestrate_request_with_declared_remote(
    request: ClusterRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry,
    remote_transport: RemoteTransport,
) -> ClusterResult:
    """Route a request and execute through the explicit declared remote seam."""
    decision = route_request(request, node_registry, adapter_registry)

    return await execute_declared_routing_decision(
        request,
        decision,
        remote_registry,
        remote_transport,
    )


async def orchestrate_request_with_declared_http_remote(
    request: ClusterRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry,
    http_client: httpx.AsyncClient,
) -> ClusterResult:
    """Route a request through the explicit declared HTTP remote seam."""
    remote_transport = HttpRemoteTransport(http_client)

    return await orchestrate_request_with_declared_remote(
        request,
        node_registry,
        adapter_registry,
        remote_registry,
        remote_transport,
    )
