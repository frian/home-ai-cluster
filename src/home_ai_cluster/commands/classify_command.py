"""One-shot client for the ordinary Home AI Cluster classify endpoint."""

import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import BinaryIO

import httpx
from pydantic import ValidationError

from home_ai_cluster.commands.chat_command import (
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
)
from home_ai_cluster.commands.summarize_command import (
    _ArgumentParser,
    _InvalidRequestInput,
    _read_bounded_file,
    _read_bounded_utf8_source,
)
from home_ai_cluster.core.models import ClassifyRequest, ClassifyResult

_ORDINARY_CLASSIFY_URL = "http://127.0.0.1:25042/v1/classify"
_NO_CAPABILITY = "error: no available classify capability"


@dataclass(frozen=True)
class _ClassifyCommandInput:
    request: ClassifyRequest
    output_mode: str
    timeout_seconds: float


def _parse_input(
    argv: Sequence[str] | None,
    *,
    stdin: BinaryIO | None = None,
    file_opener: Callable[[str, str], BinaryIO] = open,
) -> _ClassifyCommandInput:
    parser = _ArgumentParser(
        prog="home-ai-cluster classify",
        description=(
            "Classify bounded input against operator-supplied labels; read stdin "
            "when no source is supplied."
        ),
    )
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument("--text", action="append", help="Text to classify.")
    sources.add_argument(
        "-f", "--file", action="append", help="UTF-8 file to classify."
    )
    parser.add_argument(
        "-l",
        "--label",
        action="append",
        help="Candidate label supplied by the operator; repeat as needed.",
    )
    parser.add_argument(
        "--timeout-seconds",
        action="append",
        help="Native HAC request timeout in seconds.",
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "-v", "--verbose", action="store_true", help="Include execution attribution."
    )
    output.add_argument(
        "-j", "--json", action="store_true", help="Print the compact structured result."
    )
    args = parser.parse_args(argv)
    texts, files = args.text or [], args.file or []
    if len(texts) > 1 or len(files) > 1:
        raise _InvalidRequestInput
    text = (
        texts[0]
        if texts
        else (
            _read_bounded_file(files[0], file_opener=file_opener)
            if files
            else _read_bounded_utf8_source(sys.stdin.buffer if stdin is None else stdin)
        )
    )
    try:
        request = ClassifyRequest(text=text, labels=args.label or [])
        timeout_values = args.timeout_seconds or []
        if len(timeout_values) > 1:
            raise _InvalidRequestInput
        timeout = (
            _REQUEST_TIMEOUT_SECONDS
            if not timeout_values
            else _parse_timeout_seconds(timeout_values[0])
        )
    except (ValidationError, ValueError):
        raise _InvalidRequestInput from None
    return _ClassifyCommandInput(
        request,
        "verbose" if args.verbose else "json" if args.json else "default",
        timeout,
    )


def _failure_for_status(status: int) -> str | None:
    if 200 <= status < 300:
        return None
    if status == 422:
        return _CLUSTER_REJECTED
    if status == 404:
        return _NO_CAPABILITY
    if status == 409:
        return "error: execution permission denied"
    if status == 503:
        return _RUNTIME_UNAVAILABLE
    return _ORDINARY_REQUEST_FAILED


def main(
    argv: Sequence[str] | None = None,
    *,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
    _stdin: BinaryIO | None = None,
    _file_opener: Callable[[str, str], BinaryIO] = open,
) -> None:
    try:
        command = _parse_input(argv, stdin=_stdin, file_opener=_file_opener)
    except _InvalidRequestInput:
        _exit_with_failure(_INVALID_INPUT, 2)
    try:
        with _client_factory(
            timeout=command.timeout_seconds, follow_redirects=False, trust_env=False
        ) as client:
            response = client.post(
                _ORDINARY_CLASSIFY_URL,
                json=command.request.model_dump(include={"text", "labels"}),
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
        result = ClassifyResult.model_validate(response.json())
    except (ValidationError, ValueError):
        _exit_with_failure(_INVALID_CLUSTER_RESPONSE, 1)
    except Exception:
        _exit_with_failure(_ORDINARY_REQUEST_FAILED, 1)
    if command.output_mode == "json":
        sys.stdout.write(json.dumps(result.model_dump(), separators=(",", ":")) + "\n")
    elif command.output_mode == "verbose":
        sys.stdout.write(
            "Classification:\n"
            f"  Label: {result.selected_label}\n\n"
            "Execution:\n"
            f"  Node: {result.node_id}\n"
        )
    else:
        sys.stdout.write(
            result.selected_label
            if result.selected_label.endswith("\n")
            else result.selected_label + "\n"
        )
