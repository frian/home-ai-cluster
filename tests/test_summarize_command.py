import json
from io import BytesIO
from typing import BinaryIO

import httpx
import pytest

from home_ai_cluster.chat_command import _REQUEST_TIMEOUT_SECONDS as _CHAT_TIMEOUT
from home_ai_cluster.summarize_command import _REQUEST_TIMEOUT_SECONDS, main


def client_factory(handler: httpx.MockTransport):
    def create_client(**kwargs: object) -> httpx.Client:
        assert kwargs == {
            "timeout": 120.0,
            "follow_redirects": False,
        }
        return httpx.Client(transport=handler, **kwargs)

    return create_client


def test_client_uses_the_chat_shared_timeout() -> None:
    assert _REQUEST_TIMEOUT_SECONDS == _CHAT_TIMEOUT == 120.0


def run_command(
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    handler: httpx.MockTransport,
    *,
    stdin: BinaryIO | None = None,
) -> tuple[int, str, str]:
    try:
        main(
            argv,
            _client_factory=client_factory(handler),
            _stdin=BytesIO() if stdin is None else stdin,
        )
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
    raise AssertionError("invalid input must not construct an HTTP client")


class ShortReadStream:
    def __init__(self, chunks: list[bytes | Exception]) -> None:
        self.chunks = chunks
        self.read_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        chunk = self.chunks.pop(0) if self.chunks else b""
        if isinstance(chunk, Exception):
            raise chunk
        return chunk


class UnreadStream:
    def read(self, size: int = -1) -> bytes:
        raise AssertionError("explicit --text must not read stdin")


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--text", ""],
        ["--text", "   "],
        ["--text", "first", "--text", "second"],
        ["positional"],
        ["--unknown"],
        ["--text", "source", "--verbose", "--json"],
        ["--text", "ä" * 32_769],
    ],
)
def test_invalid_input_has_one_safe_error(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(argv, _client_factory=unused_client, _stdin=BytesIO())

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == "error: invalid request input\n"
    assert "65,536" not in captured.err


@pytest.mark.parametrize(
    ("stdin_bytes", "expected_text"),
    [
        (b"source text", "source text"),
        ("Grüße 👋".encode(), "Grüße 👋"),
        (b"  preserved source  ", "  preserved source  "),
    ],
)
def test_stdin_posts_one_decoded_native_request(
    capsys: pytest.CaptureFixture[str], stdin_bytes: bytes, expected_text: str
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=result_body(content="summary"))

    exit_code, stdout, stderr = run_command(
        capsys, [], httpx.MockTransport(handler), stdin=BytesIO(stdin_bytes)
    )

    assert exit_code == 0
    assert stdout == "summary\n"
    assert stderr == ""
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert str(request.url) == "http://127.0.0.1:8000/v1/summarize"
    assert json.loads(request.content) == {"text": expected_text}


def test_stdin_handles_short_reads_before_eof(
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = ShortReadStream([b"short ", b"read ", b"source"])
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=result_body(content="summary"))

    exit_code, _, stderr = run_command(
        capsys, [], httpx.MockTransport(handler), stdin=source
    )

    assert exit_code == 0
    assert stderr == ""
    assert json.loads(requests[0].content) == {"text": "short read source"}
    assert len(source.read_sizes) == 4


@pytest.mark.parametrize(
    "stdin",
    [
        BytesIO(),
        BytesIO(b"  \n\t"),
        BytesIO(b"\xff"),
        BytesIO(b"x" * 65_537),
        ShortReadStream([b"source", OSError("private read failure")]),
    ],
)
def test_invalid_stdin_has_one_safe_error_without_http_client(
    capsys: pytest.CaptureFixture[str], stdin: BinaryIO
) -> None:
    with pytest.raises(SystemExit) as raised:
        main([], _client_factory=unused_client, _stdin=stdin)

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == "error: invalid request input\n"
    assert "private" not in captured.err
    assert "xff" not in captured.err


def test_exact_stdin_byte_limit_is_accepted(
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = b"x" * 65_536
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=result_body(content="summary"))

    exit_code, _, stderr = run_command(
        capsys, [], httpx.MockTransport(handler), stdin=BytesIO(source)
    )

    assert exit_code == 0
    assert stderr == ""
    assert json.loads(requests[0].content) == {"text": source.decode()}


def test_oversized_stdin_stops_after_the_limit_without_transmission(
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = ShortReadStream([b"x" * 65_537, AssertionError("must not drain")])

    with pytest.raises(SystemExit) as raised:
        main([], _client_factory=unused_client, _stdin=source)

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == "error: invalid request input\n"
    assert source.read_sizes == [65_537]


def test_explicit_text_takes_precedence_without_reading_stdin(
    capsys: pytest.CaptureFixture[str],
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=result_body(content="summary"))

    exit_code, _, stderr = run_command(
        capsys,
        ["--text", "argument text"],
        httpx.MockTransport(handler),
        stdin=UnreadStream(),
    )

    assert exit_code == 0
    assert stderr == ""
    assert json.loads(requests[0].content) == {"text": "argument text"}


@pytest.mark.parametrize(
    ("arguments", "expected_stdout"),
    [
        ([], "summary\n"),
        (
            ["--verbose"],
            "Response:\nsummary\n\nExecution:\n  Node: cluster-node\n"
            "  Adapter: test-adapter\n  Model: cluster-model\n",
        ),
        (
            ["--json"],
            '{"content":"summary","adapter":"test-adapter",'
            '"model":"cluster-model","node_id":"cluster-node"}\n',
        ),
    ],
)
def test_stdin_preserves_existing_output_modes(
    capsys: pytest.CaptureFixture[str], arguments: list[str], expected_stdout: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body(content="summary"))

    exit_code, stdout, stderr = run_command(
        capsys,
        arguments,
        httpx.MockTransport(handler),
        stdin=BytesIO(b"source"),
    )

    assert exit_code == 0
    assert stdout == expected_stdout
    assert stderr == ""


@pytest.mark.parametrize("output_arguments", [[], ["--verbose"], ["-v"], ["--json"]])
def test_every_output_mode_posts_one_exact_native_request(
    capsys: pytest.CaptureFixture[str], output_arguments: list[str]
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=result_body(content="summary"))

    exit_code, _, stderr = run_command(
        capsys,
        ["--text", "  preserved source  ", *output_arguments],
        httpx.MockTransport(handler),
    )

    assert exit_code == 0
    assert stderr == ""
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert str(request.url) == "http://127.0.0.1:8000/v1/summarize"
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {"text": "  preserved source  "}


@pytest.mark.parametrize(
    ("content", "expected_stdout"),
    [
        ("summary", "summary\n"),
        ("summary\n", "summary\n"),
        ("", "\n"),
    ],
)
def test_default_mode_reuses_chat_terminal_newline_rule(
    capsys: pytest.CaptureFixture[str], content: str, expected_stdout: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body(content=content))

    exit_code, stdout, stderr = run_command(
        capsys, ["--text", "source"], httpx.MockTransport(handler)
    )

    assert exit_code == 0
    assert stdout == expected_stdout
    assert stderr == ""


@pytest.mark.parametrize(
    ("arguments", "content", "model", "expected_stdout"),
    [
        (
            ["--verbose"],
            "summary",
            "model-a",
            "Response:\nsummary\n\nExecution:\n  Node: cluster-node\n"
            "  Adapter: test-adapter\n  Model: model-a\n",
        ),
        (
            ["-v"],
            "summary\n\n",
            None,
            "Response:\nsummary\n\nExecution:\n  Node: cluster-node\n"
            "  Adapter: test-adapter\n",
        ),
    ],
)
def test_verbose_mode_reuses_chat_formatter_exactly(
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
    content: str,
    model: str | None,
    expected_stdout: str,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body(content=content, model=model))

    exit_code, stdout, stderr = run_command(
        capsys, ["--text", "source", *arguments], httpx.MockTransport(handler)
    )

    assert exit_code == 0
    assert stdout == expected_stdout
    assert stderr == ""


def test_json_mode_reuses_chat_compact_serialization(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body(content="Grüße 👋", model=None))

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--text", "source", "--json"],
        httpx.MockTransport(handler),
    )

    assert exit_code == 0
    assert (
        stdout
        == '{"content":"Gr\\u00fc\\u00dfe \\ud83d\\udc4b","adapter":"test-adapter",'
        '"model":null,"node_id":"cluster-node"}\n'
    )
    assert stderr == ""


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (422, "error: cluster rejected request"),
        (404, "error: no available summarize capability"),
        (503, "error: runtime adapter unavailable"),
        (500, "error: ordinary request failed"),
    ],
)
def test_http_failures_are_safely_mapped(
    capsys: pytest.CaptureFixture[str], status_code: int, expected_error: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, text="private response body")

    exit_code, stdout, stderr = run_command(
        capsys, ["--text", "private source"], httpx.MockTransport(handler)
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == f"{expected_error}\n"
    assert "private" not in stderr


def test_connection_failure_is_safely_mapped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("http://private-host token=secret")

    exit_code, stdout, stderr = run_command(
        capsys, ["--text", "private source"], httpx.MockTransport(handler)
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
        capsys, ["--text", "private source"], httpx.MockTransport(handler)
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: ordinary request timed out\n"
    assert "private" not in stderr
    assert "timeout detail" not in stderr


def test_other_httpx_request_failure_is_safely_mapped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ProtocolError("private protocol detail")

    exit_code, stdout, stderr = run_command(
        capsys, ["--text", "private source"], httpx.MockTransport(handler)
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: ordinary request failed\n"
    assert "private" not in stderr
    assert "protocol" not in stderr


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"not-json"),
        httpx.Response(200, json={"content": "private summary"}),
    ],
)
def test_invalid_success_responses_are_rejected(
    capsys: pytest.CaptureFixture[str], response: httpx.Response
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return response

    exit_code, stdout, stderr = run_command(
        capsys, ["--text", "private source"], httpx.MockTransport(handler)
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
        capsys, ["--text", "private source"], httpx.MockTransport(handler)
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: ordinary request failed\n"
    assert "private" not in stderr
    assert "secret" not in stderr
