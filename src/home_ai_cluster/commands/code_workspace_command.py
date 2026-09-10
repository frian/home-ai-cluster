"""Foreground caller edge for one RFC-0116 workspace-aware Code interaction."""

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TextIO

import httpx

from home_ai_cluster import workspace_aware_code
from home_ai_cluster.commands import chat_command, code_command
from home_ai_cluster.core.models import ChatMessage
from home_ai_cluster.core.workspace_authority import WorkspaceAuthorityError

_RUNTIME_FAILURE = "error: code-workspace interaction failed"
_ROOT_FAILURE = "error: invalid code-workspace root"


@dataclass(frozen=True)
class _CodeWorkspaceInput:
    root: str
    operations: frozenset[str]
    message: str
    timeout_seconds: float


class _ArgumentParser(argparse.ArgumentParser):
    """Convert parser failures into the existing native input boundary."""

    def error(self, message: str) -> None:
        raise chat_command._InvalidRequestInput from None


def _parse_input(argv: Sequence[str] | None) -> _CodeWorkspaceInput:
    parser = _ArgumentParser(
        prog="home-ai-cluster code-workspace",
        description=(
            "Run one bounded workspace-aware Code interaction with caller-local "
            "root and grants. Ordinary Code routing still applies, so workspace text "
            "may be sent to configured remote Code nodes; the physical root and "
            "grants remain local. --root and MESSAGE are ordinary local argv values."
        ),
    )
    parser.add_argument("--root", action="append", metavar="PATH")
    parser.add_argument("--grant", action="append", choices=("list", "read", "write"))
    parser.add_argument("message_positional", nargs="?", metavar="MESSAGE")
    parser.add_argument("--message", action="append", metavar="MESSAGE")
    parser.add_argument("--timeout-seconds", metavar="SECONDS")
    args = parser.parse_args(argv)

    roots = args.root or []
    messages = args.message or []
    grants = args.grant or []
    if len(roots) != 1 or not grants:
        raise chat_command._InvalidRequestInput
    if args.message_positional is not None:
        if messages:
            raise chat_command._InvalidRequestInput
        message = args.message_positional
    elif len(messages) == 1:
        message = messages[0]
    else:
        raise chat_command._InvalidRequestInput
    if not message.strip():
        raise chat_command._InvalidRequestInput
    try:
        timeout_seconds = (
            chat_command._REQUEST_TIMEOUT_SECONDS
            if args.timeout_seconds is None
            else chat_command._parse_timeout_seconds(args.timeout_seconds)
        )
    except ValueError:
        raise chat_command._InvalidRequestInput from None
    return _CodeWorkspaceInput(roots[0], frozenset(grants), message, timeout_seconds)


def _render_logical_path(path: str) -> str:
    """Return an ASCII-only quoted presentation of an unchanged logical path."""
    return json.dumps(path, ensure_ascii=True)


def main(
    argv: Sequence[str] | None = None,
    *,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
    _stdout: TextIO | None = None,
    _stderr: TextIO | None = None,
) -> None:
    """Run one explicit, ephemeral workspace-aware Code interaction."""
    stdout = sys.stdout if _stdout is None else _stdout
    stderr = sys.stderr if _stderr is None else _stderr
    try:
        command_input = _parse_input(argv)
    except chat_command._InvalidRequestInput:
        chat_command._exit_with_failure(chat_command._INVALID_INPUT, 2, stderr=stderr)

    saved_failure: str | None = None

    def infer(messages: Sequence[ChatMessage]):
        nonlocal saved_failure
        saved_failure = None
        result, failure = code_command._send_native_request(
            messages,
            timeout_seconds=command_input.timeout_seconds,
            client_factory=_client_factory,
        )
        saved_failure = failure
        return result

    def observe(operation: str, path: str, outcome: str) -> None:
        stderr.write(f"workspace {operation} {_render_logical_path(path)}: {outcome}\n")
        stderr.flush()

    try:
        outcome = workspace_aware_code.run_workspace_aware_code(
            command_input.message,
            root=command_input.root,
            operations=command_input.operations,
            infer=infer,
            on_completed_action=observe,
        )
    except WorkspaceAuthorityError:
        chat_command._exit_with_failure(_ROOT_FAILURE, 1, stderr=stderr)

    if outcome.status == workspace_aware_code.WorkspaceAwareCodeStatus.FINAL:
        chat_command._write_content(outcome.content or "", stdout=stdout)
        return
    if (
        outcome.status
        == workspace_aware_code.WorkspaceAwareCodeStatus.CODE_INFERENCE_FAILED
        and saved_failure is not None
    ):
        chat_command._exit_with_failure(saved_failure, 1, stderr=stderr)
    chat_command._exit_with_failure(_RUNTIME_FAILURE, 1, stderr=stderr)
