"""Tests for the concrete RFC-0068, RFC-0069, and RFC-0072 Aider caller edge."""

import http.client
import json
import subprocess
import threading
from pathlib import Path
from typing import Any

import httpx
import pytest

from home_ai_cluster.commands import aider_command


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
        assert url == "http://127.0.0.1:25042/v1/chat"
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
        ["--file", "target.py", "request", "--message", "again"],
        ["--file", "target.py", "one", "two"],
        ["--file", "target.py", "   "],
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


def test_positional_and_option_messages_normalize_to_the_same_child_input() -> None:
    positional = aider_command._parse_input(["--file", "target.py", "request"])
    option = aider_command._parse_input(["--file", "target.py", "--message", "request"])

    assert positional == option


def test_aider_rejects_both_message_forms_before_child_or_target_creation(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.py"

    with pytest.raises(SystemExit) as raised:
        aider_command.main(
            ["--file", str(target), "request", "--message", "other"],
            _which=lambda name: pytest.fail("must not find Aider"),
        )

    assert raised.value.code == 2
    assert not target.exists()


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


def test_complete_cycle_uses_private_fail_closed_aider_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.py"
    requests: list[dict[str, Any]] = []
    temporary_paths: list[Path] = []
    child_inputs: list[object] = []
    monkeypatch.setenv("AIDER_YES_ALWAYS", "true")
    monkeypatch.setenv("HAC_AIDER_UNRELATED", "preserved")

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[-1] == "--version":
            return _supported_run(argv, **kwargs)
        base_url = argv[argv.index("--openai-api-base") + 1]
        config_path = Path(argv[argv.index("--config") + 1])
        settings_path = Path(argv[argv.index("--model-settings-file") + 1])
        temporary_paths.extend((config_path, settings_path))
        assert config_path.read_text(encoding="utf-8") == "{}\n"
        assert "edit_format: whole" in settings_path.read_text(encoding="utf-8")
        child_environment = kwargs["env"]
        assert isinstance(child_environment, dict)
        assert "AIDER_YES_ALWAYS" not in child_environment
        assert child_environment["HAC_AIDER_UNRELATED"] == "preserved"
        child_input = kwargs["stdin"]
        assert child_input.read(2) == b"n\n"
        child_inputs.append(child_input)
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
    assert all(child_input.closed for child_input in child_inputs)
    assert not any(
        thread.name == aider_command._AIDER_INPUT_THREAD_NAME
        for thread in threading.enumerate()
    )


def test_private_fail_closed_aider_input_cleans_up_after_subprocess_failure(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.py"
    child_inputs: list[object] = []

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[-1] == "--version":
            return _supported_run(argv, **kwargs)
        child_input = kwargs["stdin"]
        assert child_input.read(2) == b"n\n"
        child_inputs.append(child_input)
        raise subprocess.SubprocessError("simulated child failure")

    with pytest.raises(SystemExit) as raised:
        aider_command.main(
            ["--file", str(target), "--message", "request"],
            _which=lambda name: "/test/aider",
            _run=run,
        )

    assert raised.value.code == 1
    assert all(child_input.closed for child_input in child_inputs)
    assert not any(
        thread.name == aider_command._AIDER_INPUT_THREAD_NAME
        for thread in threading.enumerate()
    )


def test_private_fail_closed_aider_input_cleans_up_without_child_reading_stdin() -> (
    None
):
    child_inputs: list[object] = []

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        child_inputs.append(kwargs["stdin"])
        return subprocess.CompletedProcess(argv, 0)

    completed = aider_command._run_aider_with_automatic_no(
        ["/test/aider"], environment={}, run=run
    )

    assert completed.returncode == 0
    assert all(child_input.closed for child_input in child_inputs)
    assert not any(
        thread.name == aider_command._AIDER_INPUT_THREAD_NAME
        for thread in threading.enumerate()
    )


def test_exclusive_creation_never_truncates_an_appearing_file(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    target.write_text("do not replace", encoding="utf-8")
    assert aider_command._create_missing_target(target)
    assert target.read_text(encoding="utf-8") == "do not replace"


def test_translator_is_loopback_strict_and_projects_one_minimal_response() -> None:
    requests: list[dict[str, Any]] = []
    client_options: list[dict[str, object]] = []

    def create_client(**kwargs: object) -> _NativeClient:
        client_options.append(kwargs)
        return _NativeClient(_response("edited text"), requests)

    translator = aider_command._AiderTranslator(
        timeout_seconds=300.0,
        client_factory=create_client,
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
    assert client_options == [
        {"timeout": 300.0, "follow_redirects": False, "trust_env": False}
    ]
    assert translator.accepted_request_count == translator.native_request_count == 1
    assert translator.projected_response_count == 1
    assert translator.completed is True


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


def test_first_native_failure_blocks_a_second_native_request() -> None:
    requests: list[dict[str, Any]] = []
    translator = aider_command._AiderTranslator(
        timeout_seconds=120.0,
        client_factory=lambda **kwargs: _NativeClient(
            httpx.Response(500, text="native failure"), requests
        ),
    )
    translator.start()
    request = {
        "model": "home-ai-cluster",
        "messages": [{"role": "user", "content": "request"}],
    }
    try:
        assert _post_bridge(translator.base_url, request) == (
            502,
            {"error": "Home AI Cluster request failed"},
        )
        assert _post_bridge(translator.base_url, request) == (
            400,
            {"error": "Home AI Cluster request failed"},
        )
    finally:
        translator.close()
    assert translator.accepted_request_count == translator.native_request_count == 1
    assert translator.projected_response_count == 0
    assert translator.completed is False
    assert translator.failed is True
    assert len(requests) == 1


def test_first_native_failure_makes_zero_exit_aider_invocation_unsuccessful(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.py"
    target.touch()
    requests: list[dict[str, Any]] = []
    translators: list[aider_command._AiderTranslator] = []
    request = {
        "model": "home-ai-cluster",
        "messages": [{"role": "user", "content": "request"}],
    }

    def translator_factory(**kwargs: object) -> aider_command._AiderTranslator:
        translator = aider_command._AiderTranslator(**kwargs)
        translators.append(translator)
        return translator

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[-1] == "--version":
            return _supported_run(argv, **kwargs)
        base_url = argv[argv.index("--openai-api-base") + 1]
        assert _post_bridge(base_url, request)[0] == 502
        assert _post_bridge(base_url, request)[0] == 400
        return subprocess.CompletedProcess(argv, 0)

    with pytest.raises(SystemExit) as raised:
        aider_command.main(
            ["--file", str(target), "--message", "request"],
            _which=lambda name: "/test/aider",
            _run=run,
            _client_factory=lambda **kwargs: _NativeClient(
                httpx.Response(500, text="native failure"), requests
            ),
            _translator_factory=translator_factory,
        )

    assert raised.value.code == 1
    assert len(translators) == 1
    assert (
        translators[0].accepted_request_count
        == translators[0].native_request_count
        == 1
    )
    assert translators[0].completed is False
    assert len(requests) == 1


def test_two_requests_are_independently_translated_by_one_aider_subprocess(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.py"
    requests: list[dict[str, Any]] = []
    translators: list[aider_command._AiderTranslator] = []
    responses = [_response("first result"), _response("second result")]
    calls: list[list[str]] = []
    first_request = {
        "model": "home-ai-cluster",
        "messages": [{"role": "system", "content": "first system"}],
    }
    second_request = {
        "model": "home-ai-cluster",
        "messages": [
            {"role": "assistant", "content": "first result"},
            {"role": "user", "content": "second request"},
        ],
    }

    def translator_factory(**kwargs: object) -> aider_command._AiderTranslator:
        translator = aider_command._AiderTranslator(**kwargs)
        translators.append(translator)
        return translator

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[-1] == "--version":
            return _supported_run(argv, **kwargs)
        calls.append(argv)
        base_url = argv[argv.index("--openai-api-base") + 1]
        first_response = _post_bridge(base_url, first_request)
        assert first_response[0] == 200
        assert first_response[1]["choices"] == [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "first result"},
                "finish_reason": None,
            }
        ]
        second_response = _post_bridge(base_url, second_request)
        assert second_response[0] == 200
        assert second_response[1]["choices"] == [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "second result"},
                "finish_reason": None,
            }
        ]
        return subprocess.CompletedProcess(argv, 0)

    aider_command.main(
        ["--file", str(target), "--message", "request"],
        _which=lambda name: "/test/aider",
        _run=run,
        _client_factory=lambda **kwargs: _NativeClient(responses.pop(0), requests),
        _translator_factory=translator_factory,
    )

    assert len(calls) == 1
    assert len(translators) == 1
    assert translators[0].accepted_request_count == 2
    assert translators[0].native_request_count == 2
    assert translators[0].projected_response_count == 2
    assert translators[0].completed is True
    assert requests == [
        {"messages": first_request["messages"], "capability": "code"},
        {"messages": second_request["messages"], "capability": "code"},
    ]


def test_second_native_failure_makes_zero_exit_aider_invocation_unsuccessful(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.py"
    requests: list[dict[str, Any]] = []
    translators: list[aider_command._AiderTranslator] = []
    responses = [_response("first result"), httpx.Response(500, text="failure")]
    request = {
        "model": "home-ai-cluster",
        "messages": [{"role": "user", "content": "request"}],
    }

    def translator_factory(**kwargs: object) -> aider_command._AiderTranslator:
        translator = aider_command._AiderTranslator(**kwargs)
        translators.append(translator)
        return translator

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[-1] == "--version":
            return _supported_run(argv, **kwargs)
        base_url = argv[argv.index("--openai-api-base") + 1]
        assert _post_bridge(base_url, request)[0] == 200
        assert _post_bridge(base_url, request) == (
            502,
            {"error": "Home AI Cluster request failed"},
        )
        assert _post_bridge(base_url, request) == (
            400,
            {"error": "Home AI Cluster request failed"},
        )
        return subprocess.CompletedProcess(argv, 0)

    with pytest.raises(SystemExit) as raised:
        aider_command.main(
            ["--file", str(target), "--message", "request"],
            _which=lambda name: "/test/aider",
            _run=run,
            _client_factory=lambda **kwargs: _NativeClient(responses.pop(0), requests),
            _translator_factory=translator_factory,
        )

    assert raised.value.code == 1
    assert translators[0].accepted_request_count == 2
    assert translators[0].native_request_count == 2
    assert translators[0].projected_response_count == 1
    assert translators[0].completed is False
    assert len(requests) == 2


def test_third_request_is_rejected_and_makes_zero_exit_unsuccessful(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.py"
    requests: list[dict[str, Any]] = []
    translators: list[aider_command._AiderTranslator] = []
    responses = [_response("first result"), _response("second result")]
    request = {
        "model": "home-ai-cluster",
        "messages": [{"role": "user", "content": "request"}],
    }

    def translator_factory(**kwargs: object) -> aider_command._AiderTranslator:
        translator = aider_command._AiderTranslator(**kwargs)
        translators.append(translator)
        return translator

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[-1] == "--version":
            return _supported_run(argv, **kwargs)
        base_url = argv[argv.index("--openai-api-base") + 1]
        assert _post_bridge(base_url, request)[0] == 200
        assert _post_bridge(base_url, request)[0] == 200
        assert _post_bridge(base_url, request) == (
            400,
            {"error": "Home AI Cluster request failed"},
        )
        return subprocess.CompletedProcess(argv, 0)

    with pytest.raises(SystemExit) as raised:
        aider_command.main(
            ["--file", str(target), "--message", "request"],
            _which=lambda name: "/test/aider",
            _run=run,
            _client_factory=lambda **kwargs: _NativeClient(responses.pop(0), requests),
            _translator_factory=translator_factory,
        )

    assert raised.value.code == 1
    assert translators[0].accepted_request_count == 2
    assert translators[0].native_request_count == 2
    assert translators[0].projected_response_count == 2
    assert translators[0].completed is False
    assert len(requests) == 2


def test_invalid_second_request_makes_zero_exit_aider_invocation_unsuccessful(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.py"
    requests: list[dict[str, Any]] = []
    translators: list[aider_command._AiderTranslator] = []
    request = {
        "model": "home-ai-cluster",
        "messages": [{"role": "user", "content": "request"}],
    }

    def translator_factory(**kwargs: object) -> aider_command._AiderTranslator:
        translator = aider_command._AiderTranslator(**kwargs)
        translators.append(translator)
        return translator

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[-1] == "--version":
            return _supported_run(argv, **kwargs)
        base_url = argv[argv.index("--openai-api-base") + 1]
        assert _post_bridge(base_url, request)[0] == 200
        assert _post_bridge(
            base_url,
            {"model": "home-ai-cluster", "messages": [], "temperature": 0},
        ) == (400, {"error": "Home AI Cluster request failed"})
        return subprocess.CompletedProcess(argv, 0)

    with pytest.raises(SystemExit) as raised:
        aider_command.main(
            ["--file", str(target), "--message", "request"],
            _which=lambda name: "/test/aider",
            _run=run,
            _client_factory=lambda **kwargs: _NativeClient(_response(), requests),
            _translator_factory=translator_factory,
        )

    assert raised.value.code == 1
    assert translators[0].accepted_request_count == 1
    assert translators[0].native_request_count == 1
    assert translators[0].projected_response_count == 1
    assert translators[0].completed is False
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
        "--no-show-model-warnings",
    } <= set(argv)
    assert argv[-4:] == [
        "--file",
        str(command_input.target),
        "--message",
        "private request",
    ]
