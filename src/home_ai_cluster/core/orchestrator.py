"""Minimal core orchestration for static local requests."""

from dataclasses import dataclass

import httpx

from home_ai_cluster.adapters.base import (
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.core.execution_intervals import (
    ExecutionIntervalCardinality,
    ExecutionPermissionDeniedError,
)
from home_ai_cluster.core.executor import (
    execute_declared_remote_routing_candidate,
    execute_declared_routing_decision,
    execute_local_routing_decision,
    execute_routing_decision,
)
from home_ai_cluster.core.models import (
    ClusterRequest,
    ClusterResult,
    LocalRoutableRequest,
    LocalRoutableResult,
    RemoteTransportRequest,
    RemoteTransportResult,
    SummarizeRequest,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclarationRegistry
from home_ai_cluster.core.remote_transport import (
    HttpRemoteTransport,
    RemoteExecutionPermissionDeniedError,
    RemoteTransport,
)
from home_ai_cluster.core.router import route_request
from home_ai_cluster.core.routing_candidates import (
    AutomaticCapabilitySelectionExplanation,
    SelectedRoutingCandidate,
    routing_candidates_for_request,
    select_automatic_capability_routing_candidate,
)


class InvalidSelectedRoutingCandidateError(Exception):
    """Raised when selected candidate orchestration receives no single candidate."""


class MissingRemoteTransportError(Exception):
    """Raised when declared remote execution lacks an explicit transport."""


class NoSelectableRoutingCandidateError(Exception):
    """Raised when automatic capability selection cannot select a candidate."""

    def __init__(self, explanation: AutomaticCapabilitySelectionExplanation) -> None:
        super().__init__(
            "Automatic capability selection produced no selectable candidate"
        )
        self.explanation = explanation


@dataclass(frozen=True)
class AutomaticCapabilityRoutingOutcome:
    """Request-scoped selection explanation and successful normalized result."""

    explanation: AutomaticCapabilitySelectionExplanation
    result: RemoteTransportResult


async def orchestrate_request(
    request: LocalRoutableRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
) -> LocalRoutableResult:
    """Route a request to an adapter and return its normalized result."""
    return await _orchestrate_request(
        request, node_registry, adapter_registry, execution_intervals=None
    )


async def orchestrate_composed_request(
    request: LocalRoutableRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    execution_intervals: ExecutionIntervalCardinality,
) -> LocalRoutableResult:
    """Route a request through one ordinary composed application process."""
    decision = route_request(request, node_registry, adapter_registry)
    if not await execution_intervals.try_enter():
        raise ExecutionPermissionDeniedError()
    return await execute_local_routing_decision(
        request, decision, execution_intervals, interval_already_entered=True
    )


async def orchestrate_receiver_composed_request(
    request: RemoteTransportRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    execution_intervals: ExecutionIntervalCardinality,
) -> RemoteTransportResult:
    """Execute a received internal request after receiver-local permission."""
    decision = route_request(request, node_registry, adapter_registry)
    if not await execution_intervals.try_enter():
        raise ExecutionPermissionDeniedError()
    return await execute_local_routing_decision(
        request, decision, execution_intervals, interval_already_entered=True
    )


async def _orchestrate_request(
    request: LocalRoutableRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    execution_intervals: ExecutionIntervalCardinality | None,
) -> LocalRoutableResult:
    decision = route_request(request, node_registry, adapter_registry)

    return await execute_routing_decision(request, decision, execution_intervals)


async def orchestrate_request_with_selected_candidate(
    request: RemoteTransportRequest,
    selected: SelectedRoutingCandidate,
    *,
    remote_transport: RemoteTransport | None = None,
    execution_intervals: ExecutionIntervalCardinality | None = None,
    local_interval_already_entered: bool = False,
) -> RemoteTransportResult:
    """Execute an already selected routing candidate without routing again."""
    if selected is None:
        raise InvalidSelectedRoutingCandidateError(
            "Selected routing candidate is required"
        )

    has_local = selected.local is not None
    has_declared_remote = selected.declared_remote is not None

    if has_local == has_declared_remote:
        raise InvalidSelectedRoutingCandidateError(
            "Selected routing candidate must contain exactly one candidate"
        )

    if selected.local is not None:
        if execution_intervals is None:
            return await execute_local_routing_decision(
                request,
                selected.local.decision,
            )
        return await execute_local_routing_decision(
            request,
            selected.local.decision,
            execution_intervals,
            interval_already_entered=local_interval_already_entered,
        )

    if remote_transport is None:
        raise MissingRemoteTransportError(
            "Declared remote selected candidate requires RemoteTransport"
        )

    return await execute_declared_remote_routing_candidate(
        request,
        selected.declared_remote,
        remote_transport,
    )


async def orchestrate_request_with_automatic_capability_explanation(
    request: RemoteTransportRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry,
    remote_transport: RemoteTransport | None = None,
) -> AutomaticCapabilityRoutingOutcome:
    """Select once, execute once, and preserve the same request-scoped explanation."""
    candidates = routing_candidates_for_request(
        request,
        node_registry,
        adapter_registry,
        remote_registry,
    )
    selection = select_automatic_capability_routing_candidate(request, candidates)

    if selection.selected is None:
        raise NoSelectableRoutingCandidateError(selection.explanation)

    result = await orchestrate_request_with_selected_candidate(
        request,
        selection.selected,
        remote_transport=remote_transport,
    )
    return AutomaticCapabilityRoutingOutcome(
        explanation=selection.explanation,
        result=result,
    )


async def orchestrate_request_with_automatic_capability_selection(
    request: RemoteTransportRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry,
    remote_transport: RemoteTransport,
) -> RemoteTransportResult:
    """Compose explicit candidate discovery, automatic selection, and execution."""
    outcome = await orchestrate_request_with_automatic_capability_explanation(
        request,
        node_registry,
        adapter_registry,
        remote_registry,
        remote_transport,
    )
    return outcome.result


async def orchestrate_request_with_static_remote_fallback(
    request: RemoteTransportRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry,
    remote_transport: RemoteTransport,
    execution_intervals: ExecutionIntervalCardinality | None = None,
) -> RemoteTransportResult:
    """Execute the accepted local-to-declared-remote fallback once."""
    candidates = routing_candidates_for_request(
        request,
        node_registry,
        adapter_registry,
        remote_registry,
    )
    selection = select_automatic_capability_routing_candidate(request, candidates)

    if selection.selected is None:
        raise NoSelectableRoutingCandidateError(selection.explanation)

    if selection.selected.local is None:
        try:
            return await orchestrate_request_with_selected_candidate(
                request,
                selection.selected,
                remote_transport=remote_transport,
                execution_intervals=execution_intervals,
            )
        except RemoteExecutionPermissionDeniedError as exc:
            raise ExecutionPermissionDeniedError(selection.explanation) from exc

    local_permitted = (
        execution_intervals is None or await execution_intervals.try_enter()
    )
    if not local_permitted:
        if request.constraints.local_only or candidates.declared_remote is None:
            raise ExecutionPermissionDeniedError(selection.explanation)
        try:
            return await execute_declared_remote_routing_candidate(
                request, candidates.declared_remote, remote_transport
            )
        except RemoteExecutionPermissionDeniedError as exc:
            raise ExecutionPermissionDeniedError(selection.explanation) from exc

    connection_error: RuntimeConnectionUnavailableBeforeRequestError | None = None
    try:
        return await orchestrate_request_with_selected_candidate(
            request,
            selection.selected,
            remote_transport=remote_transport,
            execution_intervals=execution_intervals,
            local_interval_already_entered=execution_intervals is not None,
        )
    except RuntimeConnectionUnavailableBeforeRequestError as exc:
        if request.constraints.local_only or candidates.declared_remote is None:
            raise
        connection_error = exc

    try:
        return await execute_declared_remote_routing_candidate(
            request,
            candidates.declared_remote,
            remote_transport,
        )
    except RemoteExecutionPermissionDeniedError as exc:
        if connection_error is not None:
            raise connection_error from exc
        raise ExecutionPermissionDeniedError(selection.explanation) from exc


async def orchestrate_request_with_automatic_capability_fallback(
    request: RemoteTransportRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry,
    remote_transport: RemoteTransport,
) -> RemoteTransportResult:
    """Preserve the RFC-0028 proof-facing fallback entry point."""
    return await orchestrate_request_with_static_remote_fallback(
        request,
        node_registry,
        adapter_registry,
        remote_registry,
        remote_transport,
    )


async def orchestrate_request_with_declared_remote(
    request: ClusterRequest | SummarizeRequest,
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
