"""Opt-in routing candidate composition helpers."""

from dataclasses import dataclass
from enum import StrEnum

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


class RoutingCandidateSelectionMode(StrEnum):
    """Explicit caller intent for opt-in routing candidate selection."""

    LOCAL_ONLY = "local-only"
    DECLARED_REMOTE_ONLY = "declared-remote-only"
    PREFER_LOCAL = "prefer-local"
    PREFER_DECLARED_REMOTE = "prefer-declared-remote"


@dataclass(frozen=True)
class SelectedRoutingCandidate:
    """One selected routing candidate from an opt-in candidate collection."""

    local: LocalRoutingCandidate | None
    declared_remote: DeclaredRemoteRoutingCandidate | None
    mode: RoutingCandidateSelectionMode


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


def select_routing_candidate(
    candidates: RoutingCandidates,
    mode: RoutingCandidateSelectionMode,
) -> SelectedRoutingCandidate | None:
    """Select one already-discovered candidate according to caller intent."""
    if mode == RoutingCandidateSelectionMode.LOCAL_ONLY:
        if candidates.local is None:
            return None

        return SelectedRoutingCandidate(
            local=candidates.local,
            declared_remote=None,
            mode=mode,
        )

    if mode == RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY:
        if candidates.declared_remote is None:
            return None

        return SelectedRoutingCandidate(
            local=None,
            declared_remote=candidates.declared_remote,
            mode=mode,
        )

    if mode == RoutingCandidateSelectionMode.PREFER_LOCAL:
        if candidates.local is not None:
            return SelectedRoutingCandidate(
                local=candidates.local,
                declared_remote=None,
                mode=mode,
            )

        if candidates.declared_remote is not None:
            return SelectedRoutingCandidate(
                local=None,
                declared_remote=candidates.declared_remote,
                mode=mode,
            )

        return None

    if mode == RoutingCandidateSelectionMode.PREFER_DECLARED_REMOTE:
        if candidates.declared_remote is not None:
            return SelectedRoutingCandidate(
                local=None,
                declared_remote=candidates.declared_remote,
                mode=mode,
            )

        if candidates.local is not None:
            return SelectedRoutingCandidate(
                local=candidates.local,
                declared_remote=None,
                mode=mode,
            )

        return None

    return None
