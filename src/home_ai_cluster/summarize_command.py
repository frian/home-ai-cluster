"""One-shot client for the ordinary Home AI Cluster summarize endpoint."""

import argparse
import os
import stat
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, BinaryIO

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
    _parse_timeout_seconds,
    _write_success,
)
from home_ai_cluster.core.models import ClusterResult, SummarizeRequest

_ORDINARY_SUMMARIZE_URL = "http://127.0.0.1:8000/v1/summarize"
_NO_CAPABILITY = "error: no available summarize capability"
_MAX_SOURCE_BYTES = 65_537


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
    timeout_seconds: float


def _read_bounded_utf8_source(source_input: BinaryIO) -> str:
    """Read one bounded UTF-8 byte source without retaining excess bytes."""
    source = bytearray()
    while len(source) < _MAX_SOURCE_BYTES:
        remaining = _MAX_SOURCE_BYTES - len(source)
        try:
            chunk = source_input.read(remaining)
        except Exception:
            raise _InvalidRequestInput from None
        if not chunk:
            break
        source.extend(chunk[:remaining])
        if len(chunk) > remaining:
            break

    if len(source) > _MAX_SOURCE_BYTES - 1:
        raise _InvalidRequestInput

    try:
        return bytes(source).decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise _InvalidRequestInput from None


def _read_bounded_file(
    path: str,
    *,
    file_opener: Callable[[str, str], BinaryIO],
) -> str:
    """Read one regular file through the bounded UTF-8 source boundary."""
    try:
        if not stat.S_ISREG(os.stat(path).st_mode):
            raise _InvalidRequestInput
        with file_opener(path, "rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise _InvalidRequestInput
            return _read_bounded_utf8_source(source)
    except _InvalidRequestInput:
        raise
    except Exception:
        raise _InvalidRequestInput from None


def _parse_input(
    argv: Sequence[str] | None,
    *,
    stdin: BinaryIO | None = None,
    file_opener: Callable[[str, str], BinaryIO] = open,
) -> _SummarizeCommandInput:
    parser = _ArgumentParser(prog="home-ai-cluster summarize")
    source_options = parser.add_mutually_exclusive_group()
    source_options.add_argument("--text", action="append")
    source_options.add_argument("--file", action="append")
    parser.add_argument("--timeout-seconds")
    output_options = parser.add_mutually_exclusive_group()
    output_options.add_argument("-v", "--verbose", action="store_true")
    output_options.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    texts = args.text or []
    files = args.file or []
    if len(texts) > 1 or len(files) > 1:
        raise _InvalidRequestInput
    if texts:
        text = texts[0]
    elif files:
        text = _read_bounded_file(files[0], file_opener=file_opener)
    else:
        text = _read_bounded_utf8_source(sys.stdin.buffer if stdin is None else stdin)

    try:
        request = SummarizeRequest(text=text)
    except ValidationError:
        raise _InvalidRequestInput from None

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
    return _SummarizeCommandInput(
        request=request,
        output_mode=output_mode,
        timeout_seconds=timeout_seconds,
    )


def _native_request(request: SummarizeRequest) -> dict[str, Any]:
    """Serialize only the accepted public summarize body from its model."""
    return request.model_dump(include={"text"})


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
    _stdin: BinaryIO | None = None,
    _file_opener: Callable[[str, str], BinaryIO] = open,
) -> None:
    """Send one native summarize request and emit one result or safe failure."""
    try:
        command_input = _parse_input(
            argv,
            stdin=_stdin,
            file_opener=_file_opener,
        )
    except _InvalidRequestInput:
        _exit_with_failure(_INVALID_INPUT, 2)

    try:
        response = _post_native_request(
            _native_request(command_input.request),
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
