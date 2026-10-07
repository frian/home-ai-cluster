"""One effectful request through the active RFC-0149 explanation carrier."""

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from typing import BinaryIO, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError

from home_ai_cluster.commands.chat_command import _parse_timeout_seconds
from home_ai_cluster.commands.summarize_command import (
    _InvalidRequestInput,
    _read_bounded_file,
    _read_bounded_utf8_source,
)
from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClassifyRequest,
    ClusterRequest,
    SummarizeRequest,
)

_URL = "http://127.0.0.1:25042/diagnostics/actual-request-explanation"
_INVALID_INPUT = "error: invalid request explanation input"
_UNAVAILABLE = "error: ordinary cluster unavailable"
_TIMED_OUT = "error: request explanation timed out"
_REJECTED = "error: request explanation rejected"
_EXPLANATION_UNAVAILABLE = "error: request explanation unavailable"
_FAILED = "error: request explanation failed"
_INVALID_RESPONSE = "error: invalid request explanation response"


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _InvalidRequestInput from None


class _ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _LocalSelection(_ClosedModel):
    kind: Literal["local"]


class _RemoteSelection(_ClosedModel):
    kind: Literal["declared_remote"]
    node_id: str = Field(min_length=1)


class _CandidateFact(_ClosedModel):
    family: Literal["local", "declared-remote"]
    node_id: str = Field(min_length=1)
    fact: Literal[
        "execution-permission-granted",
        "execution-permission-denied",
        "adapter-invoked",
        "transport-invoked",
        "execution-permission-refused",
    ]


class _Continuation(_ClosedModel):
    node_id: str = Field(min_length=1)
    reason: Literal[
        "local-execution-permission-denied",
        "local-runtime-connection-unavailable-before-request",
        "remote-runtime-connection-unavailable-before-request",
        "remote-execution-permission-refused",
    ]


class _Explanation(_ClosedModel):
    requested_capability: Literal["chat", "code", "summarize", "classify"]
    local_only: StrictBool
    initial_selection: _LocalSelection | _RemoteSelection | None
    candidate_facts: list[_CandidateFact]
    continuations: list[_Continuation]
    final_node_id: str | None


class _TextResult(_ClosedModel):
    content: str
    adapter: str = Field(min_length=1)
    model: str | None
    node_id: str = Field(min_length=1)


class _ClassifyResult(_ClosedModel):
    selected_label: str
    node_id: str = Field(min_length=1)


class _Failure(_ClosedModel):
    status: Literal[
        "no-selectable-candidate",
        "execution-permission-denied",
        "runtime-unavailable",
        "execution-failed",
    ]


class _Account(_ClosedModel):
    status: Literal["succeeded", "failed"]
    result: _TextResult | _ClassifyResult | None
    failure: _Failure | None
    explanation: _Explanation


_FACTS = {
    "local": {
        "execution-permission-granted",
        "execution-permission-denied",
        "adapter-invoked",
    },
    "declared-remote": {"transport-invoked", "execution-permission-refused"},
}
_REASONS = {
    "local-execution-permission-denied": ("local", "execution-permission-denied"),
    "local-runtime-connection-unavailable-before-request": (
        "local",
        "adapter-invoked",
    ),
    "remote-runtime-connection-unavailable-before-request": (
        "declared-remote",
        "transport-invoked",
    ),
    "remote-execution-permission-refused": (
        "declared-remote",
        "execution-permission-refused",
    ),
}


def _parse(
    argv: Sequence[str] | None,
    *,
    stdin: BinaryIO | None,
    file_opener: Callable[[str, str], BinaryIO],
) -> tuple[str, bool, float, dict[str, object]]:
    parser = _ArgumentParser(
        prog="home-ai-cluster explain-active-request",
        description="Execute and explain one request in the running ordinary cluster.",
    )
    commands = parser.add_subparsers(
        dest="kind", required=True, parser_class=_ArgumentParser
    )
    for kind in ("chat", "code", "summarize", "classify"):
        command = commands.add_parser(kind)
        if kind in {"chat", "code"}:
            command.add_argument("message_positional", nargs="?", metavar="MESSAGE")
            command.add_argument("--message", action="append")
        else:
            sources = command.add_mutually_exclusive_group()
            sources.add_argument("--text", action="append")
            sources.add_argument("--file", action="append")
            if kind == "classify":
                command.add_argument("--label", action="append")
        command.add_argument("--local-only", action="store_true")
        command.add_argument("--timeout-seconds", action="append")
    args = parser.parse_args(argv)
    timeouts = args.timeout_seconds or []
    if len(timeouts) > 1:
        raise _InvalidRequestInput
    try:
        timeout = 120.0 if not timeouts else _parse_timeout_seconds(timeouts[0])
    except ValueError:
        raise _InvalidRequestInput from None

    kind: str = args.kind
    if kind in {"chat", "code"}:
        options = args.message or []
        if args.message_positional is not None:
            if options:
                raise _InvalidRequestInput
            message = args.message_positional
        elif len(options) == 1:
            message = options[0]
        else:
            raise _InvalidRequestInput
        if not message.strip():
            raise _InvalidRequestInput
        try:
            ClusterRequest(
                messages=[ChatMessage(role="user", content=message)],
                capability=Capability(name=kind),
            )
        except ValidationError:
            raise _InvalidRequestInput from None
        request: dict[str, object] = {
            "capability": kind,
            "messages": [{"role": "user", "content": message}],
        }
    else:
        texts, files = args.text or [], args.file or []
        if len(texts) > 1 or len(files) > 1:
            raise _InvalidRequestInput
        if texts:
            source = texts[0]
        elif files:
            source = _read_bounded_file(files[0], file_opener=file_opener)
        else:
            source = _read_bounded_utf8_source(
                sys.stdin.buffer if stdin is None else stdin
            )
        try:
            if kind == "classify":
                labels = args.label or []
                ClassifyRequest(text=source, labels=labels)
                request = {"text": source, "labels": labels}
            else:
                SummarizeRequest(text=source)
                request = {"text": source}
        except ValidationError:
            raise _InvalidRequestInput from None
    return kind, args.local_only, timeout, request


def _validate_account(
    value: object, *, kind: str, local_only: bool, labels: list[str]
) -> _Account:
    account = _Account.model_validate(value)
    explanation = account.explanation
    if explanation.requested_capability != kind or explanation.local_only != local_only:
        raise ValueError("request identity mismatch")
    if account.status == "succeeded":
        result = account.result
        if result is None or account.failure is not None:
            raise ValueError("invalid success")
        if kind == "classify":
            if (
                not isinstance(result, _ClassifyResult)
                or result.selected_label not in labels
            ):
                raise ValueError("invalid classification result")
        elif not isinstance(result, _TextResult):
            raise ValueError("invalid text result")
        if not explanation.final_node_id or result.node_id != explanation.final_node_id:
            raise ValueError("invalid final attribution")
    elif (
        account.result is not None
        or account.failure is None
        or explanation.final_node_id is not None
    ):
        raise ValueError("invalid failure")

    positions: dict[tuple[str, str], int] = {}
    facts: set[tuple[str, str, str]] = set()
    fact_positions: dict[tuple[str, str, str], int] = {}
    current: tuple[str, str] | None = None
    for index, item in enumerate(explanation.candidate_facts):
        candidate = (item.family, item.node_id)
        if item.fact not in _FACTS[item.family]:
            raise ValueError("wrong family fact")
        if candidate != current:
            if candidate in positions:
                raise ValueError("candidate resumed")
            positions[candidate] = len(positions)
            current = candidate
        fact = (*candidate, item.fact)
        if fact in facts:
            raise ValueError("duplicate fact")
        facts.add(fact)
        fact_positions[fact] = index

    selection = explanation.initial_selection
    if selection is None:
        if positions:
            raise ValueError("facts without selection")
    elif positions:
        first = next(iter(positions))
        if isinstance(selection, _LocalSelection):
            if first[0] != "local":
                raise ValueError("wrong initial candidate")
        elif first != ("declared-remote", selection.node_id):
            raise ValueError("wrong initial candidate")

    for family, node_id in positions:
        grant = fact_positions.get((family, node_id, "execution-permission-granted"))
        denial = (family, node_id, "execution-permission-denied") in facts
        invocation = fact_positions.get((family, node_id, "adapter-invoked"))
        if family == "local":
            if denial and (grant is not None or invocation is not None):
                raise ValueError("contradictory permission")
            if invocation is not None and (grant is None or grant > invocation):
                raise ValueError("invocation without prior grant")
        else:
            transport = fact_positions.get((family, node_id, "transport-invoked"))
            refusal = fact_positions.get(
                (family, node_id, "execution-permission-refused")
            )
            if refusal is not None and (transport is None or transport > refusal):
                raise ValueError("refusal without prior transport")

    seen_continuations: set[tuple[str, str]] = set()
    previous_position = -1
    for item in explanation.continuations:
        identity = (item.node_id, item.reason)
        if identity in seen_continuations:
            raise ValueError("duplicate continuation")
        seen_continuations.add(identity)
        family, required = _REASONS[item.reason]
        candidate = (family, item.node_id)
        position = positions.get(candidate)
        if (
            position is None
            or position < previous_position
            or position == len(positions) - 1
            or (family, item.node_id, required) not in facts
        ):
            raise ValueError("invalid continuation")
        previous_position = position

    if account.status == "succeeded" and not any(
        item.node_id == explanation.final_node_id
        and item.fact in {"adapter-invoked", "transport-invoked"}
        for item in explanation.candidate_facts
    ):
        raise ValueError("final node not invoked")
    return account


def _failure(message: str, code: int) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code) from None


def main(
    argv: Sequence[str] | None = None,
    *,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
    _stdin: BinaryIO | None = None,
    _file_opener: Callable[[str, str], BinaryIO] = open,
) -> None:
    """Submit one request and print its complete validated public account."""
    try:
        kind, local_only, timeout, request = _parse(
            argv, stdin=_stdin, file_opener=_file_opener
        )
    except (_InvalidRequestInput, UnicodeError):
        _failure(_INVALID_INPUT, 2)
    body = {"kind": kind, "local_only": local_only, "request": request}
    try:
        with _client_factory(
            timeout=timeout, follow_redirects=False, trust_env=False
        ) as client:
            response = client.post(_URL, json=body)
    except httpx.TimeoutException:
        _failure(_TIMED_OUT, 1)
    except httpx.ConnectError:
        _failure(_UNAVAILABLE, 1)
    except Exception:
        _failure(_FAILED, 1)
    if response.status_code == 422:
        _failure(_REJECTED, 1)
    if response.status_code == 503:
        _failure(_EXPLANATION_UNAVAILABLE, 1)
    if response.status_code != 200:
        _failure(_FAILED, 1)
    try:
        account = _validate_account(
            response.json(),
            kind=kind,
            local_only=local_only,
            labels=request.get("labels", []),
        )
    except (ValidationError, ValueError, TypeError):
        _failure(_INVALID_RESPONSE, 1)
    except Exception:
        _failure(_FAILED, 1)
    print(json.dumps(account.model_dump(), separators=(",", ":")))
