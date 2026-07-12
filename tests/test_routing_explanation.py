import json

import pytest

from home_ai_cluster.routing_explanation import (
    ExplanationOnlyAdapter,
    create_request,
    discover_and_select,
    evaluate_explanation,
    main,
)


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
            "declared remote excluded by local-only",
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
        (
            "matching candidate but none selectable",
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


def test_discovery_and_selection_do_not_execute_the_local_adapter() -> None:
    request = create_request("chat", local_only=False)
    adapter = ExplanationOnlyAdapter(request.capability)

    selection = discover_and_select(
        request,
        include_local=True,
        include_declared_remote=True,
        local_adapter=adapter,
    )

    assert selection.selected is not None
    assert selection.selected.local is not None
    assert adapter.chat_calls == 0
