"""Native client for one-shot and bounded foreground Chat requests."""

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, TextIO

import httpx
from pydantic import ValidationError

from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
)

_ORDINARY_CHAT_URL = "http://127.0.0.1:8000/v1/chat"
_REQUEST_TIMEOUT_SECONDS = 120.0
_MIN_REQUEST_TIMEOUT_SECONDS = 1
_MAX_REQUEST_TIMEOUT_SECONDS = 3600
_INTERACTIVE_MESSAGE_CONTENT_LIMIT = 65_536

_INVALID_INPUT = "error: invalid request input"
_CLUSTER_UNAVAILABLE = "error: ordinary cluster unavailable"
_ORDINARY_REQUEST_TIMED_OUT = "error: ordinary request timed out"
_CLUSTER_REJECTED = "error: cluster rejected request"
_NO_CAPABILITY = "error: no available chat capability"
_RUNTIME_UNAVAILABLE = "error: runtime adapter unavailable"
_ORDINARY_REQUEST_FAILED = "error: ordinary request failed"
_INVALID_CLUSTER_RESPONSE = "error: invalid cluster response"


class _InvalidRequestInput(Exception):
    """Raised when one command invocation does not have one valid message."""


@dataclass(frozen=True)
class _ChatCommandInput:
    """One validated one-shot message or the no-message interactive mode."""

    message: str | None
    output_mode: str
    timeout_seconds: float


class _ArgumentParser(argparse.ArgumentParser):
    """Convert argparse failures into the RFC-0045 input boundary."""

    def error(self, message: str) -> None:
        raise _InvalidRequestInput from None


def _parse_timeout_seconds(value: str) -> float:
    """Validate one RFC-0060 base-10 integer timeout value."""
    if (
        not value
        or not value.isascii()
        or not value.isdigit()
        or (len(value) > 1 and value.startswith("0"))
    ):
        raise ValueError("invalid timeout seconds")

    seconds = int(value)
    if not _MIN_REQUEST_TIMEOUT_SECONDS <= seconds <= _MAX_REQUEST_TIMEOUT_SECONDS:
        raise ValueError("invalid timeout seconds")
    return float(seconds)


def _parse_input(argv: Sequence[str] | None) -> _ChatCommandInput:
    parser = _ArgumentParser(prog="home-ai-cluster-chat")
    parser.add_argument("message_positional", nargs="?")
    parser.add_argument("--message", action="append")
    parser.add_argument("--timeout-seconds")
    output_options = parser.add_mutually_exclusive_group()
    output_options.add_argument("-v", "--verbose", action="store_true")
    output_options.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    option_messages = args.message or []
    message: str | None = None
    if args.message_positional is not None:
        if option_messages:
            raise _InvalidRequestInput
        message = args.message_positional
    elif len(option_messages) == 1:
        message = option_messages[0]
    elif option_messages:
        raise _InvalidRequestInput

    if args.verbose:
        output_mode = "verbose"
    elif args.json:
        output_mode = "json"
    else:
        output_mode = "content"

    try:
        timeout_seconds = (
            _REQUEST_TIMEOUT_SECONDS
            if args.timeout_seconds is None
            else _parse_timeout_seconds(args.timeout_seconds)
        )
    except ValueError:
        raise _InvalidRequestInput from None

    if message is None:
        if output_mode != "content":
            raise _InvalidRequestInput
    elif not message.strip():
        raise _InvalidRequestInput

    return _ChatCommandInput(
        message=message,
        output_mode=output_mode,
        timeout_seconds=timeout_seconds,
    )


def _native_request(messages: Sequence[ChatMessage]) -> dict[str, Any]:
    request = ClusterRequest(
        messages=list(messages),
        capability=Capability(name="chat"),
    )
    return {
        "messages": [message.model_dump() for message in request.messages],
        "capability": request.capability.name,
    }


def _post_native_request(
    request: dict[str, Any],
    *,
    timeout_seconds: float,
    client_factory: Callable[..., httpx.Client],
) -> httpx.Response:
    with client_factory(
        timeout=timeout_seconds,
        follow_redirects=False,
        trust_env=False,
    ) as client:
        return client.post(_ORDINARY_CHAT_URL, json=request)


def _exit_with_failure(
    message: str, exit_code: int, *, stderr: TextIO | None = None
) -> None:
    stderr = sys.stderr if stderr is None else stderr
    print(message, file=stderr)
    raise SystemExit(exit_code)


def _failure_for_status(status_code: int) -> str | None:
    if 200 <= status_code < 300:
        return None
    if status_code == 422:
        return _CLUSTER_REJECTED
    if status_code == 404:
        return _NO_CAPABILITY
    if status_code == 503:
        return _RUNTIME_UNAVAILABLE
    return _ORDINARY_REQUEST_FAILED


def _write_content(content: str, *, stdout: TextIO | None = None) -> None:
    """Write generated content with the RFC-0049 terminal newline rule."""
    stdout = sys.stdout if stdout is None else stdout
    stdout.write(content)
    if not content.endswith("\n"):
        stdout.write("\n")


def _write_verbose_result(
    result: ClusterResult, *, stdout: TextIO | None = None
) -> None:
    """Write one RFC-0049 human-readable result without changing content."""
    stdout = sys.stdout if stdout is None else stdout
    stdout.write("Response:\n")
    stdout.write(result.content)

    if not result.content:
        separator = "\n"
    elif result.content.endswith("\n\n"):
        separator = ""
    elif result.content.endswith("\n"):
        separator = "\n"
    else:
        separator = "\n\n"

    stdout.write(separator)
    stdout.write("Execution:\n")
    stdout.write(f"  Node: {result.node_id}\n")
    stdout.write(f"  Adapter: {result.adapter}\n")
    if result.model:
        stdout.write(f"  Model: {result.model}\n")


def _write_success(
    result: ClusterResult, output_mode: str, *, stdout: TextIO | None = None
) -> None:
    """Select one RFC-0049 presentation for an already validated result."""
    stdout = sys.stdout if stdout is None else stdout
    if output_mode == "content":
        _write_content(result.content, stdout=stdout)
    elif output_mode == "verbose":
        _write_verbose_result(result, stdout=stdout)
    else:
        print(json.dumps(result.model_dump(), separators=(",", ":")), file=stdout)


def _send_native_request(
    messages: Sequence[ChatMessage],
    *,
    timeout_seconds: float,
    client_factory: Callable[..., httpx.Client],
) -> tuple[ClusterResult | None, str | None]:
    """Send one request and return a safe failure instead of exiting the process."""
    try:
        response = _post_native_request(
            _native_request(messages),
            timeout_seconds=timeout_seconds,
            client_factory=client_factory,
        )
    except httpx.ConnectError:
        return None, _CLUSTER_UNAVAILABLE
    except httpx.TimeoutException:
        return None, _ORDINARY_REQUEST_TIMED_OUT
    except httpx.RequestError:
        return None, _ORDINARY_REQUEST_FAILED
    except Exception:
        return None, _ORDINARY_REQUEST_FAILED

    failure = _failure_for_status(response.status_code)
    if failure is not None:
        return None, failure

    try:
        return ClusterResult.model_validate(response.json()), None
    except (ValidationError, ValueError):
        return None, _INVALID_CLUSTER_RESPONSE
    except Exception:
        return None, _ORDINARY_REQUEST_FAILED


def _aggregate_content_size(messages: Sequence[ChatMessage]) -> int:
    return sum(len(message.content.encode("utf-8")) for message in messages)


def _run_interactive(
    *,
    timeout_seconds: float,
    client_factory: Callable[..., httpx.Client],
    stdin: TextIO,
    stdout: TextIO,
    stderr: TextIO,
) -> None:
    """Run one process-owned terminal Chat conversation until EOF or Ctrl-C."""
    retained_messages: list[ChatMessage] = []
    try:
        while True:
            stdout.write("> ")
            stdout.flush()
            submitted = stdin.readline()
            if submitted == "":
                return
            message = submitted.rstrip("\r\n")
            if not message.strip():
                continue

            candidate = [*retained_messages, ChatMessage(role="user", content=message)]
            if _aggregate_content_size(candidate) > _INTERACTIVE_MESSAGE_CONTENT_LIMIT:
                print(_INVALID_INPUT, file=stderr)
                continue

            result, failure = _send_native_request(
                candidate,
                timeout_seconds=timeout_seconds,
                client_factory=client_factory,
            )
            if failure is not None:
                print(failure, file=stderr)
                continue

            assert result is not None
            if not result.content:
                print(_INVALID_CLUSTER_RESPONSE, file=stderr)
                continue
            retained_messages = [
                *candidate,
                ChatMessage(role="assistant", content=result.content),
            ]
            _write_content(result.content, stdout=stdout)
    except KeyboardInterrupt:
        return


def main(
    argv: Sequence[str] | None = None,
    *,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
    _stdin: TextIO | None = None,
    _stdout: TextIO | None = None,
    _stderr: TextIO | None = None,
) -> None:
    """Send one request or run the accepted TTY-only foreground lifecycle."""
    stdin = sys.stdin if _stdin is None else _stdin
    stdout = sys.stdout if _stdout is None else _stdout
    stderr = sys.stderr if _stderr is None else _stderr
    try:
        command_input = _parse_input(argv)
    except _InvalidRequestInput:
        _exit_with_failure(_INVALID_INPUT, 2, stderr=stderr)

    if command_input.message is None:
        if not stdin.isatty() or not stdout.isatty():
            _exit_with_failure(_INVALID_INPUT, 2, stderr=stderr)
        _run_interactive(
            timeout_seconds=command_input.timeout_seconds,
            client_factory=_client_factory,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )
        return

    result, failure = _send_native_request(
        [ChatMessage(role="user", content=command_input.message)],
        timeout_seconds=command_input.timeout_seconds,
        client_factory=_client_factory,
    )
    if failure is not None:
        _exit_with_failure(failure, 1, stderr=stderr)
    assert result is not None
    _write_success(result, command_input.output_mode, stdout=stdout)
