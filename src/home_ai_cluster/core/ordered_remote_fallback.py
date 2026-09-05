"""Ordered static remote fallback orchestration."""

from home_ai_cluster.adapters.base import (
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.core.execution_intervals import ExecutionIntervalCardinality
from home_ai_cluster.core.executor import (
    execute_declared_remote_routing_candidate,
)
from home_ai_cluster.core.models import (
    RoutableRequest,
    RoutableResult,
)
from home_ai_cluster.core.orchestrator import (
    NoSelectableRoutingCandidateError,
    orchestrate_request_with_selected_candidate,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclarationRegistry
from home_ai_cluster.core.remote_transport import RemoteTransport
from home_ai_cluster.core.routing_candidates import (
    routing_candidates_for_request,
    select_automatic_capability_routing_candidate,
)


async def orchestrate_request_with_ordered_static_remote_fallback(
    request: RoutableRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry,
    remote_transport: RemoteTransport,
    execution_intervals: ExecutionIntervalCardinality | None = None,
) -> RoutableResult:
    """Try local once, then eligible declared remotes once in declaration order.

    Per RFC-0028, only an affirmative pre-transmission failure may advance
    fallback; ambiguous or later failures stay visible to avoid retransmitting
    a request that may already have executed.
    """
    candidates = routing_candidates_for_request(
        request,
        node_registry,
        adapter_registry,
        remote_registry,
    )
    selection = select_automatic_capability_routing_candidate(request, candidates)

    if selection.selected is None:
        raise NoSelectableRoutingCandidateError(selection.explanation)

    last_connection_error: RuntimeConnectionUnavailableBeforeRequestError | None = None

    if selection.selected.local is not None:
        try:
            return await orchestrate_request_with_selected_candidate(
                request,
                selection.selected,
                remote_transport=remote_transport,
                execution_intervals=execution_intervals,
            )
        except RuntimeConnectionUnavailableBeforeRequestError as exc:
            last_connection_error = exc
            if request.constraints.local_only:
                raise

    for candidate in candidates.declared_remotes:
        try:
            return await execute_declared_remote_routing_candidate(
                request,
                candidate,
                remote_transport,
            )
        except RuntimeConnectionUnavailableBeforeRequestError as exc:
            last_connection_error = exc

    if last_connection_error is not None:
        raise last_connection_error

    raise NoSelectableRoutingCandidateError(selection.explanation)
