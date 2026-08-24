"""One-shot client for the ordinary Home AI Cluster chat endpoint."""

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

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
    """One validated message and its selected success presentation."""

    message: str
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
    if args.message_positional is not None:
        if option_messages:
            raise _InvalidRequestInput
        message = args.message_positional
    elif len(option_messages) == 1:
        message = option_messages[0]
    else:
        raise _InvalidRequestInput

    if not message.strip():
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
    return _ChatCommandInput(
        message=message,
        output_mode=output_mode,
        timeout_seconds=timeout_seconds,
    )


def _native_request(message: str) -> dict[str, Any]:
    request = ClusterRequest(
        messages=[ChatMessage(role="user", content=message)],
        capability=Capability(name="chat"),
    )
    return {
        "messages": [request.messages[0].model_dump()],
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


def _exit_with_failure(message: str, exit_code: int) -> None:
    print(message, file=sys.stderr)
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


def _write_content(content: str) -> None:
    """Write generated content with the RFC-0049 terminal newline rule."""
    sys.stdout.write(content)
    if not content.endswith("\n"):
        sys.stdout.write("\n")


def _write_verbose_result(result: ClusterResult) -> None:
    """Write one RFC-0049 human-readable result without changing content."""
    sys.stdout.write("Response:\n")
    sys.stdout.write(result.content)

    if not result.content:
        separator = "\n"
    elif result.content.endswith("\n\n"):
        separator = ""
    elif result.content.endswith("\n"):
        separator = "\n"
    else:
        separator = "\n\n"

    sys.stdout.write(separator)
    sys.stdout.write("Execution:\n")
    sys.stdout.write(f"  Node: {result.node_id}\n")
    sys.stdout.write(f"  Adapter: {result.adapter}\n")
    if result.model:
        sys.stdout.write(f"  Model: {result.model}\n")


def _write_success(result: ClusterResult, output_mode: str) -> None:
    """Select one RFC-0049 presentation for an already validated result."""
    if output_mode == "content":
        _write_content(result.content)
    elif output_mode == "verbose":
        _write_verbose_result(result)
    else:
        print(json.dumps(result.model_dump(), separators=(",", ":")))


def main(
    argv: Sequence[str] | None = None,
    *,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
) -> None:
    """Send one native chat request and emit one normalized result or failure."""
    try:
        command_input = _parse_input(argv)
    except _InvalidRequestInput:
        _exit_with_failure(_INVALID_INPUT, 2)

    try:
        response = _post_native_request(
            _native_request(command_input.message),
            timeout_seconds=command_input.timeout_seconds,
            client_factory=_client_factory,
        )
    except httpx.ConnectError:
        _exit_with_failure(_CLUSTER_UNAVAILABLE, 1)
    except httpx.TimeoutException:
        _exit_with_failure(_ORDINARY_REQUEST_TIMED_OUT, 1)
    except httpx.RequestError:
        _exit_with_failure(_ORDINARY_REQUEST_FAILED, 1)
    except Exception:
        _exit_with_failure(_ORDINARY_REQUEST_FAILED, 1)

    failure = _failure_for_status(response.status_code)
    if failure is not None:
        _exit_with_failure(failure, 1)

    try:
        result = ClusterResult.model_validate(response.json())
    except (ValidationError, ValueError):
        _exit_with_failure(_INVALID_CLUSTER_RESPONSE, 1)
    except Exception:
        _exit_with_failure(_ORDINARY_REQUEST_FAILED, 1)

    _write_success(result, command_input.output_mode)
