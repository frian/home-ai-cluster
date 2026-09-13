"""Bounded RFC-0116 workspace-aware Code interaction."""

import asyncio
import json
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from home_ai_cluster.api.client_disconnect import cancellation_has_won
from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
)
from home_ai_cluster.core.workspace_authority import (
    WorkspaceAuthority,
    WorkspaceAuthorityError,
    WorkspaceEntry,
)

_ACTION_BUDGET = 8
_MAX_RESULT_BYTES = 8 * 1024 * 1024
_CONTRACT = (
    "HAC workspace Code: respond with exactly one bare JSON object, no prose or "
    "Markdown fences:\n"
    '{"kind":"final","content":"..."}\n'
    '{"kind":"workspace","operation":"list","path":"."}\n'
    '{"kind":"workspace","operation":"read","path":"file.py"}\n'
    '{"kind":"workspace","operation":"create","path":"new.py"}\n'
    '{"kind":"workspace","operation":"write","path":"file.py","content":"..."}\n'
    "If the operator asks for an explanation, put that explanation only in the "
    '"content" '
    "field of a final JSON response. "
    "Request at most one workspace action. If more workspace work is required, request "
    "the next action before final. After a refusal, final may truthfully report "
    "inability. HAC owns workspace authority and may refuse operations."
)
_HISTORY_REMINDER = (
    "Previous assistant messages are history, not format examples. Use the HAC JSON "
    "contract for this response. If more workspace work is required, request the next "
    "action before final."
)
_OUTCOME_PREFIX = "HAC workspace outcome:\n"


class WorkspaceAwareCodeStatus(StrEnum):
    """Terminal states of this one bounded interaction."""

    FINAL = "final"
    MALFORMED_MODEL_RESPONSE = "malformed-model-response"
    OVERSIZED_MODEL_RESPONSE = "oversized-model-response"
    ACTION_BUDGET_EXHAUSTED = "action-budget-exhausted"
    CODE_CONTEXT_TOO_LARGE = "code-context-too-large"
    CODE_INFERENCE_FAILED = "code-inference-failed"
    INTERNAL_FAILURE = "internal-failure"


@dataclass(frozen=True)
class WorkspaceAwareCodeResult:
    """A narrow programmatic result for one RFC-0116 interaction."""

    status: WorkspaceAwareCodeStatus
    content: str | None = None


@dataclass(frozen=True)
class _Final:
    content: str


@dataclass(frozen=True)
class _WorkspaceRequest:
    operation: Literal["list", "read", "write", "create"]
    path: str
    content: str | None = None


CodeInference = Callable[[Sequence[ChatMessage]], ClusterResult | None]
AsyncCodeInference = Callable[[Sequence[ChatMessage]], Awaitable[ClusterResult | None]]
CompletedActionObserver = Callable[
    [Literal["list", "read", "write", "create"], str, Literal["success", "refused"]],
    None,
]


def run_workspace_aware_code(
    instruction: str,
    *,
    root: str | Path,
    operations: set[str] | frozenset[str],
    infer: CodeInference,
    on_completed_action: CompletedActionObserver | None = None,
) -> WorkspaceAwareCodeResult:
    """Run one synchronous, ephemeral workspace-aware Code interaction."""
    authority = WorkspaceAuthority(root, operations)
    return _run_interaction(
        instruction,
        authority=authority,
        infer=infer,
        on_completed_action=on_completed_action,
    )


def _run_interaction(
    instruction: str,
    *,
    authority: WorkspaceAuthority,
    prior_messages: Sequence[ChatMessage] = (),
    infer: CodeInference,
    on_completed_action: CompletedActionObserver | None = None,
) -> WorkspaceAwareCodeResult:
    """Run one RFC-0116 interaction using one already-constructed authority."""
    steps = _interaction_steps(
        instruction,
        authority=authority,
        prior_messages=prior_messages,
        on_completed_action=on_completed_action,
    )
    try:
        messages = next(steps)
        while True:
            try:
                result = infer(messages)
            except Exception:
                return WorkspaceAwareCodeResult(
                    WorkspaceAwareCodeStatus.INTERNAL_FAILURE
                )
            messages = steps.send(result)
    except StopIteration as terminal:
        return terminal.value


def _interaction_steps(
    instruction: str,
    *,
    authority: WorkspaceAuthority,
    prior_messages: Sequence[ChatMessage] = (),
    on_completed_action: CompletedActionObserver | None = None,
):
    """Own the shared RFC-0116 state transitions between Code inferences."""
    if not isinstance(instruction, str) or not instruction.strip():
        raise ValueError("instruction must be non-blank")
    messages = [ChatMessage(role="system", content=_CONTRACT), *prior_messages]
    if prior_messages:
        messages.append(ChatMessage(role="user", content=_HISTORY_REMINDER))
    messages.append(ChatMessage(role="user", content=instruction))
    actions = 0

    while True:
        try:
            ClusterRequest(messages=messages, capability=Capability(name="code"))
        except ValueError:
            return WorkspaceAwareCodeResult(
                WorkspaceAwareCodeStatus.CODE_CONTEXT_TOO_LARGE
            )
        result = yield tuple(messages)
        if result is None:
            return WorkspaceAwareCodeResult(
                WorkspaceAwareCodeStatus.CODE_INFERENCE_FAILED
            )
        if not isinstance(result, ClusterResult):
            return WorkspaceAwareCodeResult(WorkspaceAwareCodeStatus.INTERNAL_FAILURE)

        try:
            result_size = len(result.content.encode("utf-8", errors="strict"))
        except UnicodeError:
            return WorkspaceAwareCodeResult(
                WorkspaceAwareCodeStatus.MALFORMED_MODEL_RESPONSE
            )
        if result_size > _MAX_RESULT_BYTES:
            return WorkspaceAwareCodeResult(
                WorkspaceAwareCodeStatus.OVERSIZED_MODEL_RESPONSE
            )
        try:
            response = _parse_response(result.content)
        except (TypeError, ValueError, json.JSONDecodeError, RecursionError):
            return WorkspaceAwareCodeResult(
                WorkspaceAwareCodeStatus.MALFORMED_MODEL_RESPONSE
            )

        if isinstance(response, _Final):
            return WorkspaceAwareCodeResult(
                WorkspaceAwareCodeStatus.FINAL, response.content
            )
        if actions == _ACTION_BUDGET:
            return WorkspaceAwareCodeResult(
                WorkspaceAwareCodeStatus.ACTION_BUDGET_EXHAUSTED
            )

        actions += 1
        try:
            outcome = _dispatch(authority, response)
        except WorkspaceAuthorityError:
            outcome = {"status": "refused"}
        except Exception:
            return WorkspaceAwareCodeResult(WorkspaceAwareCodeStatus.INTERNAL_FAILURE)
        if on_completed_action is not None:
            try:
                on_completed_action(
                    response.operation, response.path, outcome["status"]
                )
            except Exception:
                return WorkspaceAwareCodeResult(
                    WorkspaceAwareCodeStatus.INTERNAL_FAILURE
                )
        messages.append(ChatMessage(role="assistant", content=result.content))
        messages.append(
            ChatMessage(role="user", content=_outcome_message(response, outcome))
        )


async def run_workspace_aware_code_async(
    instruction: str,
    *,
    root: str | Path,
    operations: set[str] | frozenset[str],
    prior_messages: Sequence[ChatMessage] = (),
    infer: AsyncCodeInference,
    on_completed_action: CompletedActionObserver | None = None,
) -> WorkspaceAwareCodeResult:
    """Run one cancellable RFC-0116 interaction for a browser turn."""
    authority = WorkspaceAuthority(root, operations)
    steps = _interaction_steps(
        instruction,
        authority=authority,
        prior_messages=prior_messages,
        on_completed_action=on_completed_action,
    )
    try:
        messages = next(steps)
        while True:
            try:
                result = await infer(messages)
            except Exception:
                return WorkspaceAwareCodeResult(
                    WorkspaceAwareCodeStatus.INTERNAL_FAILURE
                )
            if asyncio.current_task().cancelling() or cancellation_has_won():
                raise asyncio.CancelledError
            messages = steps.send(result)
    except StopIteration as terminal:
        return terminal.value


def _parse_response(content: str) -> _Final | _WorkspaceRequest:
    """Parse precisely the closed RFC-0116 response grammar."""
    value = json.loads(
        content,
        object_pairs_hook=_object_without_duplicates,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict):
        raise ValueError("response must be an object")
    kind = value.get("kind")
    if kind == "final":
        if set(value) != {"kind", "content"} or not isinstance(
            value.get("content"), str
        ):
            raise ValueError("invalid final response")
        return _Final(value["content"])
    if kind != "workspace":
        raise ValueError("invalid response kind")

    operation = value.get("operation")
    path = value.get("path")
    if operation not in {"list", "read", "write", "create"} or not isinstance(
        path, str
    ):
        raise ValueError("invalid workspace response")
    if operation in {"list", "read", "create"}:
        if set(value) != {"kind", "operation", "path"}:
            raise ValueError("invalid workspace response")
        return _WorkspaceRequest(operation, path)
    if set(value) != {"kind", "operation", "path", "content"} or not isinstance(
        value.get("content"), str
    ):
        raise ValueError("invalid workspace response")
    return _WorkspaceRequest(operation, path, value["content"])


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ValueError("non-standard JSON constant")


def _dispatch(
    authority: WorkspaceAuthority, request: _WorkspaceRequest
) -> dict[str, Any]:
    if request.operation == "list":
        entries = authority.list(request.path)
        return {
            "status": "success",
            "entries": [_entry_value(entry) for entry in entries],
        }
    if request.operation == "read":
        return {"status": "success", "content": authority.read(request.path)}
    if request.operation == "create":
        authority.create(request.path)
        return {"status": "success"}
    authority.write(request.path, request.content or "")
    return {"status": "success"}


def _entry_value(entry: WorkspaceEntry) -> dict[str, str]:
    return {"name": entry.name, "kind": entry.kind}


def _outcome_message(request: _WorkspaceRequest, outcome: dict[str, Any]) -> str:
    requested: dict[str, str] = {"operation": request.operation, "path": request.path}
    if request.operation == "write":
        requested["content"] = request.content or ""
    return _OUTCOME_PREFIX + json.dumps(
        {"requested": requested, "outcome": outcome},
        ensure_ascii=False,
        separators=(",", ":"),
    )
