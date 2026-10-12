"""Thin loopback client for the active RFC-0147 routing explanation."""

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from typing import Annotated, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError

from home_ai_cluster.core.static_capabilities import ACCEPTED_CAPABILITY_NAMES

_URL = "http://127.0.0.1:25042/diagnostics/static-routing-explanation"
_TIMEOUT_SECONDS = 10.0
_INVALID_INPUT = "error: invalid routing explanation input"
_UNAVAILABLE = "error: ordinary cluster unavailable"
_REJECTED = "error: routing explanation rejected"
_EXPLANATION_UNAVAILABLE = "error: routing explanation unavailable"
_FAILED = "error: routing explanation failed"
_INVALID_RESPONSE = "error: invalid routing explanation response"


class _InvalidInput(Exception):
    """One invocation did not supply the bounded public input."""


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _InvalidInput from None


class _LocalSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["local"]


class _RemoteSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["declared_remote"]
    node_id: str = Field(min_length=1)


class _Explanation(BaseModel):
    """The six public RFC-0147 result categories, without routing objects."""

    model_config = ConfigDict(extra="forbid", strict=True)
    capability: str
    local_only: StrictBool
    local_eligible: StrictBool
    eligible_remote_node_ids: list[Annotated[str, Field(min_length=1)]]
    remotes_excluded_by_local_only: StrictBool
    initial_selection: _LocalSelection | _RemoteSelection | None


def _parse(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = _ArgumentParser(
        prog="home-ai-cluster explain-active-routing",
        description="Explain static routing in the already-running ordinary cluster.",
    )
    parser.add_argument("--capability", required=True, metavar="CAPABILITY")
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument(
        "-j", "--json", action="store_true", help="Print the compact JSON result."
    )
    args = parser.parse_args(argv)
    if args.capability not in ACCEPTED_CAPABILITY_NAMES:
        raise _InvalidInput
    return args


def _failure(message: str, code: int) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code) from None


def _scalar(value: str | None) -> str:
    """Render one public scalar without allowing terminal control."""
    return "none" if value is None else json.dumps(value, ensure_ascii=True)


def _selection(selection: _LocalSelection | _RemoteSelection | None) -> str:
    if selection is None:
        return "none"
    if isinstance(selection, _LocalSelection):
        return "local"
    return f"declared remote {_scalar(selection.node_id)}"


def _format_report(result: _Explanation) -> str:
    """Project one validated routing explanation for a plain-text terminal."""
    remotes = (
        ", ".join(_scalar(node_id) for node_id in result.eligible_remote_node_ids)
        or "none"
    )
    return "\n".join(
        [
            "Active routing explanation",
            f"Capability: {result.capability}",
            f"Local only: {str(result.local_only).lower()}",
            f"Local eligible: {str(result.local_eligible).lower()}",
            f"Eligible declared remotes: {remotes}",
            (
                "Remotes excluded by local-only: "
                f"{str(result.remotes_excluded_by_local_only).lower()}"
            ),
            f"Initial selection: {_selection(result.initial_selection)}",
            "No selectable candidate: "
            f"{'yes' if result.initial_selection is None else 'no'}",
        ]
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
) -> None:
    """Send one request, validate one result, and write one bounded outcome."""
    try:
        args = _parse(argv)
    except _InvalidInput:
        _failure(_INVALID_INPUT, 2)

    try:
        with _client_factory(
            timeout=_TIMEOUT_SECONDS, follow_redirects=False, trust_env=False
        ) as client:
            response = client.post(
                _URL,
                json={"capability": args.capability, "local_only": args.local_only},
            )
    except (httpx.ConnectError, httpx.TimeoutException):
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
        result = _Explanation.model_validate(response.json())
        if result.capability != args.capability or result.local_only != args.local_only:
            raise ValueError("response does not match request")
        selection = result.initial_selection
        if result.remotes_excluded_by_local_only != (
            result.local_only and bool(result.eligible_remote_node_ids)
        ):
            raise ValueError("remote exclusion does not match eligible candidates")
        if result.local_eligible:
            if not isinstance(selection, _LocalSelection):
                raise ValueError("eligible local candidate must be selected")
        elif not result.local_only and result.eligible_remote_node_ids:
            if not isinstance(selection, _RemoteSelection) or (
                selection.node_id != result.eligible_remote_node_ids[0]
            ):
                raise ValueError("first eligible remote candidate must be selected")
        elif selection is not None:
            raise ValueError("no candidate is selectable")
    except (ValidationError, ValueError, TypeError):
        _failure(_INVALID_RESPONSE, 1)
    except Exception:
        _failure(_FAILED, 1)

    try:
        output = (
            json.dumps(result.model_dump(), separators=(",", ":"))
            if args.json
            else _format_report(result)
        )
    except Exception:
        _failure(_FAILED, 1)
    sys.stdout.write(output + "\n")
