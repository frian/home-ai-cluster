"""Tests for the RFC-0080 one-shot whole-file caller edge."""

import json
import os
import stat
from pathlib import Path

import httpx
import pytest

from home_ai_cluster import code_file_command


def _response(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "content": content,
            "adapter": "test-adapter",
            "model": "test-model",
            "node_id": "local",
        },
    )


@pytest.mark.parametrize(
    "argv",
    (
        [],
        ["--file", "target.py"],
        ["--message", "request"],
        ["--file", "target.py", "--file", "other.py", "--message", "request"],
        ["--file", "target.py", "--message", "request", "--message", "again"],
        ["--file", "target.py", "request", "--message", "again"],
        ["--file", "target.py", "one", "two"],
        ["--file", "target.py", "--unknown"],
        ["--file", "target.py", "   "],
        ["--file", "target.py", "--message", "   "],
        ["--file", "target.py", "--message", "request", "--timeout-seconds", "0"],
    ),
)
def test_input_requires_exact_file_message_and_timeout(argv: list[str]) -> None:
    with pytest.raises(code_file_command.chat_command._InvalidRequestInput):
        code_file_command._parse_input(argv)


def test_positional_and_option_messages_normalize_to_the_same_request() -> None:
    positional = code_file_command._parse_input(["--file", "target.py", "request"])
    option = code_file_command._parse_input(
        ["--file", "target.py", "--message", "request"]
    )

    assert positional.message == option.message == "request"
    assert code_file_command._native_request(positional.message, "before") == (
        code_file_command._native_request(option.message, "before")
    )


def test_request_contains_only_fixed_and_json_messages(tmp_path: Path) -> None:
    target = tmp_path / "secret-name.py"
    target.write_text("before\r\n", encoding="utf-8", newline="")

    current, _ = code_file_command._read_target(target)
    request = code_file_command._native_request("make it better", current)

    assert request["capability"] == "code"
    messages = request["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "secret-name.py" not in str(messages)
    assert json.loads(messages[1]["content"]) == {
        "instruction": "make it better",
        "current_content": "before\r\n",
    }


@pytest.mark.parametrize("kind", ("directory", "symlink", "broken-symlink", "invalid"))
def test_invalid_target_fails_before_request(
    tmp_path: Path, kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target"
    if kind == "directory":
        target.mkdir()
    elif kind == "symlink":
        source = tmp_path / "source"
        source.write_text("text", encoding="utf-8")
        target.symlink_to(source)
    elif kind == "broken-symlink":
        target.symlink_to(tmp_path / "missing-source")
    elif kind == "invalid":
        target.write_bytes(b"\xff")
    calls = 0

    def post(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("must not request")

    monkeypatch.setattr(code_file_command.chat_command, "_post_native_request", post)
    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), "--message", "request"])
    assert calls == 0


def test_missing_target_uses_empty_content_and_one_native_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "secret-name.py"
    requests: list[dict[str, object]] = []

    def post(request: dict[str, object], **kwargs: object) -> httpx.Response:
        requests.append(request)
        return _response('{"version":1,"content":"after"}')

    monkeypatch.setattr(code_file_command.chat_command, "_post_native_request", post)

    code_file_command.main(["--file", str(target), "--message", "request"])

    assert target.is_file()
    assert target.read_text(encoding="utf-8") == "after"
    assert len(requests) == 1
    assert requests[0]["capability"] == "code"
    messages = requests[0]["messages"]
    assert isinstance(messages, list)
    assert [message["role"] for message in messages] == ["system", "user"]
    assert json.loads(messages[1]["content"]) == {
        "instruction": "request",
        "current_content": "",
    }
    assert "secret-name.py" not in str(messages)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize("parent_kind", ("missing", "file"))
def test_missing_target_invalid_parent_fails_before_creation_and_request(
    tmp_path: Path, parent_kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = tmp_path / "parent"
    if parent_kind == "file":
        parent.write_text("not a directory", encoding="utf-8")
    target = parent / "target.py"
    calls = 0

    def post(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("must not request")

    monkeypatch.setattr(code_file_command.chat_command, "_post_native_request", post)
    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), "--message", "request"])
    assert calls == 0
    assert not target.exists()
    assert not parent.exists() if parent_kind == "missing" else parent.is_file()


@pytest.mark.parametrize(
    "argv",
    (
        ["--message", "   "],
        ["request", "--message", "other"],
        ["--message", "request", "--timeout-seconds", "0"],
    ),
)
def test_missing_target_invalid_input_creates_nothing_before_request(
    tmp_path: Path, argv: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    calls = 0

    def post(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("must not request")

    monkeypatch.setattr(code_file_command.chat_command, "_post_native_request", post)
    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), *argv])
    assert calls == 0
    assert not target.exists()


def test_missing_target_oversized_prospective_request_creates_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: pytest.fail("must not request"),
    )

    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), "--message", "x" * 65_536])

    assert not target.exists()


def test_missing_target_creation_race_fails_without_request_or_adoption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    calls = 0

    def create_race(path: Path) -> int:
        path.write_text("appeared", encoding="utf-8")
        raise ValueError

    def post(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("must not request")

    monkeypatch.setattr(code_file_command, "_create_missing_target", create_race)
    monkeypatch.setattr(code_file_command.chat_command, "_post_native_request", post)
    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), "--message", "request"])
    assert calls == 0
    assert target.read_text(encoding="utf-8") == "appeared"


def test_missing_target_creation_requests_non_executable_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    original_open = os.open
    creation: list[tuple[int, int]] = []

    def open_target(path: Path, flags: int, mode: int) -> int:
        creation.append((flags, mode))
        return original_open(path, flags, mode)

    monkeypatch.setattr(code_file_command.os, "open", open_target)
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: _response('{"version":1,"content":"after"}'),
    )
    code_file_command.main(["--file", str(target), "--message", "request"])

    assert creation[0] == (os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)


def test_missing_target_mode_uses_umask_and_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: _response('{"version":1,"content":"after"}'),
    )
    previous_umask = os.umask(0o022)
    try:
        code_file_command.main(["--file", str(target), "--message", "request"])
    finally:
        os.umask(previous_umask)

    assert stat.S_IMODE(target.stat().st_mode) == 0o644


@pytest.mark.parametrize(
    "failure",
    (
        httpx.TimeoutException("timeout"),
        httpx.ConnectError("unavailable"),
        httpx.RequestError("failed"),
        httpx.Response(404),
        httpx.Response(200, json={"content": "missing fields"}),
        _response("not an RFC-0080 envelope"),
        _response(json.dumps({"version": 1, "content": "é" * 32_769})),
    ),
)
def test_missing_target_later_failures_leave_empty_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: object
) -> None:
    target = tmp_path / "target.py"
    calls = 0

    def post(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal calls
        calls += 1
        if isinstance(failure, Exception):
            raise failure
        assert isinstance(failure, httpx.Response)
        return failure

    monkeypatch.setattr(code_file_command.chat_command, "_post_native_request", post)
    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), "--message", "request"])
    assert calls == 1
    assert target.read_bytes() == b""


def test_missing_target_atomic_failure_leaves_empty_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: _response('{"version":1,"content":"after"}'),
    )
    monkeypatch.setattr(code_file_command, "_atomic_replace", lambda *args: False)

    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), "--message", "request"])
    assert target.read_bytes() == b""


def test_missing_target_empty_generated_content_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: _response('{"version":1,"content":""}'),
    )

    code_file_command.main(["--file", str(target), "--message", "request"])

    assert target.is_file()
    assert target.read_bytes() == b""


@pytest.mark.parametrize(
    "envelope",
    (
        '```json\n{"version":1,"content":"after"}\n```',
        'prose {"version":1,"content":"after"}',
        "{",
        '{"version":1}',
        '{"version":1,"content":"after","path":"x"}',
        '{"version":1,"version":1,"content":"after"}',
        '{"version":true,"content":"after"}',
        '{"version":1.0,"content":"after"}',
        '{"version":"1","content":"after"}',
    ),
)
def test_invalid_envelopes_leave_target_untouched(
    tmp_path: Path, envelope: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    target.write_text("before", encoding="utf-8")
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: _response(envelope),
    )
    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), "--message", "request"])
    assert target.read_text(encoding="utf-8") == "before"


def test_valid_unicode_empty_and_newline_replacement_is_silent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "target.py"
    target.write_text("before", encoding="utf-8")
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: _response('{"version":1,"content":"é\\n"}'),
    )
    code_file_command.main(["--file", str(target), "--message", "request"])
    assert target.read_text(encoding="utf-8", newline="") == "é\n"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_empty_content_replaces_target_with_zero_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    target.write_text("before", encoding="utf-8")
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: _response('{"version":1,"content":""}'),
    )

    code_file_command.main(["--file", str(target), "--message", "request"])

    assert target.read_bytes() == b""


def test_one_request_has_the_rfc_0080_native_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    target.write_text("before", encoding="utf-8")
    requests: list[dict[str, object]] = []

    def post(request: dict[str, object], **kwargs: object) -> httpx.Response:
        requests.append(request)
        return _response('{"version":1,"content":"after"}')

    monkeypatch.setattr(code_file_command.chat_command, "_post_native_request", post)
    code_file_command.main(["--file", str(target), "--message", "request"])

    assert len(requests) == 1
    assert requests[0]["capability"] == "code"
    messages = requests[0]["messages"]
    assert isinstance(messages, list)
    assert len(messages) == 2
    assert [message["role"] for message in messages] == ["system", "user"]


def test_malformed_model_output_does_not_make_a_corrective_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    target.write_text("before", encoding="utf-8")
    calls = 0

    def post(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _response("not an RFC-0080 envelope")

    monkeypatch.setattr(code_file_command.chat_command, "_post_native_request", post)
    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), "--message", "request"])

    assert calls == 1
    assert target.read_text(encoding="utf-8") == "before"


def test_output_bound_is_utf8_bytes_and_preserves_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    target.write_text("before", encoding="utf-8")
    target.chmod(0o755)
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: _response(
            json.dumps({"version": 1, "content": "é" * 32_769})
        ),
    )
    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), "--message", "request"])
    assert target.read_text(encoding="utf-8") == "before"

    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: _response('{"version":1,"content":"after"}'),
    )
    code_file_command.main(["--file", str(target), "--message", "request"])
    assert target.read_text(encoding="utf-8") == "after"
    assert stat.S_IMODE(target.stat().st_mode) == 0o755


def test_input_bound_fails_before_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    target.write_text("x" * 65_536, encoding="utf-8")
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: pytest.fail("must not request"),
    )
    with pytest.raises(SystemExit) as raised:
        code_file_command.main(["--file", str(target), "--message", "request"])
    assert raised.value.code == 2


def test_native_404_uses_code_capability_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "target.py"
    target.write_text("before", encoding="utf-8")
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: httpx.Response(404),
    )
    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), "--message", "request"])
    assert capsys.readouterr().err == "error: no available code capability\n"
    assert target.read_text(encoding="utf-8") == "before"


@pytest.mark.parametrize(
    "exception",
    (
        httpx.TimeoutException("timeout"),
        httpx.ConnectError("unavailable"),
        httpx.RequestError("failed"),
    ),
)
def test_native_exceptions_leave_target_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exception: httpx.RequestError
) -> None:
    target = tmp_path / "target.py"
    target.write_text("before", encoding="utf-8")
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: (_ for _ in ()).throw(exception),
    )

    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), "--message", "request"])

    assert target.read_text(encoding="utf-8") == "before"


def test_malformed_native_result_leaves_target_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    target.write_text("before", encoding="utf-8")
    monkeypatch.setattr(
        code_file_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: httpx.Response(200, json={"content": "missing fields"}),
    )

    with pytest.raises(SystemExit):
        code_file_command.main(["--file", str(target), "--message", "request"])

    assert target.read_text(encoding="utf-8") == "before"


def test_atomic_preparation_failure_cleans_up_and_preserves_target(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.py"
    target.write_text("before", encoding="utf-8")

    assert not code_file_command._atomic_replace(
        target,
        b"after",
        0o644,
        fsync=lambda descriptor: (_ for _ in ()).throw(OSError("failed")),
    )

    assert target.read_text(encoding="utf-8") == "before"
    assert list(tmp_path.glob(".hac-code-file-*")) == []


@pytest.mark.parametrize("operation", ("chmod", "replace"))
def test_atomic_permission_or_replace_failure_cleans_up_and_preserves_target(
    tmp_path: Path, operation: str
) -> None:
    target = tmp_path / "target.py"
    target.write_text("before", encoding="utf-8")

    def failing(*args: object) -> None:
        raise OSError("failed")

    kwargs = {operation: failing}

    assert not code_file_command._atomic_replace(target, b"after", 0o644, **kwargs)

    assert target.read_text(encoding="utf-8") == "before"
    assert list(tmp_path.glob(".hac-code-file-*")) == []


def test_atomic_replacement_keeps_only_ordinary_permission_bits(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    target.write_text("before", encoding="utf-8")

    assert code_file_command._atomic_replace(target, b"after", 0o6755)

    assert target.read_text(encoding="utf-8") == "after"
    assert stat.S_IMODE(target.stat().st_mode) == 0o755
