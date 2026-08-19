"""Opt-in routing candidate composition helpers."""

from dataclasses import dataclass
from enum import StrEnum

from home_ai_cluster.core.models import (
    RoutableRequest,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    DeclaredRemoteRoutingCandidate,
    RemoteNodeDeclarationRegistry,
    declared_remote_routing_candidates_for_request,
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
    declared_remotes: tuple[DeclaredRemoteRoutingCandidate, ...] = ()

    def __post_init__(self) -> None:
        if self.declared_remotes:
            object.__setattr__(self, "declared_remote", self.declared_remotes[0])
        elif self.declared_remote is not None:
            object.__setattr__(self, "declared_remotes", (self.declared_remote,))


class RoutingCandidateSelectionMode(StrEnum):
    """Selection ownership or explicit caller intent for opt-in candidates."""

    LOCAL_ONLY = "local-only"
    DECLARED_REMOTE_ONLY = "declared-remote-only"
    PREFER_LOCAL = "prefer-local"
    PREFER_DECLARED_REMOTE = "prefer-declared-remote"
    AUTOMATIC_CAPABILITY = "automatic-capability"


@dataclass(frozen=True)
class SelectedRoutingCandidate:
    """One selected routing candidate from an opt-in candidate collection."""

    local: LocalRoutingCandidate | None
    declared_remote: DeclaredRemoteRoutingCandidate | None
    mode: RoutingCandidateSelectionMode


class AutomaticCapabilitySelectionOutcomeRule(StrEnum):
    """Deterministic outcome rules for automatic capability selection."""

    LOCAL_ONLY = "local-only"
    LOCAL_PRECEDENCE = "local-precedence"
    DECLARED_REMOTE_ONLY = "declared-remote-only"
    NO_SELECTABLE_CANDIDATE = "no-selectable-candidate"


class NoSelectableCandidateReason(StrEnum):
    """Reasons why automatic capability selection could not choose a candidate."""

    NO_MATCHING_CANDIDATE = "no-matching-candidate"
    LOCAL_ONLY_EXCLUDED_DECLARED_REMOTE = "local-only-excluded-declared-remote"


@dataclass(frozen=True)
class AutomaticCapabilitySelectionExplanation:
    """Internal facts describing one automatic capability-selection outcome."""

    requested_capability_name: str
    local_matched: bool
    declared_remote_matched: bool
    local_selectable: bool
    declared_remote_selectable: bool
    local_only_excluded_declared_remote: bool
    selected_node_id: str | None
    outcome_rule: AutomaticCapabilitySelectionOutcomeRule
    no_selectable_candidate_reason: NoSelectableCandidateReason | None


@dataclass(frozen=True)
class AutomaticCapabilitySelection:
    """A cluster-owned automatic selection and its internal explanation facts."""

    selected: SelectedRoutingCandidate | None
    explanation: AutomaticCapabilitySelectionExplanation


def routing_candidates_for_request(
    request: RoutableRequest,
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

    declared_remotes = tuple(
        declared_remote_routing_candidates_for_request(request, remote_registry)
    )
    declared_remote = declared_remotes[0] if declared_remotes else None

    return RoutingCandidates(
        local=local,
        declared_remote=declared_remote,
        declared_remotes=declared_remotes,
    )


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


def select_automatic_capability_routing_candidate(
    request: RoutableRequest,
    candidates: RoutingCandidates,
) -> AutomaticCapabilitySelection:
    """Apply the cluster-owned automatic capability-selection policy.

    This pure policy is distinct from caller-directed selection modes.  It gives
    a selectable local candidate fixed precedence and allows a declared remote
    candidate only when the request does not require local-only execution.
    """
    local_matched = candidates.local is not None
    declared_remote_matched = candidates.declared_remote is not None
    local_selectable = local_matched
    local_only_excluded_declared_remote = (
        declared_remote_matched and request.constraints.local_only
    )
    declared_remote_selectable = (
        declared_remote_matched and not request.constraints.local_only
    )

    if local_selectable:
        outcome_rule = (
            AutomaticCapabilitySelectionOutcomeRule.LOCAL_PRECEDENCE
            if declared_remote_selectable
            else AutomaticCapabilitySelectionOutcomeRule.LOCAL_ONLY
        )
        selected = SelectedRoutingCandidate(
            local=candidates.local,
            declared_remote=None,
            mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
        )
        explanation = AutomaticCapabilitySelectionExplanation(
            requested_capability_name=request.capability.name,
            local_matched=local_matched,
            declared_remote_matched=declared_remote_matched,
            local_selectable=True,
            declared_remote_selectable=declared_remote_selectable,
            local_only_excluded_declared_remote=local_only_excluded_declared_remote,
            selected_node_id=candidates.local.decision.node.id,
            outcome_rule=outcome_rule,
            no_selectable_candidate_reason=None,
        )
        return AutomaticCapabilitySelection(selected=selected, explanation=explanation)

    if declared_remote_selectable:
        selected = SelectedRoutingCandidate(
            local=None,
            declared_remote=candidates.declared_remote,
            mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
        )
        explanation = AutomaticCapabilitySelectionExplanation(
            requested_capability_name=request.capability.name,
            local_matched=local_matched,
            declared_remote_matched=declared_remote_matched,
            local_selectable=False,
            declared_remote_selectable=True,
            local_only_excluded_declared_remote=False,
            selected_node_id=candidates.declared_remote.node.id,
            outcome_rule=AutomaticCapabilitySelectionOutcomeRule.DECLARED_REMOTE_ONLY,
            no_selectable_candidate_reason=None,
        )
        return AutomaticCapabilitySelection(selected=selected, explanation=explanation)

    reason = (
        NoSelectableCandidateReason.LOCAL_ONLY_EXCLUDED_DECLARED_REMOTE
        if local_only_excluded_declared_remote
        else NoSelectableCandidateReason.NO_MATCHING_CANDIDATE
    )
    explanation = AutomaticCapabilitySelectionExplanation(
        requested_capability_name=request.capability.name,
        local_matched=local_matched,
        declared_remote_matched=declared_remote_matched,
        local_selectable=False,
        declared_remote_selectable=False,
        local_only_excluded_declared_remote=local_only_excluded_declared_remote,
        selected_node_id=None,
        outcome_rule=AutomaticCapabilitySelectionOutcomeRule.NO_SELECTABLE_CANDIDATE,
        no_selectable_candidate_reason=reason,
    )
    return AutomaticCapabilitySelection(selected=None, explanation=explanation)
