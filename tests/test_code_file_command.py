"""Tests for the RFC-0080 one-shot whole-file caller edge."""

import json
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
        ["--file", "target.py", "--message", "   "],
        ["--file", "target.py", "--message", "request", "--timeout-seconds", "0"],
    ),
)
def test_input_requires_exact_file_message_and_timeout(argv: list[str]) -> None:
    with pytest.raises(code_file_command.chat_command._InvalidRequestInput):
        code_file_command._parse_input(argv)


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


@pytest.mark.parametrize("kind", ("missing", "directory", "symlink", "invalid"))
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
