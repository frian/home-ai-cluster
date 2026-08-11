"""One-shot client for RFC-0067 bounded textual code assistance."""

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import httpx

from home_ai_cluster import chat_command
from home_ai_cluster.core.models import Capability, ChatMessage, ClusterRequest


@dataclass(frozen=True)
class _CodeCommandInput:
    """One validated bounded code message and selected presentation."""

    message: str
    output_mode: str
    timeout_seconds: float


class _ArgumentParser(argparse.ArgumentParser):
    """Convert parser failures into the existing native input boundary."""

    def error(self, message: str) -> None:
        raise chat_command._InvalidRequestInput from None


def _parse_input(argv: Sequence[str] | None) -> _CodeCommandInput:
    parser = _ArgumentParser(prog="home-ai-cluster code")
    parser.add_argument("--message", action="append")
    parser.add_argument("--timeout-seconds")
    output_options = parser.add_mutually_exclusive_group()
    output_options.add_argument("-v", "--verbose", action="store_true")
    output_options.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    messages = args.message or []
    if len(messages) != 1 or not messages[0].strip():
        raise chat_command._InvalidRequestInput

    if args.verbose:
        output_mode = "verbose"
    elif args.json:
        output_mode = "json"
    else:
        output_mode = "content"

    try:
        timeout_seconds = (
            chat_command._REQUEST_TIMEOUT_SECONDS
            if args.timeout_seconds is None
            else chat_command._parse_timeout_seconds(args.timeout_seconds)
        )
        ClusterRequest(
            messages=[ChatMessage(role="user", content=messages[0])],
            capability=Capability(name="code"),
        )
    except ValueError:
        raise chat_command._InvalidRequestInput from None

    return _CodeCommandInput(messages[0], output_mode, timeout_seconds)


def _native_request(message: str) -> dict[str, Any]:
    request = ClusterRequest(
        messages=[ChatMessage(role="user", content=message)],
        capability=Capability(name="code"),
    )
    return {
        "messages": [request.messages[0].model_dump()],
        "capability": request.capability.name,
    }


def main(
    argv: Sequence[str] | None = None,
    *,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
) -> None:
    """Send one explicit bounded code request through the native chat path."""
    try:
        command_input = _parse_input(argv)
    except chat_command._InvalidRequestInput:
        chat_command._exit_with_failure(chat_command._INVALID_INPUT, 2)

    try:
        response = chat_command._post_native_request(
            _native_request(command_input.message),
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
        result = chat_command.ClusterResult.model_validate(response.json())
    except (chat_command.ValidationError, ValueError):
        chat_command._exit_with_failure(chat_command._INVALID_CLUSTER_RESPONSE, 1)
    except Exception:
        chat_command._exit_with_failure(chat_command._ORDINARY_REQUEST_FAILED, 1)

    chat_command._write_success(result, command_input.output_mode)
