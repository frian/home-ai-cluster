"""Execution helper for selected routing decisions."""

from collections.abc import Awaitable, Callable

from home_ai_cluster.core.execution_intervals import (
    ExecutionIntervalCardinality,
    ExecutionPermissionDeniedError,
)
from home_ai_cluster.core.execution_target import (
    remote_declaration_for_routing_decision,
)
from home_ai_cluster.core.models import (
    ClassifyRequest,
    ClassifyResult,
    ClusterRequest,
    ClusterResult,
    ImageGenerationRequest,
    ImageGenerationResult,
    LocalRoutableRequest,
    LocalRoutableResult,
    RemoteTransportRequest,
    RemoteTransportResult,
    SourceGroundedChatRequest,
    SourceGroundedChatResult,
    SummarizeRequest,
    project_source_grounded_chat_request,
)
from home_ai_cluster.core.png_validation import validate_still_png
from home_ai_cluster.core.remote_node import (
    DeclaredRemoteRoutingCandidate,
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.remote_transport import RemoteTransport
from home_ai_cluster.core.router import RoutingDecision


class InvalidClassificationLabelError(Exception):
    """Raised when an adapter proposes a label outside the request's label set."""


async def _await_local_adapter_invocation(
    invocation: Callable[[], Awaitable[object]],
    execution_intervals: ExecutionIntervalCardinality | None,
    *,
    interval_already_entered: bool = False,
) -> object:
    if execution_intervals is None:
        return await invocation()
    if not interval_already_entered:
        if not await execution_intervals.try_enter():
            raise ExecutionPermissionDeniedError()
    try:
        return await invocation()
    finally:
        await execution_intervals.exit()


async def execute_local_routing_decision(
    request: LocalRoutableRequest,
    decision: RoutingDecision,
    execution_intervals: ExecutionIntervalCardinality | None = None,
    *,
    interval_already_entered: bool = False,
) -> LocalRoutableResult:
    """Execute the selected local adapter for a routing decision."""
    if isinstance(request, ClusterRequest):
        result = await _await_local_adapter_invocation(
            lambda: decision.adapter.chat(request),
            execution_intervals,
            interval_already_entered=interval_already_entered,
        )
        return ClusterResult(
            content=result.content,
            adapter=result.adapter,
            model=result.model,
            node_id=decision.node.id,
        )

    if isinstance(request, SourceGroundedChatRequest):
        projected_request = project_source_grounded_chat_request(request)
        result = await _await_local_adapter_invocation(
            lambda: decision.adapter.chat(projected_request),
            execution_intervals,
            interval_already_entered=interval_already_entered,
        )
        return SourceGroundedChatResult(
            content=result.content,
            sources=request.sources,
            adapter=result.adapter,
            model=result.model,
            node_id=decision.node.id,
        )

    if isinstance(request, SummarizeRequest):
        result = await _await_local_adapter_invocation(
            lambda: decision.adapter.summarize(request),
            execution_intervals,
            interval_already_entered=interval_already_entered,
        )
        return ClusterResult(
            content=result.content,
            adapter=result.adapter,
            model=result.model,
            node_id=decision.node.id,
        )

    if isinstance(request, ImageGenerationRequest):
        candidate = await _await_local_adapter_invocation(
            lambda: decision.adapter.generate_image(request),
            execution_intervals,
            interval_already_entered=interval_already_entered,
        )
        return ImageGenerationResult(
            image_bytes=validate_still_png(candidate),
            node_id=decision.node.id,
        )

    if isinstance(request, ClassifyRequest):
        proposal = await _await_local_adapter_invocation(
            lambda: decision.adapter.classify(request),
            execution_intervals,
            interval_already_entered=interval_already_entered,
        )
        if proposal not in request.labels:
            raise InvalidClassificationLabelError("Invalid classification label")
        return ClassifyResult(selected_label=proposal, node_id=decision.node.id)

    raise TypeError("Unsupported local routable request")


async def execute_routing_decision(
    request: LocalRoutableRequest,
    decision: RoutingDecision,
    execution_intervals: ExecutionIntervalCardinality | None = None,
) -> LocalRoutableResult:
    """Execute a routing decision using the current local execution path."""
    return await execute_local_routing_decision(request, decision, execution_intervals)


async def execute_remote_routing_decision(
    request: RemoteTransportRequest,
    decision: RoutingDecision,
    declaration: RemoteNodeDeclaration,
    transport: RemoteTransport,
) -> RemoteTransportResult:
    """Execute a routing decision through an explicit remote transport."""
    result = await transport.send(request, declaration)
    return result.model_copy(update={"node_id": declaration.node.id})


async def execute_declared_remote_routing_candidate(
    request: RemoteTransportRequest,
    candidate: DeclaredRemoteRoutingCandidate,
    transport: RemoteTransport,
) -> RemoteTransportResult:
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
