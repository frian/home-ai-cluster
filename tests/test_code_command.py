"""Tests for RFC-0088 bounded ephemeral interactive Code."""

import json
from io import StringIO

import httpx
import pytest

from home_ai_cluster.commands import code_command


class terminal(StringIO):
    def isatty(self) -> bool:
        return True


class non_terminal(StringIO):
    def isatty(self) -> bool:
        return False


class unreadable_terminal(non_terminal):
    def readline(self, size: int | None = -1) -> str:
        raise AssertionError("non-TTY Code must not read stdin")


class interrupted_terminal(terminal):
    def readline(self, size: int | None = -1) -> str:
        raise KeyboardInterrupt


def result(content: str) -> dict[str, str | None]:
    return {
        "content": content,
        "adapter": "test-adapter",
        "model": "test-model",
        "node_id": "test-node",
    }


@pytest.mark.parametrize(
    "argv", (["Write a function"], ["--message", "Write a function"])
)
def test_explicit_message_forms_remain_one_shot(argv: list[str]) -> None:
    requests: list[dict[str, object]] = []
    stdout = StringIO()
    stderr = StringIO()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=result("answer"))

    code_command.main(
        argv,
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdout=stdout,
        _stderr=stderr,
    )

    assert requests == [
        {
            "messages": [{"role": "user", "content": "Write a function"}],
            "capability": "code",
        }
    ]
    assert stdout.getvalue() == "answer\n"
    assert stderr.getvalue() == ""


@pytest.mark.parametrize(
    ("arguments", "expected_output"),
    [
        ([], "answer\n"),
        (
            ["--json"],
            '{"content":"answer","adapter":"test-adapter",'
            '"model":"test-model","node_id":"test-node"}\n',
        ),
        (
            ["--verbose"],
            "Response:\nanswer\n\nExecution:\n"
            "  Node: test-node\n  Adapter: test-adapter\n  Model: test-model\n",
        ),
    ],
)
def test_explicit_message_output_and_timeout_remain_one_shot(
    arguments: list[str], expected_output: str
) -> None:
    timeouts: list[float] = []
    stdout = StringIO()
    stderr = StringIO()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result("answer"))

    code_command.main(
        ["request", "--timeout-seconds", "300", *arguments],
        _client_factory=lambda **kwargs: (
            timeouts.append(kwargs["timeout"])
            or httpx.Client(transport=httpx.MockTransport(handler), **kwargs)
        ),
        _stdout=stdout,
        _stderr=stderr,
    )

    assert timeouts == [300.0]
    assert stdout.getvalue() == expected_output
    assert stderr.getvalue() == ""


def test_one_shot_empty_result_remains_successful() -> None:
    stdout = StringIO()
    code_command.main(
        ["request"],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=result(""))
            ),
            **kwargs,
        ),
        _stdout=stdout,
        _stderr=StringIO(),
    )

    assert stdout.getvalue() == "\n"


@pytest.mark.parametrize("argv", (["--json"], ["--verbose"], ["-v"]))
def test_no_message_machine_output_modes_fail_before_request(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        code_command.main(
            argv,
            _client_factory=lambda **kwargs: pytest.fail("must not request"),
            _stdin=terminal(),
            _stdout=terminal(),
            _stderr=StringIO(),
        )

    assert raised.value.code == 2


@pytest.mark.parametrize(
    ("stdin", "stdout"),
    [(unreadable_terminal(), terminal()), (terminal(), non_terminal())],
)
def test_no_message_requires_both_tty_streams(
    stdin: StringIO, stdout: StringIO
) -> None:
    stderr = StringIO()
    with pytest.raises(SystemExit) as raised:
        code_command.main(
            [],
            _client_factory=lambda **kwargs: pytest.fail("must not request"),
            _stdin=stdin,
            _stdout=stdout,
            _stderr=stderr,
        )

    assert raised.value.code == 2
    assert stderr.getvalue() == "error: invalid request input\n"


def test_interactive_code_sends_complete_exact_successful_context() -> None:
    requests: list[dict[str, object]] = []
    stderr = StringIO()
    stdout = terminal()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json=result(
                ["```python\nprint('x')\n```\nUse it.", "plain result"][
                    len(requests) - 1
                ]
            ),
        )

    code_command.main(
        [],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdin=terminal("first request\nsecond correction\n"),
        _stdout=stdout,
        _stderr=stderr,
    )

    assert requests == [
        {
            "messages": [{"role": "user", "content": "first request"}],
            "capability": "code",
        },
        {
            "messages": [
                {"role": "user", "content": "first request"},
                {"role": "assistant", "content": "```python\nprint('x')\n```\nUse it."},
                {"role": "user", "content": "second correction"},
            ],
            "capability": "code",
        },
    ]
    assert stderr.getvalue() == "…\n…\n"
    assert "…" not in stdout.getvalue()


def test_blank_and_failed_turns_do_not_mutate_interactive_context() -> None:
    requests: list[dict[str, object]] = []
    stderr = StringIO()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        if len(requests) == 2:
            return httpx.Response(404)
        return httpx.Response(200, json=result("first result"))

    code_command.main(
        [],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdin=terminal("first\n \nfailed\nthird\n"),
        _stdout=terminal(),
        _stderr=stderr,
    )

    assert [request["messages"] for request in requests] == [
        [{"role": "user", "content": "first"}],
        [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "first result"},
            {"role": "user", "content": "failed"},
        ],
        [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "first result"},
            {"role": "user", "content": "third"},
        ],
    ]
    assert stderr.getvalue() == "…\n…\nerror: no available code capability\n…\n"


def test_empty_result_and_over_limit_turns_do_not_send_or_mutate() -> None:
    requests: list[dict[str, object]] = []
    stderr = StringIO()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            return httpx.Response(200, json=result("saved"))
        return httpx.Response(200, json=result(""))

    code_command.main(
        [],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdin=terminal(f"first\nempty\n{'a' * 65_536}\nthird\n"),
        _stdout=terminal(),
        _stderr=stderr,
    )

    assert len(requests) == 3
    assert requests[2]["messages"] == [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "saved"},
        {"role": "user", "content": "third"},
    ]
    assert stderr.getvalue() == (
        "…\n…\nerror: invalid cluster response\n"
        "error: invalid request input\n…\n"
        "error: invalid cluster response\n"
    )


def test_interactive_timeout_is_per_request_and_ctrl_c_exits_cleanly() -> None:
    timeouts: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result("answer"))

    code_command.main(
        ["--timeout-seconds", "300"],
        _client_factory=lambda **kwargs: (
            timeouts.append(kwargs["timeout"])
            or httpx.Client(transport=httpx.MockTransport(handler), **kwargs)
        ),
        _stdin=terminal("one\ntwo\n"),
        _stdout=terminal(),
        _stderr=StringIO(),
    )
    code_command.main(
        [],
        _client_factory=lambda **kwargs: pytest.fail("must not request"),
        _stdin=interrupted_terminal(),
        _stdout=terminal(),
        _stderr=StringIO(),
    )

    assert timeouts == [300.0, 300.0]


def test_timeout_turn_is_not_retained_and_the_loop_continues() -> None:
    requests: list[dict[str, object]] = []
    stderr = StringIO()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            raise httpx.ReadTimeout("private timeout")
        return httpx.Response(200, json=result("answer"))

    code_command.main(
        [],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdin=terminal("timed out\nnext\n"),
        _stdout=terminal(),
        _stderr=stderr,
    )

    assert [request["messages"] for request in requests] == [
        [{"role": "user", "content": "timed out"}],
        [{"role": "user", "content": "next"}],
    ]
    assert stderr.getvalue() == "…\nerror: ordinary request timed out\n…\n"


def test_interactive_candidate_at_code_bound_is_submitted() -> None:
    requests: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=result("answer"))

    code_command.main(
        [],
        _client_factory=lambda **kwargs: httpx.Client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
        _stdin=terminal(f"{'é' * 16_384}\n"),
        _stdout=terminal(),
        _stderr=StringIO(),
    )

    assert len(requests) == 1
