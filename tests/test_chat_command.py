import json
from io import StringIO

import httpx
import pytest

from home_ai_cluster.chat_command import (
    _INTERACTIVE_MESSAGE_CONTENT_LIMIT,
    _REQUEST_TIMEOUT_SECONDS,
    main,
)


class terminal(StringIO):
    def isatty(self) -> bool:
        return True


class non_terminal(StringIO):
    def isatty(self) -> bool:
        return False


class interrupted_terminal(terminal):
    def readline(self, size: int | None = -1) -> str:
        raise KeyboardInterrupt


def client_factory(handler: httpx.MockTransport):
    def create_client(**kwargs: object) -> httpx.Client:
        assert kwargs == {
            "timeout": 120.0,
            "follow_redirects": False,
            "trust_env": False,
        }
        return httpx.Client(transport=handler, **kwargs)

    return create_client


def test_client_uses_the_accepted_shared_timeout() -> None:
    assert _REQUEST_TIMEOUT_SECONDS == 120.0


@pytest.mark.parametrize(
    ("timeout_value", "expected_timeout"),
    [("1", 1.0), ("300", 300.0), ("3600", 3600.0)],
)
def test_client_accepts_integer_timeout_override(
    capsys: pytest.CaptureFixture[str],
    timeout_value: str,
    expected_timeout: float,
) -> None:
    requests: list[httpx.Request] = []
    captured_timeouts: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=result_body(content="response"))

    def create_client(**kwargs: object) -> httpx.Client:
        captured_timeouts.append(kwargs["timeout"])  # type: ignore[arg-type]
        return httpx.Client(transport=httpx.MockTransport(handler), **kwargs)

    main(
        ["--timeout-seconds", timeout_value, "Hello"],
        _client_factory=create_client,
    )

    assert capsys.readouterr().out == "response\n"
    assert captured_timeouts == [expected_timeout]
    assert len(requests) == 1


def run_command(
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    handler: httpx.MockTransport,
) -> tuple[int, str, str]:
    try:
        main(argv, _client_factory=client_factory(handler))
    except SystemExit as error:
        exit_code = error.code
    else:
        exit_code = 0
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def result_body(
    *, content: str, model: str | None = "cluster-model"
) -> dict[str, str | None]:
    return {
        "content": content,
        "adapter": "test-adapter",
        "model": model,
        "node_id": "cluster-node",
    }


def unused_client(**kwargs: object) -> httpx.Client:
    raise AssertionError("invalid input and --help must not send a request")


@pytest.mark.parametrize(
    "argv",
    [
        [],
        [""],
        ["   "],
        ["--message", ""],
        ["--message", "   "],
        ["--unknown"],
        ["--message", "first", "--message", "second"],
        ["positional", "--message", "option"],
        ["first", "second"],
        ["Hello", "--timeout-seconds"],
        ["--timeout-seconds", "0", "Hello"],
        ["--timeout-seconds", "-1", "Hello"],
        ["--timeout-seconds", "+1", "Hello"],
        ["--timeout-seconds", "01", "Hello"],
        ["--timeout-seconds", "0.5", "Hello"],
        ["--timeout-seconds", "300.5", "Hello"],
        ["--timeout-seconds", "1e3", "Hello"],
        ["--timeout-seconds", "NaN", "Hello"],
        ["--timeout-seconds", "Infinity", "Hello"],
        ["--timeout-seconds", "3601", "Hello"],
        ["--timeout-seconds", "5m", "Hello"],
    ],
)
def test_invalid_input_has_one_safe_error(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(argv, _client_factory=unused_client)

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == "error: invalid request input\n"


def test_help_does_not_send_a_request(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--help"], _client_factory=unused_client)

    captured = capsys.readouterr()
    assert raised.value.code == 0
    assert captured.out.startswith("usage: home-ai-cluster-chat")
    assert captured.err == ""


@pytest.mark.parametrize(
    "message_arguments",
    [["  preserved message  "], ["--message", "  preserved message  "]],
)
@pytest.mark.parametrize("output_arguments", [[], ["--verbose"], ["-v"], ["--json"]])
def test_every_output_mode_posts_one_exact_native_request(
    capsys: pytest.CaptureFixture[str],
    message_arguments: list[str],
    output_arguments: list[str],
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "content": "response content",
                "adapter": "test-adapter",
                "model": "cluster-model",
                "node_id": "cluster-node",
            },
        )

    exit_code, stdout, stderr = run_command(
        capsys,
        [*message_arguments, *output_arguments],
        httpx.MockTransport(handler),
    )

    assert exit_code == 0
    assert stderr == ""
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert str(request.url) == "http://127.0.0.1:8000/v1/chat"
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {
        "messages": [{"role": "user", "content": "  preserved message  "}],
        "capability": "chat",
    }


@pytest.mark.parametrize(
    ("content", "expected_stdout"),
    [
        ("answer", "answer\n"),
        ("answer\n", "answer\n"),
        ("answer\n\n", "answer\n\n"),
        ("", "\n"),
        ("first\n\n  second  ", "first\n\n  second  \n"),
        ("  leading and trailing  ", "  leading and trailing  \n"),
        ("```python\nprint('hello')\n```", "```python\nprint('hello')\n```\n"),
        ("Grüße 👋", "Grüße 👋\n"),
    ],
)
def test_default_mode_projects_content_with_terminal_newline_rule(
    capsys: pytest.CaptureFixture[str], content: str, expected_stdout: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body(content=content))

    exit_code, stdout, stderr = run_command(
        capsys, ["--message", "request"], httpx.MockTransport(handler)
    )

    assert exit_code == 0
    assert stdout == expected_stdout
    assert stderr == ""


@pytest.mark.parametrize(
    ("arguments", "content", "model", "expected_stdout"),
    [
        (
            ["--verbose"],
            "answer",
            "model-a",
            "Response:\nanswer\n\nExecution:\n  Node: cluster-node\n"
            "  Adapter: test-adapter\n  Model: model-a\n",
        ),
        (
            ["-v"],
            "answer\n",
            "model-a",
            "Response:\nanswer\n\nExecution:\n  Node: cluster-node\n"
            "  Adapter: test-adapter\n  Model: model-a\n",
        ),
        (
            ["--verbose"],
            "answer\n\n",
            None,
            "Response:\nanswer\n\nExecution:\n  Node: cluster-node\n"
            "  Adapter: test-adapter\n",
        ),
        (
            ["--verbose"],
            "",
            "",
            "Response:\n\nExecution:\n  Node: cluster-node\n  Adapter: test-adapter\n",
        ),
        (
            ["--verbose"],
            "first\n  indented second",
            "model-a",
            "Response:\nfirst\n  indented second\n\nExecution:\n"
            "  Node: cluster-node\n  Adapter: test-adapter\n  Model: model-a\n",
        ),
        (
            ["--verbose"],
            "Grüße 👋",
            "model-a",
            "Response:\nGrüße 👋\n\nExecution:\n  Node: cluster-node\n"
            "  Adapter: test-adapter\n  Model: model-a\n",
        ),
    ],
)
def test_verbose_mode_formats_content_and_attribution_exactly(
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
    content: str,
    model: str | None,
    expected_stdout: str,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body(content=content, model=model))

    exit_code, stdout, stderr = run_command(
        capsys, ["--message", "request", *arguments], httpx.MockTransport(handler)
    )

    assert exit_code == 0
    assert stdout == expected_stdout
    assert stderr == ""


@pytest.mark.parametrize(
    ("content", "model", "expected_stdout"),
    [
        (
            "response content",
            "cluster-model",
            '{"content":"response content","adapter":"test-adapter",'
            '"model":"cluster-model","node_id":"cluster-node"}\n',
        ),
        (
            "response content",
            None,
            '{"content":"response content","adapter":"test-adapter",'
            '"model":null,"node_id":"cluster-node"}\n',
        ),
        (
            "Grüße 👋",
            "cluster-model",
            '{"content":"Gr\\u00fc\\u00dfe \\ud83d\\udc4b","adapter":"test-adapter",'
            '"model":"cluster-model","node_id":"cluster-node"}\n',
        ),
    ],
)
def test_json_mode_preserves_historical_compact_serialization(
    capsys: pytest.CaptureFixture[str],
    content: str,
    model: str | None,
    expected_stdout: str,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body(content=content, model=model))

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "request", "--json"],
        httpx.MockTransport(handler),
    )

    assert exit_code == 0
    assert stdout == expected_stdout
    assert stderr == ""


@pytest.mark.parametrize(
    "arguments",
    [["--verbose", "--json"], ["-v", "--json"]],
)
def test_conflicting_output_options_fail_before_client_construction(
    capsys: pytest.CaptureFixture[str], arguments: list[str]
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--message", "request", *arguments], _client_factory=unused_client)

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == "error: invalid request input\n"


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (422, "error: cluster rejected request"),
        (404, "error: no available chat capability"),
        (503, "error: runtime adapter unavailable"),
        (500, "error: ordinary request failed"),
    ],
)
def test_http_failures_are_safely_mapped(
    capsys: pytest.CaptureFixture[str], status_code: int, expected_error: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            text="private response body and generated response",
        )

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "private submitted prompt"],
        httpx.MockTransport(handler),
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == f"{expected_error}\n"
    assert "private" not in stderr
    assert "response body" not in stderr


def test_connection_failure_is_safely_mapped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("http://private-host token=secret")

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "private submitted prompt"],
        httpx.MockTransport(handler),
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: ordinary cluster unavailable\n"
    assert "private" not in stderr
    assert "secret" not in stderr


@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectTimeout("private timeout detail"),
        httpx.ReadTimeout("private timeout detail"),
        httpx.WriteTimeout("private timeout detail"),
        httpx.PoolTimeout("private timeout detail"),
    ],
)
def test_timeout_failures_are_safely_mapped(
    capsys: pytest.CaptureFixture[str], error: Exception
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "private submitted prompt"],
        httpx.MockTransport(handler),
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: ordinary request timed out\n"
    assert "private" not in stderr
    assert "timeout detail" not in stderr


def test_other_httpx_request_failures_are_safely_mapped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ProtocolError("private protocol detail")

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "private submitted prompt"],
        httpx.MockTransport(handler),
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: ordinary request failed\n"
    assert "private" not in stderr
    assert "protocol" not in stderr


def test_no_message_requires_both_terminal_streams_before_read_or_request() -> None:
    for stdin, stdout in [
        (non_terminal("unexpected"), terminal()),
        (terminal(), non_terminal()),
    ]:
        stderr = StringIO()
        with pytest.raises(SystemExit) as raised:
            main(
                [],
                _client_factory=unused_client,
                _stdin=stdin,
                _stdout=stdout,
                _stderr=stderr,
            )

        assert raised.value.code == 2
        assert stdin.tell() == 0
        assert stderr.getvalue() == "error: invalid request input\n"


@pytest.mark.parametrize("arguments", [["--json"], ["--verbose"], ["-v"]])
def test_no_message_output_modes_fail_before_request(arguments: list[str]) -> None:
    stderr = StringIO()
    with pytest.raises(SystemExit) as raised:
        main(
            arguments,
            _client_factory=unused_client,
            _stdin=terminal(),
            _stdout=terminal(),
            _stderr=stderr,
        )

    assert raised.value.code == 2
    assert stderr.getvalue() == "error: invalid request input\n"


def test_interactive_turns_send_complete_successful_context_and_per_turn_timeout() -> (
    None
):
    requests: list[dict[str, object]] = []
    timeouts: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=result_body(content=f"answer {len(requests)}"))

    def create_client(**kwargs: object) -> httpx.Client:
        timeouts.append(kwargs["timeout"])  # type: ignore[arg-type]
        return httpx.Client(transport=httpx.MockTransport(handler), **kwargs)

    stdout, stderr = terminal(), StringIO()
    main(
        ["--timeout-seconds", "300"],
        _client_factory=create_client,
        _stdin=terminal("first\nsecond\n"),
        _stdout=stdout,
        _stderr=stderr,
    )

    assert requests == [
        {"messages": [{"role": "user", "content": "first"}], "capability": "chat"},
        {
            "messages": [
                {"role": "user", "content": "first"},
                {"role": "assistant", "content": "answer 1"},
                {"role": "user", "content": "second"},
            ],
            "capability": "chat",
        },
    ]
    assert timeouts == [300.0, 300.0]
    assert stdout.getvalue() == "> answer 1\n> answer 2\n> "
    assert stderr.getvalue() == ""


def test_interactive_failed_turn_is_not_retained_and_session_continues() -> None:
    requests: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        if len(requests) == 2:
            raise httpx.ReadTimeout("private")
        return httpx.Response(200, json=result_body(content=f"answer {len(requests)}"))

    stdout, stderr = terminal(), StringIO()
    main(
        [],
        _client_factory=client_factory(httpx.MockTransport(handler)),
        _stdin=terminal("first\nfailed\nthird\n"),
        _stdout=stdout,
        _stderr=stderr,
    )

    assert requests[2]["messages"] == [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "answer 1"},
        {"role": "user", "content": "third"},
    ]
    assert stderr.getvalue() == "error: ordinary request timed out\n"


def test_interactive_blank_turns_send_nothing_and_eof_returns_normally() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=result_body(content="answer"))

    main(
        [],
        _client_factory=client_factory(httpx.MockTransport(handler)),
        _stdin=terminal("\n  \t\nmessage\n"),
        _stdout=terminal(),
        _stderr=StringIO(),
    )

    assert len(requests) == 1


def test_interactive_ctrl_c_exits_cleanly_without_a_request() -> None:
    main(
        [],
        _client_factory=unused_client,
        _stdin=interrupted_terminal(),
        _stdout=terminal(),
        _stderr=StringIO(),
    )


def test_interactive_aggregate_bound_rejects_only_the_new_turn() -> None:
    accepted = "é" * (_INTERACTIVE_MESSAGE_CONTENT_LIMIT // 2)
    requests: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=result_body(content="a"))

    stderr = StringIO()
    main(
        [],
        _client_factory=client_factory(httpx.MockTransport(handler)),
        _stdin=terminal(f"{accepted}\nx\n"),
        _stdout=terminal(),
        _stderr=stderr,
    )

    assert len(requests) == 1
    assert stderr.getvalue() == "error: invalid request input\n"


@pytest.mark.parametrize(
    ("arguments", "response"),
    [
        ([], httpx.Response(200, content=b"not-json")),
        (
            ["--verbose"],
            httpx.Response(200, json={"content": "private generated response"}),
        ),
        (["--json"], httpx.Response(200, content=b"not-json")),
    ],
)
def test_invalid_success_responses_are_rejected(
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
    response: httpx.Response,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return response

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "private submitted prompt", *arguments],
        httpx.MockTransport(handler),
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: invalid cluster response\n"
    assert "private" not in stderr


def test_unexpected_client_failure_is_safely_mapped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise RuntimeError("private exception token=secret")

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "private submitted prompt"],
        httpx.MockTransport(handler),
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: ordinary request failed\n"
    assert "private" not in stderr
    assert "secret" not in stderr
