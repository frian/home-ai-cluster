"""Ordered static remote fallback orchestration."""

from home_ai_cluster.adapters.base import (
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.core.execution_intervals import ExecutionIntervalCardinality
from home_ai_cluster.core.executor import (
    execute_declared_remote_routing_candidate,
)
from home_ai_cluster.core.models import (
    RemoteTransportRequest,
    RemoteTransportResult,
)
from home_ai_cluster.core.orchestrator import (
    ExecutionPermissionDeniedError,
    NoSelectableRoutingCandidateError,
    orchestrate_request_with_selected_candidate,
)
from home_ai_cluster.core.ordinary_request_lifecycle import OrdinaryRequestLifecycle
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclarationRegistry
from home_ai_cluster.core.remote_transport import (
    RemoteExecutionPermissionDeniedError,
    RemoteTransport,
)
from home_ai_cluster.core.routing_candidates import (
    routing_candidates_for_request,
    select_automatic_capability_routing_candidate,
)


async def orchestrate_request_with_ordered_static_remote_fallback(
    request: RemoteTransportRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry,
    remote_transport: RemoteTransport,
    execution_intervals: ExecutionIntervalCardinality | None = None,
    lifecycle: OrdinaryRequestLifecycle | None = None,
) -> RemoteTransportResult:
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

    if lifecycle is not None:
        lifecycle.selected(selection.explanation)

    if selection.selected is None:
        raise NoSelectableRoutingCandidateError(selection.explanation)

    last_connection_error: RuntimeConnectionUnavailableBeforeRequestError | None = None
    remote_permission_denied = False

    if selection.selected.local is not None:
        local_permitted = (
            execution_intervals is None or await execution_intervals.try_enter()
        )
        if not local_permitted:
            if lifecycle is not None:
                lifecycle.local_permission(
                    False, selection.selected.local.decision.node.id
                )
            if request.constraints.local_only or not candidates.declared_remotes:
                raise ExecutionPermissionDeniedError(selection.explanation)
            if lifecycle is not None:
                lifecycle.continued(
                    selection.selected.local.decision.node.id,
                    "local-execution-permission-denied",
                )
        else:
            if lifecycle is not None:
                lifecycle.local_permission(
                    True, selection.selected.local.decision.node.id
                )
                lifecycle.local_adapter_invoked(
                    selection.selected.local.decision.node.id
                )
            try:
                result = await orchestrate_request_with_selected_candidate(
                    request,
                    selection.selected,
                    remote_transport=remote_transport,
                    execution_intervals=execution_intervals,
                    local_interval_already_entered=execution_intervals is not None,
                )
                if lifecycle is not None:
                    lifecycle.succeeded(result.node_id)
                return result
            except RuntimeConnectionUnavailableBeforeRequestError as exc:
                last_connection_error = exc
                if request.constraints.local_only:
                    raise
                if lifecycle is not None and candidates.declared_remotes:
                    lifecycle.continued(
                        selection.selected.local.decision.node.id,
                        "local-runtime-connection-unavailable-before-request",
                    )

    for index, candidate in enumerate(candidates.declared_remotes):
        has_next_remote = index + 1 < len(candidates.declared_remotes)
        if lifecycle is not None:
            lifecycle.remote_transport_invoked(candidate.node.id)
        try:
            result = await execute_declared_remote_routing_candidate(
                request,
                candidate,
                remote_transport,
            )
            if lifecycle is not None:
                lifecycle.succeeded(result.node_id)
            return result
        except RuntimeConnectionUnavailableBeforeRequestError as exc:
            last_connection_error = exc
            if lifecycle is not None and has_next_remote:
                lifecycle.continued(
                    candidate.node.id,
                    "remote-runtime-connection-unavailable-before-request",
                )
        except RemoteExecutionPermissionDeniedError:
            remote_permission_denied = True
            if lifecycle is not None:
                lifecycle.remote_refused(candidate.node.id)
            if lifecycle is not None and has_next_remote:
                lifecycle.continued(
                    candidate.node.id, "remote-execution-permission-refused"
                )

    if last_connection_error is not None:
        raise last_connection_error

    if remote_permission_denied:
        raise ExecutionPermissionDeniedError(selection.explanation)

    raise NoSelectableRoutingCandidateError(selection.explanation)
