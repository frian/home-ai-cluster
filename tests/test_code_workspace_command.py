"""Focused operator proof for the RFC-0117 code-workspace command."""

import json
from io import StringIO

import httpx
import pytest

from home_ai_cluster.commands import code_workspace_command


class terminal(StringIO):
    def isatty(self) -> bool:
        return True


class non_terminal(StringIO):
    def isatty(self) -> bool:
        return False


class unreadable_terminal(non_terminal):
    def readline(self, size: int | None = -1) -> str:
        raise AssertionError("non-TTY code-workspace must not read stdin")


class unreadable_tty(terminal):
    def readline(self, size: int | None = -1) -> str:
        raise AssertionError("invalid root must fail before reading stdin")


class interrupted_tty(terminal):
    def readline(self, size: int | None = -1) -> str:
        raise KeyboardInterrupt


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


def test_grant_help_explains_that_multiple_operations_require_repetition(capsys):
    with pytest.raises(SystemExit) as raised:
        code_workspace_command.main(["-h"])

    captured = capsys.readouterr()
    assert raised.value.code == 0
    assert captured.err == ""
    assert (
        "Grant one workspace operation. Repeat --grant for multiple operations."
        in " ".join(captured.out.split())
    )


def test_comma_separated_grant_is_rejected_before_inference():
    with pytest.raises(SystemExit) as raised:
        code_workspace_command.main(
            ["--root", ".", "--grant", "read,list", "task"],
            _client_factory=lambda **kwargs: pytest.fail("must not infer"),
        )

    assert raised.value.code == 2


def test_repeated_grants_are_accepted():
    command_input = code_workspace_command._parse_input(
        ["--root", ".", "--grant", "read", "--grant", "list", "task"]
    )

    assert command_input.operations == frozenset({"read", "list"})


def test_naked_invocation_shows_authority_requirement_and_usage():
    stderr = StringIO()

    with pytest.raises(SystemExit) as raised:
        code_workspace_command.main([], _stderr=stderr)

    assert raised.value.code == 2
    assert stderr.getvalue().startswith("usage: home-ai-cluster code-workspace")
    assert "error: --root and at least one --grant are required\n" in stderr.getvalue()


@pytest.mark.parametrize(
    ("stdin", "stdout"),
    [(unreadable_terminal(), terminal()), (terminal(), non_terminal())],
)
def test_no_message_requires_both_tty_streams_before_input_or_inference(stdin, stdout):
    stderr = StringIO()
    with pytest.raises(SystemExit) as raised:
        code_workspace_command.main(
            ["--root", ".", "--grant", "read"],
            _client_factory=lambda **kwargs: pytest.fail("must not infer"),
            _stdin=stdin,
            _stdout=stdout,
            _stderr=stderr,
        )

    assert raised.value.code == 2
    assert stderr.getvalue() == "error: invalid request input\n"


def test_interactive_reuses_one_authority_and_retains_only_successful_conversation(
    tmp_path, monkeypatch
):
    target = tmp_path / "data.txt"
    target.write_text("value", encoding="utf-8")
    requests = []
    constructed = 0
    original = code_workspace_command.workspace_aware_code.WorkspaceAuthority

    def construct(*args, **kwargs):
        nonlocal constructed
        constructed += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        code_workspace_command.workspace_aware_code, "WorkspaceAuthority", construct
    )
    responses = iter(
        (
            '{"kind":"workspace","operation":"read","path":"data.txt"}',
            '{"kind":"final","content":"first result"}',
            '{"kind":"final","content":"second result"}',
        )
    )

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=_result(next(responses)))

    stdout, stderr = terminal(), StringIO()
    code_workspace_command.main(
        ["--root", str(tmp_path), "--grant", "read"],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdin=terminal("first instruction\nsecond instruction\n"),
        _stdout=stdout,
        _stderr=stderr,
    )

    assert constructed == 1
    assert requests[2]["messages"] == [
        {
            "role": "system",
            "content": code_workspace_command.workspace_aware_code._CONTRACT,
        },
        {"role": "user", "content": "first instruction"},
        {"role": "assistant", "content": "first result"},
        {
            "role": "user",
            "content": code_workspace_command.workspace_aware_code._HISTORY_REMINDER,
        },
        {"role": "user", "content": "second instruction"},
    ]
    assert "HAC workspace outcome:" not in str(requests[2])
    assert stderr.getvalue() == 'workspace read "data.txt": success\n'


def test_interactive_empty_final_is_not_retained_and_loop_continues(tmp_path):
    requests = []
    responses = iter(
        (
            '{"kind":"final","content":"saved"}',
            '{"kind":"final","content":""}',
            '{"kind":"final","content":"later"}',
        )
    )

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=_result(next(responses)))

    stderr = StringIO()
    code_workspace_command.main(
        ["--root", str(tmp_path), "--grant", "read"],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdin=terminal("first\nempty\nthird\n"),
        _stdout=terminal(),
        _stderr=stderr,
    )

    assert requests[2]["messages"][1:] == [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "saved"},
        {
            "role": "user",
            "content": code_workspace_command.workspace_aware_code._HISTORY_REMINDER,
        },
        {"role": "user", "content": "third"},
    ]
    assert stderr.getvalue() == "error: invalid cluster response\n"


def test_interactive_action_budget_starts_fresh_for_each_human_turn(tmp_path):
    target = tmp_path / "data.txt"
    target.write_text("value", encoding="utf-8")
    action = '{"kind":"workspace","operation":"read","path":"data.txt"}'
    responses = iter(
        [
            *([action] * 8),
            '{"kind":"final","content":"first"}',
            *([action] * 8),
            '{"kind":"final","content":"second"}',
        ]
    )
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=_result(next(responses)))

    stderr = StringIO()
    code_workspace_command.main(
        ["--root", str(tmp_path), "--grant", "read"],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdin=terminal("first turn\nsecond turn\n"),
        _stdout=terminal(),
        _stderr=stderr,
    )

    assert len(requests) == 18
    assert stderr.getvalue().count('workspace read "data.txt": success\n') == 16
    assert "action budget exhausted" not in stderr.getvalue()


def test_interactive_failed_turn_is_not_retained_after_success(tmp_path):
    requests = []
    responses = iter(
        (
            '{"kind":"final","content":"saved"}',
            "not JSON",
            '{"kind":"final","content":"later"}',
        )
    )

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=_result(next(responses)))

    stderr = StringIO()
    code_workspace_command.main(
        ["--root", str(tmp_path), "--grant", "read"],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdin=terminal("saved turn\nfailed turn\nlater turn\n"),
        _stdout=terminal(),
        _stderr=stderr,
    )

    assert requests[2]["messages"][1:] == [
        {"role": "user", "content": "saved turn"},
        {"role": "assistant", "content": "saved"},
        {
            "role": "user",
            "content": code_workspace_command.workspace_aware_code._HISTORY_REMINDER,
        },
        {"role": "user", "content": "later turn"},
    ]
    assert stderr.getvalue() == "error: invalid code-workspace model response\n"


def test_interactive_committed_create_survives_failed_turn_without_retention(tmp_path):
    requests = []
    responses = iter(
        (
            '{"kind":"final","content":"saved"}',
            '{"kind":"workspace","operation":"create","path":"created.txt"}',
            "not JSON",
            '{"kind":"final","content":"later"}',
        )
    )

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=_result(next(responses)))

    stderr = StringIO()
    code_workspace_command.main(
        ["--root", str(tmp_path), "--grant", "create"],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdin=terminal("saved turn\ncreate then fail\nlater turn\n"),
        _stdout=terminal(),
        _stderr=stderr,
    )

    assert (tmp_path / "created.txt").read_bytes() == b""
    assert requests[3]["messages"][1:] == [
        {"role": "user", "content": "saved turn"},
        {"role": "assistant", "content": "saved"},
        {
            "role": "user",
            "content": code_workspace_command.workspace_aware_code._HISTORY_REMINDER,
        },
        {"role": "user", "content": "later turn"},
    ]
    assert stderr.getvalue() == (
        'workspace create "created.txt": success\n'
        "error: invalid code-workspace model response\n"
    )


def test_interactive_over_limit_turn_is_not_sent_or_retained(tmp_path):
    requests = []
    responses = iter(
        (
            json.dumps({"kind": "final", "content": "x" * 64_000}),
            '{"kind":"final","content":"later"}',
        )
    )

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=_result(next(responses)))

    stderr = StringIO()
    code_workspace_command.main(
        ["--root", str(tmp_path), "--grant", "read"],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdin=terminal(f"saved\n{'y' * 1_000}\nlater\n"),
        _stdout=terminal(),
        _stderr=stderr,
    )

    assert len(requests) == 2
    assert requests[1]["messages"][1:] == [
        {"role": "user", "content": "saved"},
        {"role": "assistant", "content": "x" * 64_000},
        {
            "role": "user",
            "content": code_workspace_command.workspace_aware_code._HISTORY_REMINDER,
        },
        {"role": "user", "content": "later"},
    ]
    assert stderr.getvalue() == "error: code-workspace Code context too large\n"


def test_interactive_timeout_is_applied_to_each_code_inference(tmp_path):
    timeouts = []
    responses = iter(
        (
            '{"kind":"workspace","operation":"list","path":"."}',
            '{"kind":"final","content":"done"}',
        )
    )

    code_workspace_command.main(
        ["--root", str(tmp_path), "--grant", "list", "--timeout-seconds", "7"],
        _client_factory=lambda **kwargs: (
            timeouts.append(kwargs["timeout"])
            or httpx.Client(
                transport=httpx.MockTransport(
                    lambda request: httpx.Response(200, json=_result(next(responses)))
                ),
                **kwargs,
            )
        ),
        _stdin=terminal("inspect\n"),
        _stdout=terminal(),
        _stderr=StringIO(),
    )

    assert timeouts == [7.0, 7.0]


def test_interactive_eof_and_keyboard_interrupt_exit_without_inference(tmp_path):
    for stdin in (terminal(), interrupted_tty()):
        code_workspace_command.main(
            ["--root", str(tmp_path), "--grant", "read"],
            _client_factory=lambda **kwargs: pytest.fail("must not infer"),
            _stdin=stdin,
            _stdout=terminal(),
            _stderr=StringIO(),
        )


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


def test_interactive_invalid_root_fails_before_input_or_inference():
    stderr = StringIO()
    with pytest.raises(SystemExit) as raised:
        code_workspace_command.main(
            ["--root", "", "--grant", "read"],
            _client_factory=lambda **kwargs: pytest.fail("must not infer"),
            _stdin=unreadable_tty(),
            _stdout=terminal(),
            _stderr=stderr,
        )

    assert raised.value.code == 1
    assert stderr.getvalue() == "error: invalid code-workspace root\n"


def test_duplicate_grants_collapse_idempotently():
    command_input = code_workspace_command._parse_input(
        ["--root", ".", "--grant", "read", "--grant", "read", "task"]
    )

    assert command_input.operations == frozenset({"read"})


def test_create_grants_are_accepted_and_idempotent():
    command_input = code_workspace_command._parse_input(
        [
            "--root",
            ".",
            "--grant",
            "create",
            "--grant",
            "write",
            "--grant",
            "create",
            "task",
        ]
    )
    assert command_input.operations == frozenset({"create", "write"})


def test_create_activity_and_create_then_write_use_existing_cli_flow(tmp_path):
    stdout, stderr = StringIO(), StringIO()
    responses = iter(
        (
            '{"kind":"workspace","operation":"create","path":"new.txt"}',
            '{"kind":"workspace","operation":"write","path":"new.txt","content":"value"}',
            '{"kind":"final","content":"done"}',
        )
    )
    code_workspace_command.main(
        ["--root", str(tmp_path), "--grant", "create", "--grant", "write", "task"],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=_result(next(responses)))
            ),
            **kwargs,
        ),
        _stdout=stdout,
        _stderr=stderr,
    )
    assert (tmp_path / "new.txt").read_text(encoding="utf-8") == "value"
    assert stderr.getvalue() == (
        'workspace create "new.txt": success\nworkspace write "new.txt": success\n'
    )
    assert stdout.getvalue() == "done\n"


def test_create_only_interaction_leaves_an_empty_file(tmp_path):
    stdout, stderr = StringIO(), StringIO()
    responses = iter(
        (
            '{"kind":"workspace","operation":"create","path":"empty.txt"}',
            '{"kind":"final","content":"done"}',
        )
    )
    code_workspace_command.main(
        ["--root", str(tmp_path), "--grant", "create", "task"],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=_result(next(responses)))
            ),
            **kwargs,
        ),
        _stdout=stdout,
        _stderr=stderr,
    )
    assert (tmp_path / "empty.txt").read_bytes() == b""
    assert stderr.getvalue() == 'workspace create "empty.txt": success\n'
    assert stdout.getvalue() == "done\n"


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
