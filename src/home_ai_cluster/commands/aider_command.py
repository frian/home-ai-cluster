"""Bounded Aider caller edge accepted by RFC-0068, RFC-0069, and RFC-0072."""

import argparse
import http.client
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import httpx
from pydantic import ValidationError

from home_ai_cluster.commands import chat_command
from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
)

_AIDER_VERSION = "0.86.2"
_AIDER_MODEL = "openai/home-ai-cluster"
_AIDER_ENDPOINT_MODEL = "home-ai-cluster"
_NATIVE_CHAT_URL = "http://127.0.0.1:25042/v1/chat"
_BRIDGE_FAILURE = "Home AI Cluster request failed"
_AIDER_FAILURE = "error: Aider caller edge failed"
_AIDER_PREREQUISITE_FAILURE = "error: Aider 0.86.2 is required"
_TARGET_FAILURE = "error: invalid Aider target"

# Suppress Aider config discovery without setting confirmation behavior.
_AIDER_CONFIG = "{}\n"
_AIDER_MODEL_SETTINGS = """- name: openai/home-ai-cluster
  edit_format: whole
  use_temperature: false
"""
_AIDER_INPUT_THREAD_NAME = "home-ai-cluster-aider-no-input"


class _ArgumentParser(argparse.ArgumentParser):
    """Keep the command's input failure boundary small and consistent."""

    def error(self, message: str) -> None:
        raise chat_command._InvalidRequestInput from None


@dataclass(frozen=True)
class _AiderCommandInput:
    target: Path
    message: str
    timeout_seconds: float


def _parse_input(argv: Sequence[str] | None) -> _AiderCommandInput:
    parser = _ArgumentParser(
        prog="home-ai-cluster aider",
        description="Run one bounded Aider caller edge for one selected file.",
    )
    parser.add_argument(
        "-f", "--file", action="append", help="Exactly one target file to edit."
    )
    parser.add_argument(
        "message_positional",
        nargs="?",
        metavar="MESSAGE",
        help="One Aider edit request.",
    )
    parser.add_argument(
        "--message", action="append", help="One Aider edit request, instead of MESSAGE."
    )
    parser.add_argument(
        "--timeout-seconds", help="Native HAC request timeout in seconds."
    )
    args = parser.parse_args(argv)

    files = args.file or []
    option_messages = args.message or []
    if args.message_positional is not None:
        if option_messages:
            raise chat_command._InvalidRequestInput
        message = args.message_positional
    elif len(option_messages) == 1:
        message = option_messages[0]
    else:
        raise chat_command._InvalidRequestInput

    if len(files) != 1 or not message.strip():
        raise chat_command._InvalidRequestInput

    try:
        timeout_seconds = (
            chat_command._REQUEST_TIMEOUT_SECONDS
            if args.timeout_seconds is None
            else chat_command._parse_timeout_seconds(args.timeout_seconds)
        )
    except ValueError:
        raise chat_command._InvalidRequestInput from None

    return _AiderCommandInput(Path(files[0]), message, timeout_seconds)


def _validate_target(target: Path) -> bool:
    """Validate only target identity and parent existence, never its contents."""
    if target.exists():
        return target.is_file()
    return target.parent.exists() and target.parent.is_dir()


def _aider_is_supported(
    executable: str,
    *,
    run: Callable[..., subprocess.CompletedProcess[str]],
) -> bool:
    try:
        completed = run(
            [executable, "--version"],
            capture_output=True,
            check=False,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if completed.returncode != 0:
        return False
    return completed.stdout.strip() == f"aider {_AIDER_VERSION}"


def _create_missing_target(target: Path) -> bool:
    """Create exactly the named missing leaf without truncating any path."""
    try:
        with target.open("x", encoding="utf-8"):
            pass
    except FileExistsError:
        return target.is_file()
    except OSError:
        return False
    return True


def _native_request(messages: list[dict[str, str]]) -> dict[str, Any]:
    request = ClusterRequest(
        messages=[ChatMessage(**message) for message in messages],
        capability=Capability(name="code"),
    )
    return {
        "messages": [message.model_dump() for message in request.messages],
        "capability": request.capability.name,
    }


def _valid_aider_request(body: object) -> list[dict[str, str]] | None:
    if not isinstance(body, dict) or set(body) not in (
        {"model", "messages"},
        {"model", "messages", "stream"},
    ):
        return None
    if body.get("model") != _AIDER_ENDPOINT_MODEL:
        return None
    if "stream" in body and body["stream"] is not False:
        return None
    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        return None
    accepted: list[dict[str, str]] = []
    for message in messages:
        if (
            not isinstance(message, dict)
            or set(message) != {"role", "content"}
            or message.get("role") not in {"system", "user", "assistant"}
            or not isinstance(message.get("content"), str)
            or not message["content"]
        ):
            return None
        accepted.append({"role": message["role"], "content": message["content"]})
    return accepted


class _AiderTranslator:
    """Private sequential two-request loopback translator for one Aider child."""

    def __init__(
        self,
        *,
        timeout_seconds: float,
        client_factory: Callable[..., httpx.Client],
        server_factory: Callable[..., HTTPServer] = HTTPServer,
    ) -> None:
        self.accepted_request_count = 0
        self.native_request_count = 0
        self.projected_response_count = 0
        self.failed = False
        self._timeout_seconds = timeout_seconds
        self._client_factory = client_factory
        self._server = server_factory(("127.0.0.1", 0), self._handler_type())
        self._thread = threading.Thread(target=self._server.serve_forever)
        self._started = False

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}/v1"

    @property
    def completed(self) -> bool:
        """Report only a successful, complete bounded child interaction."""
        return (
            not self.failed
            and self.accepted_request_count > 0
            and self.projected_response_count == self.accepted_request_count
        )

    def start(self) -> None:
        self._thread.start()
        self._started = True

    def close(self) -> None:
        if self._started:
            self._server.shutdown()
            self._thread.join()
        self._server.server_close()

    def _handler_type(self) -> type[BaseHTTPRequestHandler]:
        translator = self

        class _Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                return

            def _write_json(self, status: int, body: dict[str, Any]) -> None:
                payload = json.dumps(body).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def _fail(self, status: int) -> None:
                translator.failed = True
                self._write_json(status, {"error": _BRIDGE_FAILURE})

            def do_POST(self) -> None:  # noqa: N802
                if self.path != "/v1/chat/completions":
                    self._fail(404)
                    return
                authorization = self.headers.get("Authorization")
                if authorization is not None and (
                    not authorization.startswith("Bearer ")
                    or len(authorization) == len("Bearer ")
                ):
                    self._fail(400)
                    return
                try:
                    length = int(self.headers.get("Content-Length", ""))
                    body = json.loads(self.rfile.read(length))
                except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
                    self._fail(400)
                    return
                messages = _valid_aider_request(body)
                if (
                    messages is None
                    or translator.failed
                    or translator.accepted_request_count >= 2
                    or translator.accepted_request_count
                    != translator.projected_response_count
                ):
                    self._fail(400)
                    return
                translator.accepted_request_count += 1
                try:
                    request = _native_request(messages)
                    translator.native_request_count += 1
                    with translator._client_factory(
                        timeout=translator._timeout_seconds,
                        follow_redirects=False,
                        trust_env=False,
                    ) as client:
                        response = client.post(_NATIVE_CHAT_URL, json=request)
                    if not 200 <= response.status_code < 300:
                        raise ValueError("native request failed")
                    result = ClusterResult.model_validate(response.json())
                except (
                    http.client.HTTPException,
                    httpx.HTTPError,
                    ValidationError,
                    ValueError,
                    OSError,
                ):
                    self._fail(502)
                    return
                self._write_json(
                    200,
                    {
                        "id": f"hac-aider-{uuid.uuid4()}",
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": _AIDER_ENDPOINT_MODEL,
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": result.content,
                                },
                                "finish_reason": None,
                            }
                        ],
                    },
                )
                translator.projected_response_count += 1

        return _Handler


def _aider_argv(
    executable: str,
    command_input: _AiderCommandInput,
    *,
    base_url: str,
    config_path: Path,
    model_settings_path: Path,
) -> list[str]:
    return [
        executable,
        "--model",
        _AIDER_MODEL,
        "--openai-api-base",
        base_url,
        "--openai-api-key",
        "ignored-loopback-placeholder",
        "--model-settings-file",
        str(model_settings_path),
        "--no-stream",
        "--no-analytics",
        "--no-check-update",
        "--no-show-release-notes",
        "--no-show-model-warnings",
        "--no-cache-prompts",
        "--input-history-file",
        os.devnull,
        "--chat-history-file",
        os.devnull,
        "--llm-history-file",
        os.devnull,
        "--env-file",
        os.devnull,
        "--config",
        str(config_path),
        "--no-git",
        "--no-gitignore",
        "--no-auto-commits",
        "--no-auto-lint",
        "--no-auto-test",
        "--no-watch-files",
        "--no-suggest-shell-commands",
        "--no-detect-urls",
        "--no-gui",
        "--no-copy-paste",
        "--disable-playwright",
        "--no-notifications",
        "--file",
        str(command_input.target),
        "--message",
        command_input.message,
    ]


def _run_aider_with_automatic_no(
    argv: list[str],
    *,
    environment: dict[str, str],
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    """Run the fixed Aider child with a private, continuously available No input."""
    read_fd, write_fd = os.pipe()
    child_input = os.fdopen(read_fd, "rb", buffering=0)
    stopped = threading.Event()

    def write_no() -> None:
        try:
            while not stopped.is_set():
                os.write(write_fd, b"n\n")
        except (BrokenPipeError, OSError):
            return
        finally:
            os.close(write_fd)

    writer = threading.Thread(
        target=write_no,
        name=_AIDER_INPUT_THREAD_NAME,
        daemon=False,
    )
    writer.start()
    try:
        return run(argv, check=False, env=environment, stdin=child_input)
    finally:
        stopped.set()
        try:
            child_input.close()
        finally:
            writer.join()


def main(
    argv: Sequence[str] | None = None,
    *,
    _which: Callable[[str], str | None] = shutil.which,
    _run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
    _translator_factory: Callable[..., _AiderTranslator] = _AiderTranslator,
    _temporary_directory: Callable[..., tempfile.TemporaryDirectory[str]] = (
        tempfile.TemporaryDirectory
    ),
) -> None:
    """Run one fixed Aider invocation with at most two translated requests."""
    try:
        command_input = _parse_input(argv)
    except chat_command._InvalidRequestInput:
        chat_command._exit_with_failure(chat_command._INVALID_INPUT, 2)
    if not _validate_target(command_input.target):
        chat_command._exit_with_failure(_TARGET_FAILURE, 2)

    executable = _which("aider")
    if executable is None or not _aider_is_supported(executable, run=_run):
        chat_command._exit_with_failure(_AIDER_PREREQUISITE_FAILURE, 1)
    if command_input.target.exists():
        if not command_input.target.is_file():
            chat_command._exit_with_failure(_TARGET_FAILURE, 1)
    elif not _create_missing_target(command_input.target):
        chat_command._exit_with_failure(_TARGET_FAILURE, 1)

    try:
        with _temporary_directory(prefix="home-ai-cluster-aider-") as temporary:
            temporary_path = Path(temporary)
            config_path = temporary_path / "aider.conf.yml"
            model_settings_path = temporary_path / "model-settings.yml"
            config_path.write_text(_AIDER_CONFIG, encoding="utf-8")
            model_settings_path.write_text(_AIDER_MODEL_SETTINGS, encoding="utf-8")
            child_environment = os.environ.copy()
            child_environment.pop("AIDER_YES_ALWAYS", None)
            translator = _translator_factory(
                timeout_seconds=command_input.timeout_seconds,
                client_factory=_client_factory,
            )
            try:
                translator.start()
                completed = _run_aider_with_automatic_no(
                    _aider_argv(
                        executable,
                        command_input,
                        base_url=translator.base_url,
                        config_path=config_path,
                        model_settings_path=model_settings_path,
                    ),
                    environment=child_environment,
                    run=_run,
                )
            finally:
                translator.close()
    except (OSError, subprocess.SubprocessError):
        chat_command._exit_with_failure(_AIDER_FAILURE, 1)

    if completed.returncode != 0 or not translator.completed:
        chat_command._exit_with_failure(_AIDER_FAILURE, 1)
