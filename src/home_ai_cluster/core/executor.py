"""Execution helper for selected routing decisions."""

from home_ai_cluster.core.execution_target import (
    remote_declaration_for_routing_decision,
)
from home_ai_cluster.core.models import ClusterRequest, ClusterResult
from home_ai_cluster.core.remote_node import (
    DeclaredRemoteRoutingCandidate,
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.remote_transport import RemoteTransport
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


async def execute_remote_routing_decision(
    request: ClusterRequest,
    decision: RoutingDecision,
    declaration: RemoteNodeDeclaration,
    transport: RemoteTransport,
) -> ClusterResult:
    """Execute a routing decision through an explicit remote transport."""
    return await transport.send(request, declaration)


async def execute_declared_remote_routing_candidate(
    request: ClusterRequest,
    candidate: DeclaredRemoteRoutingCandidate,
    transport: RemoteTransport,
) -> ClusterResult:
    """Execute a declared remote candidate through explicit remote transport."""
    return await transport.send(request, candidate.declaration)


async def execute_declared_routing_decision(
    request: ClusterRequest,
    decision: RoutingDecision,
    remote_registry: RemoteNodeDeclarationRegistry,
    remote_transport: RemoteTransport,
) -> ClusterResult:
    """Execute through declared remote transport when the selected node matches."""
    declaration = remote_declaration_for_routing_decision(decision, remote_registry)

    if declaration is None:
        return await execute_local_routing_decision(request, decision)

    return await execute_remote_routing_decision(
        request,
        decision,
        declaration,
        remote_transport,
    )
