"""Client for one-shot and bounded foreground Code requests."""

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, TextIO

import httpx

from home_ai_cluster import chat_command
from home_ai_cluster.core.models import Capability, ChatMessage, ClusterRequest


@dataclass(frozen=True)
class _CodeCommandInput:
    """One validated code message or the no-message interactive mode."""

    message: str | None
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
    output_options.add_argument("-j", "--json", action="store_true")
    args = parser.parse_args(argv)

    option_messages = args.message or []
    message: str | None = None
    if args.message_positional is not None:
        if option_messages:
            raise chat_command._InvalidRequestInput
        message = args.message_positional
    elif len(option_messages) == 1:
        message = option_messages[0]
    elif option_messages:
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
    except ValueError:
        raise chat_command._InvalidRequestInput from None

    if message is None:
        if output_mode != "content":
            raise chat_command._InvalidRequestInput
    elif not message.strip():
        raise chat_command._InvalidRequestInput
    else:
        try:
            ClusterRequest(
                messages=[ChatMessage(role="user", content=message)],
                capability=Capability(name="code"),
            )
        except ValueError:
            raise chat_command._InvalidRequestInput from None

    return _CodeCommandInput(message, output_mode, timeout_seconds)


def _native_request(messages: str | Sequence[ChatMessage]) -> dict[str, Any]:
    """Build one existing bounded Code request without changing its wire shape."""
    if isinstance(messages, str):
        messages = [ChatMessage(role="user", content=messages)]
    request = ClusterRequest(
        messages=list(messages),
        capability=Capability(name="code"),
    )
    return {
        "messages": [message.model_dump() for message in request.messages],
        "capability": request.capability.name,
    }


def _failure_for_status(status_code: int) -> str | None:
    """Keep the native code capability failure name truthful."""
    if status_code == 404:
        return "error: no available code capability"
    return chat_command._failure_for_status(status_code)


def _send_native_request(
    messages: Sequence[ChatMessage],
    *,
    timeout_seconds: float,
    client_factory: Callable[..., httpx.Client],
) -> tuple[chat_command.ClusterResult | None, str | None]:
    """Send one Code request, retaining Code-specific safe failures."""
    try:
        response = chat_command._post_native_request(
            _native_request(messages),
            timeout_seconds=timeout_seconds,
            client_factory=client_factory,
        )
    except httpx.ConnectError:
        return None, chat_command._CLUSTER_UNAVAILABLE
    except httpx.TimeoutException:
        return None, chat_command._ORDINARY_REQUEST_TIMED_OUT
    except httpx.RequestError:
        return None, chat_command._ORDINARY_REQUEST_FAILED
    except Exception:
        return None, chat_command._ORDINARY_REQUEST_FAILED

    failure = _failure_for_status(response.status_code)
    if failure is not None:
        return None, failure

    try:
        return chat_command.ClusterResult.model_validate(response.json()), None
    except (chat_command.ValidationError, ValueError):
        return None, chat_command._INVALID_CLUSTER_RESPONSE
    except Exception:
        return None, chat_command._ORDINARY_REQUEST_FAILED


def _run_interactive(
    *,
    timeout_seconds: float,
    client_factory: Callable[..., httpx.Client],
    stdin: TextIO,
    stdout: TextIO,
    stderr: TextIO,
) -> None:
    """Run one process-owned Code conversation until EOF or Ctrl-C."""
    retained_messages: list[ChatMessage] = []
    try:
        while True:
            stdout.write("> ")
            stdout.flush()
            submitted = stdin.readline()
            if submitted == "":
                return
            message = submitted.rstrip("\r\n")
            if not message.strip():
                continue

            candidate = [*retained_messages, ChatMessage(role="user", content=message)]
            try:
                _native_request(candidate)
            except ValueError:
                print(chat_command._INVALID_INPUT, file=stderr)
                continue

            print("…", file=stderr)
            result, failure = _send_native_request(
                candidate,
                timeout_seconds=timeout_seconds,
                client_factory=client_factory,
            )
            if failure is not None:
                print(failure, file=stderr)
                continue

            assert result is not None
            if not result.content:
                print(chat_command._INVALID_CLUSTER_RESPONSE, file=stderr)
                continue
            retained_messages = [
                *candidate,
                ChatMessage(role="assistant", content=result.content),
            ]
            chat_command._write_content(result.content, stdout=stdout)
    except KeyboardInterrupt:
        return


def main(
    argv: Sequence[str] | None = None,
    *,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
    _stdin: TextIO | None = None,
    _stdout: TextIO | None = None,
    _stderr: TextIO | None = None,
) -> None:
    """Send one Code request or run the accepted TTY-only lifecycle."""
    stdin = sys.stdin if _stdin is None else _stdin
    stdout = sys.stdout if _stdout is None else _stdout
    stderr = sys.stderr if _stderr is None else _stderr
    try:
        command_input = _parse_input(argv)
    except chat_command._InvalidRequestInput:
        chat_command._exit_with_failure(chat_command._INVALID_INPUT, 2, stderr=stderr)

    if command_input.message is None:
        if not stdin.isatty() or not stdout.isatty():
            chat_command._exit_with_failure(
                chat_command._INVALID_INPUT, 2, stderr=stderr
            )
        _run_interactive(
            timeout_seconds=command_input.timeout_seconds,
            client_factory=_client_factory,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )
        return

    result, failure = _send_native_request(
        [ChatMessage(role="user", content=command_input.message)],
        timeout_seconds=command_input.timeout_seconds,
        client_factory=_client_factory,
    )
    if failure is not None:
        chat_command._exit_with_failure(failure, 1, stderr=stderr)
    assert result is not None
    chat_command._write_success(result, command_input.output_mode, stdout=stdout)
