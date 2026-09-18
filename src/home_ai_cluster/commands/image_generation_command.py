"""One-shot client for the ordinary local Image Generation endpoint."""

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import BinaryIO, TextIO

import httpx
from pydantic import ValidationError

from home_ai_cluster.commands.chat_command import (
    _CLUSTER_REJECTED,
    _CLUSTER_UNAVAILABLE,
    _INVALID_INPUT,
    _ORDINARY_REQUEST_FAILED,
    _ORDINARY_REQUEST_TIMED_OUT,
    _REQUEST_TIMEOUT_SECONDS,
    _RUNTIME_UNAVAILABLE,
    _parse_timeout_seconds,
)
from home_ai_cluster.core.models import ImageGenerationRequest
from home_ai_cluster.core.png_validation import (
    MAX_ENCODED_PNG_BYTES,
    validate_still_png,
)

_ORDINARY_IMAGE_GENERATION_URL = "http://127.0.0.1:25042/v1/image-generation"
_NO_CAPABILITY = "error: no available image-generation capability"
_INVALID_CLUSTER_RESPONSE = "error: invalid image generation response"
_TTY_STDOUT = "error: image generation requires non-TTY stdout"
_STDOUT_WRITE_FAILED = "error: image generation stdout write failed"


class _InvalidRequestInput(Exception):
    """Raised when one invocation does not contain exactly one instruction."""


class _ArgumentParser(argparse.ArgumentParser):
    """Convert parser failures into the ordinary local input boundary."""

    def error(self, message: str) -> None:
        raise _InvalidRequestInput from None


@dataclass(frozen=True)
class _ImageGenerationCommandInput:
    request: ImageGenerationRequest
    timeout_seconds: float


def _parse_input(argv: Sequence[str] | None) -> _ImageGenerationCommandInput:
    parser = _ArgumentParser(
        prog="home-ai-cluster image-generation",
        description="Send one local Image Generation request to ordinary HAC.",
    )
    parser.add_argument("instruction", metavar="INSTRUCTION")
    parser.add_argument("--width", metavar="PIXELS")
    parser.add_argument("--height", metavar="PIXELS")
    parser.add_argument(
        "--timeout-seconds", help="Native HAC request timeout in seconds."
    )
    args = parser.parse_args(argv)
    try:
        dimensions = {}
        if args.width is not None:
            dimensions["width"] = int(args.width)
        if args.height is not None:
            dimensions["height"] = int(args.height)
        request = ImageGenerationRequest(instruction=args.instruction, **dimensions)
        timeout_seconds = (
            _REQUEST_TIMEOUT_SECONDS
            if args.timeout_seconds is None
            else _parse_timeout_seconds(args.timeout_seconds)
        )
    except (ValidationError, ValueError):
        raise _InvalidRequestInput from None
    return _ImageGenerationCommandInput(request, timeout_seconds)


def _failure_for_status(status_code: int) -> str | None:
    if 200 <= status_code < 300:
        return None
    if status_code == 422:
        return _CLUSTER_REJECTED
    if status_code == 404:
        return _NO_CAPABILITY
    if status_code == 409:
        return "error: execution permission denied"
    if status_code == 503:
        return _RUNTIME_UNAVAILABLE
    return _ORDINARY_REQUEST_FAILED


def _fail(message: str, exit_code: int, stderr: TextIO) -> None:
    print(message, file=stderr)
    raise SystemExit(exit_code)


def _acquire_png(
    response: httpx.Response,
    *,
    maximum_bytes: int = MAX_ENCODED_PNG_BYTES,
) -> bytes:
    """Acquire one native PNG without buffering beyond its accepted bound."""
    if response.headers.get("content-type") != "image/png":
        raise ValueError("unexpected response media type")
    if response.headers.get("content-encoding") not in (None, "identity"):
        raise ValueError("unexpected response content encoding")
    body = bytearray()
    for chunk in response.iter_raw():
        if len(body) + len(chunk) > maximum_bytes:
            raise ValueError("encoded PNG exceeds accepted bound")
        body.extend(chunk)
    return validate_still_png(bytes(body))


def _write_png(stdout: BinaryIO, png: bytes) -> None:
    """Submit one established PNG completely, including its observable flush."""
    remaining = memoryview(png)
    while remaining:
        written = stdout.write(remaining)
        if (
            not isinstance(written, int)
            or isinstance(written, bool)
            or written <= 0
            or written > len(remaining)
        ):
            raise OSError("stdout sink did not make progress")
        remaining = remaining[written:]
    stdout.flush()


def main(
    argv: Sequence[str] | None = None,
    *,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
    _stdout: BinaryIO | None = None,
    _stderr: TextIO | None = None,
) -> None:
    """Send once, validate the complete PNG, and write it only to non-TTY stdout."""
    stdout = sys.stdout.buffer if _stdout is None else _stdout
    stderr = sys.stderr if _stderr is None else _stderr
    try:
        command = _parse_input(argv)
    except _InvalidRequestInput:
        _fail(_INVALID_INPUT, 2, stderr)

    if stdout.isatty():
        _fail(_TTY_STDOUT, 1, stderr)

    try:
        with _client_factory(
            timeout=command.timeout_seconds,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            with client.stream(
                "POST",
                _ORDINARY_IMAGE_GENERATION_URL,
                json=command.request.model_dump(exclude_none=True),
            ) as response:
                failure = _failure_for_status(response.status_code)
                if failure is not None:
                    _fail(failure, 1, stderr)
                try:
                    png = _acquire_png(response)
                except httpx.RequestError:
                    raise
                except Exception:
                    _fail(_INVALID_CLUSTER_RESPONSE, 1, stderr)
    except httpx.ConnectError:
        _fail(_CLUSTER_UNAVAILABLE, 1, stderr)
    except httpx.TimeoutException:
        _fail(_ORDINARY_REQUEST_TIMED_OUT, 1, stderr)
    except httpx.RequestError:
        _fail(_ORDINARY_REQUEST_FAILED, 1, stderr)
    except Exception:
        _fail(_ORDINARY_REQUEST_FAILED, 1, stderr)

    try:
        _write_png(stdout, png)
    except Exception:
        _fail(_STDOUT_WRITE_FAILED, 1, stderr)
