"""One-shot RFC-0078 external-information acquisition caller edge."""

import argparse
import asyncio
import importlib.metadata
import inspect
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import ValidationError

from home_ai_cluster import chat_command
from home_ai_cluster.core.models import (
    SourceEvidence,
    SourceGroundedChatRequest,
    SourceGroundedChatResult,
)

_ENTRY_POINT_GROUP = "home_ai_cluster.external_information_acquisition.v1"
_SOURCE_GROUNDED_CHAT_URL = "http://127.0.0.1:25042/v1/chat/sources"
_MAX_PLUGIN_NAME_BYTES = 64
_MAX_QUERY_BYTES = 4_096
_ACQUISITION_FAILED = "error: external-information-acquisition-failed"
_SOURCE_FIELDS = {"title", "url", "content"}


class _InvalidRequestInput(Exception):
    """Raised when the caller edge has invalid explicit operator input."""


class _AcquisitionFailure(Exception):
    """Raised for one privacy-safe pre-routing acquisition failure."""


class _ArgumentParser(argparse.ArgumentParser):
    """Convert parser failures into the established native input boundary."""

    def error(self, message: str) -> None:
        raise _InvalidRequestInput from None


@dataclass(frozen=True)
class _CommandInput:
    plugin_name: str
    query: str
    question: str
    output_mode: str
    timeout_seconds: float


def _validate_name(value: str) -> str:
    if not value.strip() or len(value.encode("utf-8")) > _MAX_PLUGIN_NAME_BYTES:
        raise _InvalidRequestInput
    return value


def _validate_query(value: str) -> str:
    if not value.strip() or len(value.encode("utf-8")) > _MAX_QUERY_BYTES:
        raise _InvalidRequestInput
    return value


def _parse_input(argv: Sequence[str] | None) -> _CommandInput:
    parser = _ArgumentParser(prog="home-ai-cluster external-information")
    parser.add_argument("--plugin", action="append")
    parser.add_argument("--query", action="append")
    parser.add_argument("--question", action="append")
    parser.add_argument("--timeout-seconds")
    output_options = parser.add_mutually_exclusive_group()
    output_options.add_argument("-v", "--verbose", action="store_true")
    output_options.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    plugins = args.plugin or []
    queries = args.query or []
    questions = args.question or []
    if len(plugins) != 1 or len(queries) != 1 or len(questions) != 1:
        raise _InvalidRequestInput

    try:
        timeout_seconds = (
            chat_command._REQUEST_TIMEOUT_SECONDS
            if args.timeout_seconds is None
            else chat_command._parse_timeout_seconds(args.timeout_seconds)
        )
    except ValueError:
        raise _InvalidRequestInput from None

    return _CommandInput(
        plugin_name=_validate_name(plugins[0]),
        query=_validate_query(queries[0]),
        question=questions[0],
        output_mode="verbose" if args.verbose else "json" if args.json else "content",
        timeout_seconds=timeout_seconds,
    )


def _selected_entry_point(name: str) -> Any:
    try:
        matches = [
            entry_point
            for entry_point in importlib.metadata.entry_points().select(
                group=_ENTRY_POINT_GROUP
            )
            if entry_point.name == name
        ]
    except Exception:
        raise _AcquisitionFailure from None
    if len(matches) != 1:
        raise _AcquisitionFailure
    return matches[0]


def _load_async_acquisition(entry_point: Any) -> Callable[[str], Any]:
    try:
        acquisition = entry_point.load()
    except Exception:
        raise _AcquisitionFailure from None
    if not callable(acquisition) or not (
        inspect.iscoroutinefunction(acquisition)
        or inspect.iscoroutinefunction(acquisition.__call__)
    ):
        raise _AcquisitionFailure
    return acquisition


def _candidate_sources(value: object) -> list[SourceEvidence]:
    if type(value) is not list or not 1 <= len(value) <= 5:
        raise _AcquisitionFailure

    sources: list[SourceEvidence] = []
    for candidate in value:
        if type(candidate) is not dict or set(candidate) != _SOURCE_FIELDS:
            raise _AcquisitionFailure
        if any(type(key) is not str for key in candidate):
            raise _AcquisitionFailure
        if any(type(item) is not str for item in candidate.values()):
            raise _AcquisitionFailure
        try:
            sources.append(SourceEvidence(**candidate))
        except (TypeError, ValidationError, ValueError):
            raise _AcquisitionFailure from None
    return sources


def _acquire_request(command_input: _CommandInput) -> SourceGroundedChatRequest:
    entry_point = _selected_entry_point(command_input.plugin_name)
    acquisition = _load_async_acquisition(entry_point)
    try:
        candidates = asyncio.run(acquisition(command_input.query))
        sources = _candidate_sources(candidates)
        return SourceGroundedChatRequest(
            question=command_input.question,
            sources=sources,
        )
    except _AcquisitionFailure:
        raise
    except Exception:
        raise _AcquisitionFailure from None


def _public_request(request: SourceGroundedChatRequest) -> dict[str, object]:
    """Serialize only the accepted public source-grounded body."""
    return {
        "question": request.question,
        "sources": [source.model_dump() for source in request.sources],
    }


def _post_source_grounded_request(
    request: dict[str, object],
    *,
    timeout_seconds: float,
    client_factory: Callable[..., httpx.Client],
) -> httpx.Response:
    with client_factory(
        timeout=timeout_seconds, follow_redirects=False, trust_env=False
    ) as client:
        return client.post(_SOURCE_GROUNDED_CHAT_URL, json=request)


def _write_verbose_result(result: SourceGroundedChatResult) -> None:
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


def _write_success(result: SourceGroundedChatResult, output_mode: str) -> None:
    if output_mode == "content":
        chat_command._write_content(result.content)
    elif output_mode == "verbose":
        _write_verbose_result(result)
    else:
        print(json.dumps(result.model_dump(), separators=(",", ":")))


def main(
    argv: Sequence[str] | None = None,
    *,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
) -> None:
    """Acquire bounded evidence once, then use the existing source-chat route."""
    try:
        command_input = _parse_input(argv)
    except _InvalidRequestInput:
        chat_command._exit_with_failure(chat_command._INVALID_INPUT, 2)

    try:
        request = _acquire_request(command_input)
    except _AcquisitionFailure:
        chat_command._exit_with_failure(_ACQUISITION_FAILED, 1)

    try:
        response = _post_source_grounded_request(
            _public_request(request),
            timeout_seconds=command_input.timeout_seconds,
            client_factory=_client_factory,
        )
    except httpx.ConnectError:
        chat_command._exit_with_failure(chat_command._CLUSTER_UNAVAILABLE, 1)
    except httpx.TimeoutException:
        chat_command._exit_with_failure(chat_command._ORDINARY_REQUEST_TIMED_OUT, 1)
    except httpx.RequestError:
        chat_command._exit_with_failure(chat_command._ORDINARY_REQUEST_FAILED, 1)
    except Exception:
        chat_command._exit_with_failure(chat_command._ORDINARY_REQUEST_FAILED, 1)

    failure = chat_command._failure_for_status(response.status_code)
    if failure is not None:
        chat_command._exit_with_failure(failure, 1)

    try:
        result = SourceGroundedChatResult.model_validate(response.json())
    except (ValidationError, ValueError):
        chat_command._exit_with_failure(chat_command._INVALID_CLUSTER_RESPONSE, 1)
    except Exception:
        chat_command._exit_with_failure(chat_command._ORDINARY_REQUEST_FAILED, 1)

    _write_success(result, command_input.output_mode)
