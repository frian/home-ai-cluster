import json

import pytest

from home_ai_cluster.adapters.base import RuntimeAdapter
from home_ai_cluster.commands.routing_explanation import (
    LOCAL_ADAPTER_NAME,
    create_request,
    discover_and_select,
    evaluate_explanation,
    main,
    project_explanation,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    RuntimeResult,
)
from home_ai_cluster.core.routing_candidates import AutomaticCapabilitySelection


class RecordingAdapter(RuntimeAdapter):
    """Test-only adapter spy proving explanation never executes local runtime work."""

    def __init__(self, capability: Capability) -> None:
        self._capability = capability
        self.chat_calls = 0

    @property
    def name(self) -> str:
        return LOCAL_ADAPTER_NAME

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [self._capability]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.chat_calls += 1
        raise AssertionError("routing explanation must not execute an adapter")


@pytest.mark.parametrize(
    (
        "description",
        "local_only",
        "include_local",
        "include_declared_remote",
        "expected",
    ),
    [
        (
            "local candidate only",
            False,
            True,
            False,
            {
                "requested_capability": "chat",
                "matched_candidate_families": ["local"],
                "selectable_candidate_families": ["local"],
                "excluded_candidate_families": [],
                "selected_candidate_family": "local",
                "selected_node_id": "local",
                "outcome_rule": "local-only",
                "failure_reason": None,
            },
        ),
        (
            "declared remote only",
            False,
            False,
            True,
            {
                "requested_capability": "chat",
                "matched_candidate_families": ["declared-remote"],
                "selectable_candidate_families": ["declared-remote"],
                "excluded_candidate_families": [],
                "selected_candidate_family": "declared-remote",
                "selected_node_id": "declared-remote",
                "outcome_rule": "declared-remote-only",
                "failure_reason": None,
            },
        ),
        (
            "both selectable",
            False,
            True,
            True,
            {
                "requested_capability": "chat",
                "matched_candidate_families": ["local", "declared-remote"],
                "selectable_candidate_families": ["local", "declared-remote"],
                "excluded_candidate_families": [],
                "selected_candidate_family": "local",
                "selected_node_id": "local",
                "outcome_rule": "local-precedence",
                "failure_reason": None,
            },
        ),
        (
            # RFC-0027's two no-selection requirements are one concrete
            # RFC-0025 outcome: local_only excludes the sole declared remote.
            "matching declared remote exists but none is selectable because "
            "local_only excludes it",
            True,
            False,
            True,
            {
                "requested_capability": "chat",
                "matched_candidate_families": ["declared-remote"],
                "selectable_candidate_families": [],
                "excluded_candidate_families": ["declared-remote"],
                "selected_candidate_family": None,
                "selected_node_id": None,
                "outcome_rule": "no-selectable-candidate",
                "failure_reason": "local-only-excluded-declared-remote",
            },
        ),
        (
            "no matching candidates",
            False,
            False,
            False,
            {
                "requested_capability": "chat",
                "matched_candidate_families": [],
                "selectable_candidate_families": [],
                "excluded_candidate_families": [],
                "selected_candidate_family": None,
                "selected_node_id": None,
                "outcome_rule": "no-selectable-candidate",
                "failure_reason": "no-matching-candidate",
            },
        ),
    ],
)
def test_evaluate_explanation_returns_the_complete_rfc_0027_contract(
    description: str,
    local_only: bool,
    include_local: bool,
    include_declared_remote: bool,
    expected: dict[str, object],
) -> None:
    assert description
    assert (
        evaluate_explanation(
            "chat",
            local_only=local_only,
            include_local=include_local,
            include_declared_remote=include_declared_remote,
        )
        == expected
    )


def test_main_writes_exactly_one_json_object_and_newline(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["--capability", "chat", "--declared-remote"])

    captured = capsys.readouterr()
    expected = evaluate_explanation(
        "chat",
        local_only=False,
        include_local=False,
        include_declared_remote=True,
    )
    assert captured.out == json.dumps(expected) + "\n"
    assert captured.err == ""
    assert json.loads(captured.out) == expected


def test_valid_no_selection_exits_successfully(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["--capability", "chat", "--declared-remote", "--local-only"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out)["failure_reason"] == (
        "local-only-excluded-declared-remote"
    )


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--capability", "   "],
        ["--capability", "chat", "--message", "Hello"],
    ],
)
def test_invalid_invocation_uses_stderr_and_nonzero_exit(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(argv)

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == ""
    assert captured.err


def test_discovery_and_selection_stop_before_any_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.core import executor, orchestrator, remote_transport

    request = create_request("chat", local_only=False)
    adapter = RecordingAdapter(request.capability)
    execution_calls: list[str] = []
    transport_creations: list[object] = []

    async def record_selected_execution(*args: object, **kwargs: object) -> None:
        execution_calls.append("selected")

    async def record_local_execution(*args: object, **kwargs: object) -> None:
        execution_calls.append("local")

    async def record_remote_execution(*args: object, **kwargs: object) -> None:
        execution_calls.append("remote")

    class RecordingHttpRemoteTransport:
        def __init__(self, *args: object, **kwargs: object) -> None:
            transport_creations.append((args, kwargs))

    monkeypatch.setattr(
        orchestrator,
        "orchestrate_request_with_selected_candidate",
        record_selected_execution,
    )
    monkeypatch.setattr(
        executor, "execute_local_routing_decision", record_local_execution
    )
    monkeypatch.setattr(
        executor,
        "execute_declared_remote_routing_candidate",
        record_remote_execution,
    )
    monkeypatch.setattr(
        remote_transport,
        "HttpRemoteTransport",
        RecordingHttpRemoteTransport,
    )

    selection = discover_and_select(
        request,
        include_local=True,
        include_declared_remote=True,
        local_adapter=adapter,
    )

    assert isinstance(selection, AutomaticCapabilitySelection)
    assert selection.selected is not None
    assert selection.selected.local is not None
    assert project_explanation(selection)["selected_node_id"] == "local"
    assert adapter.chat_calls == 0
    assert execution_calls == []
    assert transport_creations == []
