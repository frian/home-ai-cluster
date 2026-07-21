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
_REQUEST_TIMEOUT_SECONDS = 30.0

_INVALID_INPUT = "error: invalid request input"
_CLUSTER_UNAVAILABLE = "error: ordinary cluster unavailable"
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


class _ArgumentParser(argparse.ArgumentParser):
    """Convert argparse failures into the RFC-0045 input boundary."""

    def error(self, message: str) -> None:
        raise _InvalidRequestInput from None


def _parse_input(argv: Sequence[str] | None) -> _ChatCommandInput:
    parser = _ArgumentParser(prog="home-ai-cluster-chat")
    parser.add_argument("--message", action="append", required=True)
    output_options = parser.add_mutually_exclusive_group()
    output_options.add_argument("-v", "--verbose", action="store_true")
    output_options.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if len(args.message) != 1 or not args.message[0].strip():
        raise _InvalidRequestInput

    if args.verbose:
        output_mode = "verbose"
    elif args.json:
        output_mode = "json"
    else:
        output_mode = "content"

    return _ChatCommandInput(message=args.message[0], output_mode=output_mode)


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
    client_factory: Callable[..., httpx.Client],
) -> httpx.Response:
    with client_factory(
        timeout=_REQUEST_TIMEOUT_SECONDS,
        follow_redirects=False,
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
            client_factory=_client_factory,
        )
    except (httpx.ConnectError, httpx.TimeoutException):
        _exit_with_failure(_CLUSTER_UNAVAILABLE, 1)
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
