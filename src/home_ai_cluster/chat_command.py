"""One-shot client for the ordinary Home AI Cluster chat endpoint."""

import argparse
import json
import sys
from collections.abc import Callable, Sequence
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


class _ArgumentParser(argparse.ArgumentParser):
    """Convert argparse failures into the RFC-0045 input boundary."""

    def error(self, message: str) -> None:
        raise _InvalidRequestInput from None


def _parse_message(argv: Sequence[str] | None) -> str:
    parser = _ArgumentParser(prog="home-ai-cluster-chat")
    parser.add_argument("--message", action="append", required=True)
    args = parser.parse_args(argv)

    if len(args.message) != 1 or not args.message[0].strip():
        raise _InvalidRequestInput

    return args.message[0]


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


def main(
    argv: Sequence[str] | None = None,
    *,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
) -> None:
    """Send one native chat request and emit one normalized result or failure."""
    try:
        message = _parse_message(argv)
    except _InvalidRequestInput:
        _exit_with_failure(_INVALID_INPUT, 2)

    try:
        response = _post_native_request(
            _native_request(message),
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

    print(json.dumps(result.model_dump(), separators=(",", ":")))
