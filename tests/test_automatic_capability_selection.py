import inspect

import pytest

from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    NodeDescription,
    NodeHealth,
    RequestConstraints,
)
from home_ai_cluster.core.remote_node import (
    DECLARED_REMOTE_ROUTING_REASON,
    DeclaredRemoteRoutingCandidate,
    RemoteNodeDeclaration,
)
from home_ai_cluster.core.router import RoutingDecision
from home_ai_cluster.core.routing_candidates import (
    AutomaticCapabilitySelectionOutcomeRule,
    LocalRoutingCandidate,
    NoSelectableCandidateReason,
    RoutingCandidates,
    RoutingCandidateSelectionMode,
    select_automatic_capability_routing_candidate,
    select_routing_candidate,
)


class RecordingAdapter:
    def __init__(self) -> None:
        self.calls = 0

    async def chat(self, request: ClusterRequest) -> None:
        self.calls += 1


def make_request(
    *,
    local_only: bool = True,
    prefer_fast_response: bool = False,
    min_context_size: int | None = None,
) -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
        constraints=RequestConstraints(
            local_only=local_only,
            prefer_fast_response=prefer_fast_response,
            min_context_size=min_context_size,
        ),
    )


def make_node(node_id: str) -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["adapter"],
    )


def make_local_candidate(
    adapter: RecordingAdapter | None = None,
) -> LocalRoutingCandidate:
    return LocalRoutingCandidate(
        RoutingDecision(
            node=make_node("local"),
            adapter=adapter or RecordingAdapter(),
            capability=Capability(name="chat"),
            reason="Local candidate for test.",
        )
    )


def make_declared_remote_candidate() -> DeclaredRemoteRoutingCandidate:
    declaration = RemoteNodeDeclaration(
        node=make_node("remote"),
        transport_address="http://remote.example:8000",
    )
    return DeclaredRemoteRoutingCandidate(
        node=declaration.node,
        declaration=declaration,
        capability=Capability(name="chat"),
        reason=DECLARED_REMOTE_ROUTING_REASON,
    )


@pytest.mark.parametrize(
    (
        "local_only",
        "has_local",
        "has_remote",
        "expected_family",
        "expected_outcome_rule",
        "expected_remote_excluded",
        "expected_failure_reason",
    ),
    [
        (
            True,
            True,
            True,
            "local",
            AutomaticCapabilitySelectionOutcomeRule.LOCAL_ONLY,
            True,
            None,
        ),
        (
            True,
            True,
            False,
            "local",
            AutomaticCapabilitySelectionOutcomeRule.LOCAL_ONLY,
            False,
            None,
        ),
        (
            True,
            False,
            True,
            None,
            AutomaticCapabilitySelectionOutcomeRule.NO_SELECTABLE_CANDIDATE,
            True,
            NoSelectableCandidateReason.LOCAL_ONLY_EXCLUDED_DECLARED_REMOTE,
        ),
        (
            True,
            False,
            False,
            None,
            AutomaticCapabilitySelectionOutcomeRule.NO_SELECTABLE_CANDIDATE,
            False,
            NoSelectableCandidateReason.NO_MATCHING_CANDIDATE,
        ),
        (
            False,
            True,
            True,
            "local",
            AutomaticCapabilitySelectionOutcomeRule.LOCAL_PRECEDENCE,
            False,
            None,
        ),
        (
            False,
            True,
            False,
            "local",
            AutomaticCapabilitySelectionOutcomeRule.LOCAL_ONLY,
            False,
            None,
        ),
        (
            False,
            False,
            True,
            "declared_remote",
            AutomaticCapabilitySelectionOutcomeRule.DECLARED_REMOTE_ONLY,
            False,
            None,
        ),
        (
            False,
            False,
            False,
            None,
            AutomaticCapabilitySelectionOutcomeRule.NO_SELECTABLE_CANDIDATE,
            False,
            NoSelectableCandidateReason.NO_MATCHING_CANDIDATE,
        ),
    ],
)
def test_automatic_policy_uses_the_normative_selectability_matrix(
    local_only: bool,
    has_local: bool,
    has_remote: bool,
    expected_family: str | None,
    expected_outcome_rule: AutomaticCapabilitySelectionOutcomeRule,
    expected_remote_excluded: bool,
    expected_failure_reason: NoSelectableCandidateReason | None,
) -> None:
    local = make_local_candidate() if has_local else None
    declared_remote = make_declared_remote_candidate() if has_remote else None

    outcome = select_automatic_capability_routing_candidate(
        make_request(local_only=local_only),
        RoutingCandidates(local=local, declared_remote=declared_remote),
    )

    if expected_family is None:
        assert outcome.selected is None
        assert outcome.explanation.selected_node_id is None
    elif expected_family == "local":
        assert outcome.selected is not None
        assert outcome.selected.local is local
        assert outcome.selected.declared_remote is None
        assert outcome.explanation.selected_node_id == "local"
    else:
        assert outcome.selected is not None
        assert outcome.selected.local is None
        assert outcome.selected.declared_remote is declared_remote
        assert outcome.explanation.selected_node_id == "remote"

    assert outcome.explanation.outcome_rule == expected_outcome_rule
    assert (
        outcome.explanation.local_only_excluded_declared_remote
        is expected_remote_excluded
    )
    assert outcome.explanation.no_selectable_candidate_reason == expected_failure_reason


def test_automatic_policy_is_distinct_from_caller_directed_prefer_local() -> None:
    candidates = RoutingCandidates(
        local=make_local_candidate(),
        declared_remote=make_declared_remote_candidate(),
    )

    automatic = select_automatic_capability_routing_candidate(
        make_request(local_only=False), candidates
    )
    caller_directed = select_routing_candidate(
        candidates, RoutingCandidateSelectionMode.PREFER_LOCAL
    )

    assert automatic.selected is not None
    assert automatic.selected.mode == RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY
    assert caller_directed is not None
    assert caller_directed.mode == RoutingCandidateSelectionMode.PREFER_LOCAL


def test_local_only_excludes_the_only_declared_remote_candidate() -> None:
    outcome = select_automatic_capability_routing_candidate(
        make_request(local_only=True),
        RoutingCandidates(local=None, declared_remote=make_declared_remote_candidate()),
    )

    assert outcome.selected is None
    assert outcome.explanation.declared_remote_matched is True
    assert outcome.explanation.declared_remote_selectable is False
    assert outcome.explanation.local_only_excluded_declared_remote is True
    assert outcome.explanation.selected_node_id is None
    assert (
        outcome.explanation.no_selectable_candidate_reason
        == NoSelectableCandidateReason.LOCAL_ONLY_EXCLUDED_DECLARED_REMOTE
    )


def test_both_selectable_candidates_use_fixed_local_precedence() -> None:
    outcome = select_automatic_capability_routing_candidate(
        make_request(local_only=False),
        RoutingCandidates(
            local=make_local_candidate(),
            declared_remote=make_declared_remote_candidate(),
        ),
    )

    assert outcome.selected is not None
    assert outcome.selected.local is not None
    assert (
        outcome.explanation.outcome_rule
        == AutomaticCapabilitySelectionOutcomeRule.LOCAL_PRECEDENCE
    )


def test_no_candidates_has_a_deterministic_explanation() -> None:
    outcome = select_automatic_capability_routing_candidate(
        make_request(), RoutingCandidates(local=None, declared_remote=None)
    )

    assert outcome.selected is None
    assert outcome.explanation.requested_capability_name == "chat"
    assert outcome.explanation.local_matched is False
    assert outcome.explanation.declared_remote_matched is False
    assert outcome.explanation.local_selectable is False
    assert outcome.explanation.declared_remote_selectable is False
    assert (
        outcome.explanation.outcome_rule
        == AutomaticCapabilitySelectionOutcomeRule.NO_SELECTABLE_CANDIDATE
    )
    assert (
        outcome.explanation.no_selectable_candidate_reason
        == NoSelectableCandidateReason.NO_MATCHING_CANDIDATE
    )


def test_non_selectability_constraints_do_not_alter_the_result() -> None:
    candidates = RoutingCandidates(
        local=None, declared_remote=make_declared_remote_candidate()
    )

    baseline = select_automatic_capability_routing_candidate(
        make_request(local_only=False), candidates
    )
    constrained = select_automatic_capability_routing_candidate(
        make_request(
            local_only=False,
            prefer_fast_response=True,
            min_context_size=32768,
        ),
        candidates,
    )

    assert constrained == baseline


def test_automatic_policy_does_not_call_a_local_adapter() -> None:
    adapter = RecordingAdapter()

    select_automatic_capability_routing_candidate(
        make_request(local_only=False),
        RoutingCandidates(
            local=make_local_candidate(adapter),
            declared_remote=make_declared_remote_candidate(),
        ),
    )

    assert adapter.calls == 0


def test_automatic_policy_has_no_execution_dependencies() -> None:
    signature = inspect.signature(select_automatic_capability_routing_candidate)

    assert list(signature.parameters) == ["request", "candidates"]
