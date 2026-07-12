"""Minimal core orchestration for static local requests."""

import httpx

from home_ai_cluster.core.executor import (
    execute_declared_remote_routing_candidate,
    execute_declared_routing_decision,
    execute_local_routing_decision,
    execute_routing_decision,
)
from home_ai_cluster.core.models import ClusterRequest, ClusterResult
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclarationRegistry
from home_ai_cluster.core.remote_transport import HttpRemoteTransport, RemoteTransport
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


async def orchestrate_request(
    request: ClusterRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
) -> ClusterResult:
    """Route a request to an adapter and return its normalized result."""
    decision = route_request(request, node_registry, adapter_registry)

    return await execute_routing_decision(request, decision)


async def orchestrate_request_with_selected_candidate(
    request: ClusterRequest,
    selected: SelectedRoutingCandidate,
    *,
    remote_transport: RemoteTransport | None = None,
) -> ClusterResult:
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
        return await execute_local_routing_decision(
            request,
            selected.local.decision,
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


async def orchestrate_request_with_automatic_capability_selection(
    request: ClusterRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry,
    remote_transport: RemoteTransport,
) -> ClusterResult:
    """Compose explicit candidate discovery, automatic selection, and execution."""
    candidates = routing_candidates_for_request(
        request,
        node_registry,
        adapter_registry,
        remote_registry,
    )
    selection = select_automatic_capability_routing_candidate(request, candidates)

    if selection.selected is None:
        raise NoSelectableRoutingCandidateError(selection.explanation)

    return await orchestrate_request_with_selected_candidate(
        request,
        selection.selected,
        remote_transport=remote_transport,
    )


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
