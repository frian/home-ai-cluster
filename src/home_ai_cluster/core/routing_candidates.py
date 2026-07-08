"""Opt-in routing candidate composition helpers."""

from dataclasses import dataclass

from home_ai_cluster.core.models import ClusterRequest
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    DeclaredRemoteRoutingCandidate,
    RemoteNodeDeclarationRegistry,
    declared_remote_routing_candidate_for_request,
)
from home_ai_cluster.core.router import (
    NoMatchingAdapterError,
    RoutingDecision,
    route_request,
)


@dataclass(frozen=True)
class LocalRoutingCandidate:
    """A local adapter-backed routing candidate."""

    decision: RoutingDecision


@dataclass(frozen=True)
class RoutingCandidates:
    """Opt-in routing candidates discovered without choosing between them."""

    local: LocalRoutingCandidate | None
    declared_remote: DeclaredRemoteRoutingCandidate | None


def routing_candidates_for_request(
    request: ClusterRequest,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry,
) -> RoutingCandidates:
    """Return local and declared remote candidates without selecting a policy."""
    try:
        local = LocalRoutingCandidate(
            route_request(request, node_registry, adapter_registry)
        )
    except NoMatchingAdapterError:
        local = None

    declared_remote = declared_remote_routing_candidate_for_request(
        request,
        remote_registry,
    )

    return RoutingCandidates(local=local, declared_remote=declared_remote)
