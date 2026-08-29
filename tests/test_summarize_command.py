import json
import stat
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import httpx
import pytest

from home_ai_cluster import summarize_command
from home_ai_cluster.chat_command import _REQUEST_TIMEOUT_SECONDS as _CHAT_TIMEOUT
from home_ai_cluster.summarize_command import _REQUEST_TIMEOUT_SECONDS, main


def client_factory(handler: httpx.MockTransport):
    def create_client(**kwargs: object) -> httpx.Client:
        assert kwargs == {
            "timeout": 120.0,
            "follow_redirects": False,
            "trust_env": False,
        }
        return httpx.Client(transport=handler, **kwargs)

    return create_client


def test_client_uses_the_chat_shared_timeout() -> None:
    assert _REQUEST_TIMEOUT_SECONDS == _CHAT_TIMEOUT == 120.0


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
        return httpx.Response(200, json=result_body(content="summary"))

    def create_client(**kwargs: object) -> httpx.Client:
        captured_timeouts.append(kwargs["timeout"])  # type: ignore[arg-type]
        return httpx.Client(transport=httpx.MockTransport(handler), **kwargs)

    main(
        ["--timeout-seconds", timeout_value, "--text", "source"],
        _client_factory=create_client,
        _stdin=UnreadStream(),
    )

    assert capsys.readouterr().out == "summary\n"
    assert captured_timeouts == [expected_timeout]
    assert len(requests) == 1


def run_command(
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    handler: httpx.MockTransport,
    *,
    stdin: BinaryIO | None = None,
    file_opener=None,
) -> tuple[int, str, str]:
    try:
        kwargs = {
            "_client_factory": client_factory(handler),
            "_stdin": BytesIO() if stdin is None else stdin,
        }
        if file_opener is not None:
            kwargs["_file_opener"] = file_opener
        main(argv, **kwargs)
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


class OpenedShortReadFile(ShortReadStream):
    def __init__(self, path: Path, chunks: list[bytes | Exception]) -> None:
        super().__init__(chunks)
        self.source = path.open("rb")

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        self.source.close()

    def fileno(self) -> int:
        return self.source.fileno()


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
        ["--text", "source", "--timeout-seconds"],
        ["--timeout-seconds", "0", "--text", "source"],
        ["--timeout-seconds", "-1", "--text", "source"],
        ["--timeout-seconds", "+1", "--text", "source"],
        ["--timeout-seconds", "01", "--text", "source"],
        ["--timeout-seconds", "0.5", "--text", "source"],
        ["--timeout-seconds", "300.5", "--text", "source"],
        ["--timeout-seconds", "1e3", "--text", "source"],
        ["--timeout-seconds", "NaN", "--text", "source"],
        ["--timeout-seconds", "Infinity", "--text", "source"],
        ["--timeout-seconds", "3601", "--text", "source"],
        ["--timeout-seconds", "5m", "--text", "source"],
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
    assert str(request.url) == "http://127.0.0.1:25042/v1/summarize"
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
    ("contents", "expected_text"),
    [
        (b"file source", "file source"),
        ("Grüße 👋".encode(), "Grüße 👋"),
        (b"  preserved file source  ", "  preserved file source  "),
    ],
)
def test_regular_file_posts_one_decoded_native_request(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    contents: bytes,
    expected_text: str,
) -> None:
    path = tmp_path / "source.txt"
    path.write_bytes(contents)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=result_body(content="summary"))

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--file", str(path)],
        httpx.MockTransport(handler),
        stdin=UnreadStream(),
    )

    assert exit_code == 0
    assert stdout == "summary\n"
    assert stderr == ""
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert str(request.url) == "http://127.0.0.1:25042/v1/summarize"
    assert json.loads(request.content) == {"text": expected_text}


def test_relative_regular_file_uses_process_working_directory(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "relative.txt").write_bytes(b"relative source")
    monkeypatch.chdir(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body(content="summary"))

    exit_code, _, stderr = run_command(
        capsys,
        ["--file", "relative.txt"],
        httpx.MockTransport(handler),
        stdin=UnreadStream(),
    )

    assert exit_code == 0
    assert stderr == ""


@pytest.mark.parametrize(
    "contents",
    [
        b"",
        b" \n\t",
        b"\xff",
        b"x" * 65_537,
    ],
)
def test_invalid_file_has_one_safe_error_without_http_client(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, contents: bytes
) -> None:
    path = tmp_path / "invalid.txt"
    path.write_bytes(contents)

    with pytest.raises(SystemExit) as raised:
        main(
            ["--file", str(path)],
            _client_factory=unused_client,
            _stdin=UnreadStream(),
        )

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == "error: invalid request input\n"
    assert str(path) not in captured.err


def test_exact_file_byte_limit_is_accepted(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    path = tmp_path / "limit.txt"
    contents = b"x" * 65_536
    path.write_bytes(contents)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=result_body(content="summary"))

    exit_code, _, stderr = run_command(
        capsys, ["--file", str(path)], httpx.MockTransport(handler)
    )

    assert exit_code == 0
    assert stderr == ""
    assert json.loads(requests[0].content) == {"text": contents.decode()}


def test_file_short_reads_and_read_failure_do_not_transmit_partial_input(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    path = tmp_path / "source.txt"
    path.write_bytes(b"regular descriptor")
    source = OpenedShortReadFile(
        path,
        [b"partial ", OSError("private file read failure")],
    )

    with pytest.raises(SystemExit) as raised:
        main(
            ["--file", str(path)],
            _client_factory=unused_client,
            _stdin=UnreadStream(),
            _file_opener=lambda _path, _mode: source,
        )

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == "error: invalid request input\n"
    assert "private" not in captured.err


def test_opened_non_regular_file_descriptor_is_invalid(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "source.txt"
    path.write_bytes(b"source")
    monkeypatch.setattr(
        summarize_command.os,
        "fstat",
        lambda _descriptor: type("Result", (), {"st_mode": stat.S_IFIFO})(),
    )

    with pytest.raises(SystemExit) as raised:
        main(
            ["--file", str(path)],
            _client_factory=unused_client,
            _stdin=UnreadStream(),
        )

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == "error: invalid request input\n"


def test_file_symlink_to_regular_file_is_accepted(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    target = tmp_path / "target.txt"
    target.write_bytes(b"linked source")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error.__class__.__name__}")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body(content="summary"))

    exit_code, _, stderr = run_command(
        capsys, ["--file", str(link)], httpx.MockTransport(handler)
    )

    assert exit_code == 0
    assert stderr == ""


@pytest.mark.parametrize("path_kind", ["missing", "directory", "broken-link"])
def test_invalid_file_paths_are_safe(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, path_kind: str
) -> None:
    path = tmp_path / "path"
    if path_kind == "directory":
        path.mkdir()
    elif path_kind == "broken-link":
        try:
            path.symlink_to(tmp_path / "missing-target")
        except OSError as error:
            pytest.skip(f"symlinks unavailable: {error.__class__.__name__}")

    with pytest.raises(SystemExit) as raised:
        main(
            ["--file", str(path)],
            _client_factory=unused_client,
            _stdin=UnreadStream(),
        )

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == "error: invalid request input\n"
    assert str(path) not in captured.err


def test_file_option_conflicts_and_repetition_are_invalid(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for argv in (
        ["--text", "source", "--file", "private.txt"],
        ["--file", "first.txt", "--file", "second.txt"],
    ):
        with pytest.raises(SystemExit) as raised:
            main(argv, _client_factory=unused_client, _stdin=UnreadStream())

        captured = capsys.readouterr()
        assert raised.value.code == 2
        assert captured.out == ""
        assert captured.err == "error: invalid request input\n"
        assert "private" not in captured.err


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
def test_file_preserves_existing_output_modes(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    arguments: list[str],
    expected_stdout: str,
) -> None:
    path = tmp_path / "source.txt"
    path.write_bytes(b"source")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body(content="summary"))

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--file", str(path), *arguments],
        httpx.MockTransport(handler),
        stdin=UnreadStream(),
    )

    assert exit_code == 0
    assert stdout == expected_stdout
    assert stderr == ""


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
    assert str(request.url) == "http://127.0.0.1:25042/v1/summarize"
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
