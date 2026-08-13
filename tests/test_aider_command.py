"""Tests for the concrete RFC-0068 and RFC-0069 Aider caller edge."""

import http.client
import json
import subprocess
from pathlib import Path
from typing import Any

import httpx
import pytest

from home_ai_cluster import aider_command


class _NativeClient:
    def __init__(
        self, response: httpx.Response, requests: list[dict[str, Any]]
    ) -> None:
        self._response = response
        self._requests = requests

    def __enter__(self) -> "_NativeClient":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def post(self, url: str, *, json: dict[str, Any]) -> httpx.Response:
        assert url == "http://127.0.0.1:8000/v1/chat"
        self._requests.append(json)
        return self._response


def _response(content: str = "answer") -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "content": content,
            "adapter": "test-adapter",
            "model": "test-model",
            "node_id": "local",
        },
    )


def _supported_run(
    argv: list[str], **kwargs: object
) -> subprocess.CompletedProcess[str]:
    assert kwargs["capture_output"] is True
    assert kwargs["check"] is False
    assert kwargs["text"] is True
    assert argv == ["/test/aider", "--version"]
    return subprocess.CompletedProcess(argv, 0, "aider 0.86.2\n", "")


def _post_bridge(
    base_url: str, body: dict[str, object]
) -> tuple[int, dict[str, object]]:
    parsed = base_url.removeprefix("http://").removesuffix("/v1")
    host, port = parsed.split(":")
    connection = http.client.HTTPConnection(host, int(port))
    connection.request(
        "POST",
        "/v1/chat/completions",
        body=json.dumps(body),
        headers={"Content-Type": "application/json"},
    )
    response = connection.getresponse()
    result = response.status, json.loads(response.read())
    connection.close()
    return result


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
        ["--file", "target.py", "--message", "request", "--unknown"],
    ),
)
def test_input_requires_exact_file_message_and_rfc_0060_timeout(
    argv: list[str],
) -> None:
    with pytest.raises(aider_command.chat_command._InvalidRequestInput):
        aider_command._parse_input(argv)


def test_input_uses_existing_timeout_default_and_validation() -> None:
    parsed = aider_command._parse_input(
        ["--file", "target.py", "--message", "request", "--timeout-seconds", "300"]
    )
    assert parsed.timeout_seconds == 300.0
    assert (
        aider_command._parse_input(
            ["--file", "target.py", "--message", "request"]
        ).timeout_seconds
        == 120.0
    )


def test_invalid_target_fails_before_aider_or_target_creation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    directory = tmp_path / "directory"
    directory.mkdir()
    with pytest.raises(SystemExit) as raised:
        aider_command.main(
            ["--file", str(directory), "--message", "request"],
            _which=lambda name: pytest.fail("must not find Aider"),
        )
    assert raised.value.code == 2
    assert capsys.readouterr().err == "error: invalid Aider target\n"


def test_missing_aider_and_wrong_version_create_no_missing_target(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "target.py"
    with pytest.raises(SystemExit):
        aider_command.main(
            ["--file", str(target), "--message", "request"],
            _which=lambda name: None,
        )
    assert not target.exists()

    def wrong_version(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, "aider 0.86.1\n", "")

    with pytest.raises(SystemExit):
        aider_command.main(
            ["--file", str(target), "--message", "request"],
            _which=lambda name: "/test/aider",
            _run=wrong_version,
        )
    assert not target.exists()
    assert capsys.readouterr().err.count("Aider 0.86.2 is required") == 2


def test_missing_target_is_created_empty_after_prerequisite_and_not_rolled_back(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.py"
    calls: list[list[str]] = []

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[-1] == "--version":
            return _supported_run(argv, **kwargs)
        calls.append(argv)
        assert target.read_text(encoding="utf-8") == ""
        return subprocess.CompletedProcess(argv, 1)

    with pytest.raises(SystemExit) as raised:
        aider_command.main(
            ["--file", str(target), "--message", "request"],
            _which=lambda name: "/test/aider",
            _run=run,
        )
    assert raised.value.code == 1
    assert target.exists()
    assert target.read_text(encoding="utf-8") == ""
    assert len(calls) == 1


def test_existing_target_is_never_changed_by_caller_edge(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    target.write_text("existing caller content\n", encoding="utf-8")

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[-1] == "--version":
            return _supported_run(argv, **kwargs)
        assert target.read_text(encoding="utf-8") == "existing caller content\n"
        return subprocess.CompletedProcess(argv, 1)

    with pytest.raises(SystemExit):
        aider_command.main(
            ["--file", str(target), "--message", "request"],
            _which=lambda name: "/test/aider",
            _run=run,
        )
    assert target.read_text(encoding="utf-8") == "existing caller content\n"


def test_complete_cycle_uses_temporary_material_then_removes_it(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    requests: list[dict[str, Any]] = []
    temporary_paths: list[Path] = []

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[-1] == "--version":
            return _supported_run(argv, **kwargs)
        base_url = argv[argv.index("--openai-api-base") + 1]
        config_path = Path(argv[argv.index("--config") + 1])
        settings_path = Path(argv[argv.index("--model-settings-file") + 1])
        temporary_paths.extend((config_path, settings_path))
        assert config_path.read_text(encoding="utf-8") == "{}\n"
        assert "edit_format: whole" in settings_path.read_text(encoding="utf-8")
        assert target.read_text(encoding="utf-8") == ""
        assert (
            _post_bridge(
                base_url,
                {
                    "model": "home-ai-cluster",
                    "messages": [{"role": "user", "content": "request"}],
                },
            )[0]
            == 200
        )
        return subprocess.CompletedProcess(argv, 0)

    aider_command.main(
        ["--file", str(target), "--message", "request"],
        _which=lambda name: "/test/aider",
        _run=run,
        _client_factory=lambda **kwargs: _NativeClient(_response(), requests),
    )
    assert target.read_text(encoding="utf-8") == ""
    assert requests == [
        {
            "messages": [{"role": "user", "content": "request"}],
            "capability": "code",
        }
    ]
    assert all(not path.exists() for path in temporary_paths)


def test_exclusive_creation_never_truncates_an_appearing_file(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    target.write_text("do not replace", encoding="utf-8")
    assert aider_command._create_missing_target(target)
    assert target.read_text(encoding="utf-8") == "do not replace"


def test_translator_is_loopback_strict_and_projects_one_minimal_response() -> None:
    requests: list[dict[str, Any]] = []
    translator = aider_command._AiderTranslator(
        timeout_seconds=300.0,
        client_factory=lambda **kwargs: _NativeClient(
            _response("edited text"), requests
        ),
    )
    assert translator._server.server_address[0] == "127.0.0.1"
    translator.start()
    try:
        status, response = _post_bridge(
            translator.base_url,
            {
                "model": "home-ai-cluster",
                "messages": [
                    {"role": "system", "content": "system"},
                    {"role": "user", "content": "request"},
                ],
                "stream": False,
            },
        )
    finally:
        translator.close()
    assert status == 200
    assert set(response) == {"id", "object", "created", "model", "choices"}
    assert response["object"] == "chat.completion"
    assert response["model"] == "home-ai-cluster"
    assert response["choices"] == [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "edited text"},
            "finish_reason": None,
        }
    ]
    assert requests == [
        {
            "messages": [
                {"role": "system", "content": "system"},
                {"role": "user", "content": "request"},
            ],
            "capability": "code",
        }
    ]
    assert translator.accepted_request_count == translator.native_request_count == 1


@pytest.mark.parametrize(
    "body",
    (
        {"model": "home-ai-cluster", "messages": [], "temperature": 0},
        {"model": "home-ai-cluster", "messages": [], "stream": True},
        {"model": "home-ai-cluster", "messages": [{"role": "tool", "content": "x"}]},
        {"model": "home-ai-cluster", "messages": [{"role": "user", "content": ["x"]}]},
    ),
)
def test_translator_rejects_unknown_streaming_and_non_plain_messages(
    body: dict[str, object],
) -> None:
    requests: list[dict[str, Any]] = []
    translator = aider_command._AiderTranslator(
        timeout_seconds=120.0,
        client_factory=lambda **kwargs: _NativeClient(_response(), requests),
    )
    translator.start()
    try:
        status, response = _post_bridge(translator.base_url, body)
    finally:
        translator.close()
    assert status == 400
    assert response == {"error": "Home AI Cluster request failed"}
    assert requests == []
    assert translator.accepted_request_count == translator.native_request_count == 0


def test_second_request_cannot_cause_a_second_native_request() -> None:
    requests: list[dict[str, Any]] = []
    translator = aider_command._AiderTranslator(
        timeout_seconds=120.0,
        client_factory=lambda **kwargs: _NativeClient(_response(), requests),
    )
    translator.start()
    request = {
        "model": "home-ai-cluster",
        "messages": [{"role": "user", "content": "request"}],
    }
    try:
        assert _post_bridge(translator.base_url, request)[0] == 200
        # The first success stops the one-shot listener, so there is no second service.
    finally:
        translator.close()
    assert len(requests) == 1


def test_hac_failure_is_small_and_does_not_leak_response_body() -> None:
    requests: list[dict[str, Any]] = []
    translator = aider_command._AiderTranslator(
        timeout_seconds=120.0,
        client_factory=lambda **kwargs: _NativeClient(
            httpx.Response(500, text="secret"), requests
        ),
    )
    translator.start()
    try:
        status, response = _post_bridge(
            translator.base_url,
            {
                "model": "home-ai-cluster",
                "messages": [{"role": "user", "content": "request"}],
            },
        )
    finally:
        translator.close()
    assert status == 502
    assert response == {"error": "Home AI Cluster request failed"}


def test_malformed_hac_success_is_safely_rejected() -> None:
    requests: list[dict[str, Any]] = []
    translator = aider_command._AiderTranslator(
        timeout_seconds=120.0,
        client_factory=lambda **kwargs: _NativeClient(
            httpx.Response(200, json={}), requests
        ),
    )
    translator.start()
    try:
        status, response = _post_bridge(
            translator.base_url,
            {
                "model": "home-ai-cluster",
                "messages": [{"role": "user", "content": "request"}],
            },
        )
    finally:
        translator.close()
    assert status == 502
    assert response == {"error": "Home AI Cluster request failed"}


def test_fixed_aider_arguments_include_all_privacy_guardrails(tmp_path: Path) -> None:
    command_input = aider_command._parse_input(
        ["--file", str(tmp_path / "target.py"), "--message", "private request"]
    )
    argv = aider_command._aider_argv(
        "/test/aider",
        command_input,
        base_url="http://127.0.0.1:1234/v1",
        config_path=tmp_path / "aider.conf.yml",
        model_settings_path=tmp_path / "model-settings.yml",
    )
    assert argv[0] == "/test/aider"
    assert (
        "--llm-history-file" in argv
        and argv[argv.index("--llm-history-file") + 1] == "/dev/null"
    )
    assert {
        "--no-git",
        "--no-auto-test",
        "--no-auto-lint",
        "--no-suggest-shell-commands",
    } <= set(argv)
    assert argv[-4:] == [
        "--file",
        str(command_input.target),
        "--message",
        "private request",
    ]
