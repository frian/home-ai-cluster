"""One-shot client for the ordinary Home AI Cluster summarize endpoint."""

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import ValidationError

from home_ai_cluster.chat_command import (
    _CLUSTER_REJECTED,
    _CLUSTER_UNAVAILABLE,
    _INVALID_CLUSTER_RESPONSE,
    _INVALID_INPUT,
    _ORDINARY_REQUEST_FAILED,
    _ORDINARY_REQUEST_TIMED_OUT,
    _REQUEST_TIMEOUT_SECONDS,
    _RUNTIME_UNAVAILABLE,
    _exit_with_failure,
    _write_success,
)
from home_ai_cluster.core.models import ClusterResult, SummarizeRequest

_ORDINARY_SUMMARIZE_URL = "http://127.0.0.1:8000/v1/summarize"
_NO_CAPABILITY = "error: no available summarize capability"


class _InvalidRequestInput(Exception):
    """Raised when one invocation does not contain one valid source text."""


class _ArgumentParser(argparse.ArgumentParser):
    """Convert parser failures into the RFC-0054 input boundary."""

    def error(self, message: str) -> None:
        raise _InvalidRequestInput from None


@dataclass(frozen=True)
class _SummarizeCommandInput:
    """One validated source text and its selected success presentation."""

    request: SummarizeRequest
    output_mode: str


def _parse_input(argv: Sequence[str] | None) -> _SummarizeCommandInput:
    parser = _ArgumentParser(prog="home-ai-cluster summarize")
    parser.add_argument("--text", action="append")
    output_options = parser.add_mutually_exclusive_group()
    output_options.add_argument("-v", "--verbose", action="store_true")
    output_options.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    texts = args.text or []
    if len(texts) != 1:
        raise _InvalidRequestInput

    try:
        request = SummarizeRequest(text=texts[0])
    except ValidationError:
        raise _InvalidRequestInput from None

    if args.verbose:
        output_mode = "verbose"
    elif args.json:
        output_mode = "json"
    else:
        output_mode = "content"

    return _SummarizeCommandInput(request=request, output_mode=output_mode)


def _native_request(request: SummarizeRequest) -> dict[str, Any]:
    """Serialize only the accepted public summarize body from its model."""
    return request.model_dump(include={"text"})


def _post_native_request(
    request: dict[str, Any],
    *,
    client_factory: Callable[..., httpx.Client],
) -> httpx.Response:
    with client_factory(
        timeout=_REQUEST_TIMEOUT_SECONDS,
        follow_redirects=False,
    ) as client:
        return client.post(_ORDINARY_SUMMARIZE_URL, json=request)


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
    """Send one native summarize request and emit one result or safe failure."""
    try:
        command_input = _parse_input(argv)
    except _InvalidRequestInput:
        _exit_with_failure(_INVALID_INPUT, 2)

    try:
        response = _post_native_request(
            _native_request(command_input.request),
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
