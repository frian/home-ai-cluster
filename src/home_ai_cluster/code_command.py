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
            raise chat_command._InvalidRequestInput
        message = args.message_positional
    elif len(option_messages) == 1:
        message = option_messages[0]
    else:
        raise chat_command._InvalidRequestInput

    if not message.strip():
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
            messages=[ChatMessage(role="user", content=message)],
            capability=Capability(name="code"),
        )
    except ValueError:
        raise chat_command._InvalidRequestInput from None

    return _CodeCommandInput(message, output_mode, timeout_seconds)


def _native_request(message: str) -> dict[str, Any]:
    request = ClusterRequest(
        messages=[ChatMessage(role="user", content=message)],
        capability=Capability(name="code"),
    )
    return {
        "messages": [request.messages[0].model_dump()],
        "capability": request.capability.name,
    }


def _failure_for_status(status_code: int) -> str | None:
    """Keep the native code capability failure name truthful."""
    if status_code == 404:
        return "error: no available code capability"
    return chat_command._failure_for_status(status_code)


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

    failure = _failure_for_status(response.status_code)
    if failure is not None:
        chat_command._exit_with_failure(failure, 1)

    try:
        result = chat_command.ClusterResult.model_validate(response.json())
    except (chat_command.ValidationError, ValueError):
        chat_command._exit_with_failure(chat_command._INVALID_CLUSTER_RESPONSE, 1)
    except Exception:
        chat_command._exit_with_failure(chat_command._ORDINARY_REQUEST_FAILED, 1)

    chat_command._write_success(result, command_input.output_mode)
