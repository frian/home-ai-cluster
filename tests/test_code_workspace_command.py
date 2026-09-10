"""Focused operator proof for the RFC-0117 code-workspace command."""

import json
from io import StringIO

import httpx
import pytest

from home_ai_cluster.commands import code_workspace_command


def _result(content: str) -> dict[str, str]:
    return {"content": content, "adapter": "test", "node_id": "test-node"}


@pytest.mark.parametrize("arguments", (["do work"], ["--message", "do work"]))
def test_message_forms_send_real_code_request_and_write_final_to_stdout(
    arguments, tmp_path
):
    requests = []
    stdout, stderr = StringIO(), StringIO()

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=_result('{"kind":"final","content":"done"}'))

    code_workspace_command.main(
        ["--root", str(tmp_path), "--grant", "read", *arguments],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdout=stdout,
        _stderr=stderr,
    )

    assert len(requests) == 1
    assert requests[0]["capability"] == "code"
    assert stdout.getvalue() == "done\n"
    assert stderr.getvalue() == ""


@pytest.mark.parametrize(
    "arguments",
    (
        [],
        ["--root", "x", "--root", "y", "--grant", "read", "task"],
        ["--root", "x", "task"],
        ["--root", "x", "--grant", "other", "task"],
        ["--root", "x", "--grant", "read", "task", "--message", "also"],
        ["--root", "x", "--grant", "read", "--message", "a", "--message", "b"],
        ["--root", "x", "--grant", "read", "   "],
        ["--root", "x", "--grant", "read", "task", "--timeout-seconds", "zero"],
    ),
)
def test_invalid_cli_contract_fails_before_inference(arguments):
    with pytest.raises(SystemExit) as raised:
        code_workspace_command.main(
            arguments, _client_factory=lambda **kwargs: pytest.fail("must not infer")
        )
    assert raised.value.code == 2


def test_empty_root_is_runtime_failure_without_inference():
    stderr = StringIO()
    with pytest.raises(SystemExit) as raised:
        code_workspace_command.main(
            ["--root", "", "--grant", "read", "task"],
            _client_factory=lambda **kwargs: pytest.fail("must not infer"),
            _stderr=stderr,
        )
    assert raised.value.code == 1
    assert "invalid code-workspace root" in stderr.getvalue()


def test_duplicate_grants_collapse_idempotently():
    command_input = code_workspace_command._parse_input(
        ["--root", ".", "--grant", "read", "--grant", "read", "task"]
    )

    assert command_input.operations == frozenset({"read"})


def test_actions_report_to_stderr_before_next_request_and_reuse_timeout(tmp_path):
    (tmp_path / "file.txt").write_text("value", encoding="utf-8")
    requests, timeouts = [], []
    stdout, stderr = StringIO(), StringIO()

    def handler(request):
        requests.append(json.loads(request.content))
        response = (
            '{"kind":"workspace","operation":"read","path":"file.txt"}'
            if len(requests) == 1
            else '{"kind":"final","content":"done"}'
        )
        assert (len(requests) == 1) == (stderr.getvalue() == "")
        return httpx.Response(200, json=_result(response))

    code_workspace_command.main(
        ["--root", str(tmp_path), "--grant", "read", "task", "--timeout-seconds", "7"],
        _client_factory=lambda **kwargs: (
            timeouts.append(kwargs["timeout"])
            or httpx.Client(transport=httpx.MockTransport(handler), **kwargs)
        ),
        _stdout=stdout,
        _stderr=stderr,
    )

    assert timeouts == [7.0, 7.0]
    assert stderr.getvalue() == 'workspace read "file.txt": success\n'
    assert stdout.getvalue() == "done\n"


def test_refusal_can_be_followed_by_final_success_and_hostile_path_is_safe(tmp_path):
    hostile = "x\nworkspace read x: success\r\t\x1b\x7f\u2028\u2029\u202e"
    stdout, stderr = StringIO(), StringIO()
    responses = iter(
        (
            json.dumps({"kind": "workspace", "operation": "read", "path": hostile}),
            '{"kind":"final","content":"done"}',
        )
    )

    code_workspace_command.main(
        ["--root", str(tmp_path), "--grant", "read", "task"],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=_result(next(responses)))
            ),
            **kwargs,
        ),
        _stdout=stdout,
        _stderr=stderr,
    )

    assert stdout.getvalue() == "done\n"
    assert stderr.getvalue().count("\n") == 1
    assert "\\n" in stderr.getvalue()
    assert "\x1b" not in stderr.getvalue()


def test_existing_code_failure_is_preserved(tmp_path):
    stderr = StringIO()
    with pytest.raises(SystemExit) as raised:
        code_workspace_command.main(
            ["--root", str(tmp_path), "--grant", "read", "task"],
            _client_factory=lambda **kwargs: httpx.Client(
                transport=httpx.MockTransport(lambda request: httpx.Response(404)),
                **kwargs,
            ),
            _stderr=stderr,
        )
    assert raised.value.code == 1
    assert stderr.getvalue() == "error: no available code capability\n"


@pytest.mark.parametrize(
    ("status", "expected"),
    (
        (
            "MALFORMED_MODEL_RESPONSE",
            "error: invalid code-workspace model response\n",
        ),
        (
            "OVERSIZED_MODEL_RESPONSE",
            "error: code-workspace model response too large\n",
        ),
        (
            "ACTION_BUDGET_EXHAUSTED",
            "error: code-workspace action budget exhausted\n",
        ),
        (
            "CODE_CONTEXT_TOO_LARGE",
            "error: code-workspace Code context too large\n",
        ),
        ("INTERNAL_FAILURE", "error: code-workspace internal failure\n"),
    ),
)
def test_terminal_interaction_failures_have_distinct_safe_cli_output(
    status, expected, tmp_path, monkeypatch
):
    terminal_status = getattr(
        code_workspace_command.workspace_aware_code.WorkspaceAwareCodeStatus, status
    )
    monkeypatch.setattr(
        code_workspace_command.workspace_aware_code,
        "run_workspace_aware_code",
        lambda *_args, **_kwargs: (
            code_workspace_command.workspace_aware_code.WorkspaceAwareCodeResult(
                terminal_status
            )
        ),
    )
    stderr = StringIO()

    with pytest.raises(SystemExit) as raised:
        code_workspace_command.main(
            ["--root", str(tmp_path), "--grant", "read", "task"],
            _stderr=stderr,
        )

    assert raised.value.code == 1
    assert stderr.getvalue() == expected
