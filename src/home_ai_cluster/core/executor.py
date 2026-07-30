"""Execution helper for selected routing decisions."""

from home_ai_cluster.core.execution_target import (
    remote_declaration_for_routing_decision,
)
from home_ai_cluster.core.models import (
    ClassifyRequest,
    ClassifyResult,
    ClusterRequest,
    ClusterResult,
    SummarizeRequest,
)
from home_ai_cluster.core.remote_node import (
    DeclaredRemoteRoutingCandidate,
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.remote_transport import RemoteTransport
from home_ai_cluster.core.router import RoutingDecision


class InvalidClassificationLabelError(Exception):
    """Raised when an adapter proposes a label outside the request's label set."""


async def execute_local_routing_decision(
    request: ClusterRequest | SummarizeRequest | ClassifyRequest,
    decision: RoutingDecision,
) -> ClusterResult | ClassifyResult:
    """Execute the selected local adapter for a routing decision."""
    if isinstance(request, ClusterRequest):
        result = await decision.adapter.chat(request)
        return ClusterResult(
            content=result.content,
            adapter=result.adapter,
            model=result.model,
            node_id=decision.node.id,
        )

    if isinstance(request, SummarizeRequest):
        result = await decision.adapter.summarize(request)
        return ClusterResult(
            content=result.content,
            adapter=result.adapter,
            model=result.model,
            node_id=decision.node.id,
        )

    proposal = await decision.adapter.classify(request)
    if proposal not in request.labels:
        raise InvalidClassificationLabelError("Invalid classification label")

    return ClassifyResult(
        selected_label=proposal,
        node_id=decision.node.id,
    )


async def execute_routing_decision(
    request: ClusterRequest | SummarizeRequest | ClassifyRequest,
    decision: RoutingDecision,
) -> ClusterResult | ClassifyResult:
    """Execute a routing decision using the current local execution path."""
    return await execute_local_routing_decision(request, decision)


async def execute_remote_routing_decision(
    request: ClusterRequest,
    decision: RoutingDecision,
    declaration: RemoteNodeDeclaration,
    transport: RemoteTransport,
) -> ClusterResult:
    """Execute a routing decision through an explicit remote transport."""
    result = await transport.send(request, declaration)
    return result.model_copy(update={"node_id": declaration.node.id})


async def execute_declared_remote_routing_candidate(
    request: ClusterRequest,
    candidate: DeclaredRemoteRoutingCandidate,
    transport: RemoteTransport,
) -> ClusterResult:
    """Execute a declared remote candidate through explicit remote transport."""
    result = await transport.send(request, candidate.declaration)
    return result.model_copy(update={"node_id": candidate.node.id})


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
