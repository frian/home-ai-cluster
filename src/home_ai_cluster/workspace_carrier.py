"""Bounded one-shot machine carrier for RFC-0114 workspace authority."""

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any, BinaryIO, NoReturn, TextIO

from home_ai_cluster.core.workspace_authority import (
    WorkspaceAuthority,
    WorkspaceAuthorityError,
)

_MAX_INPUT_BYTES = 8 * 1024 * 1024
_MAX_OUTPUT_BYTES = 8 * 1024 * 1024
_OPERATIONS = frozenset({"list", "read", "write"})
_INVALID_REQUEST = {"ok": False, "error": "invalid request"}
_REFUSED_REQUEST = {"ok": False, "error": "workspace request refused"}


class _StartupError(Exception):
    """Raised for invalid trusted carrier construction input."""


class _RequestError(Exception):
    """Raised for invalid untrusted carrier request input."""


class _ResponseError(Exception):
    """Raised when one complete bounded response cannot be delivered."""


class _ArgumentParser(argparse.ArgumentParser):
    """Reject every spelling outside the accepted startup surface."""

    def error(self, message: str) -> NoReturn:
        raise _StartupError from None


def _parse_startup(argv: Sequence[str] | None) -> tuple[str, frozenset[str]]:
    parser = _ArgumentParser(
        prog="home-ai-cluster-workspace-carrier",
        add_help=False,
        allow_abbrev=False,
    )
    parser.add_argument("--root", action="append")
    parser.add_argument("--grant", action="append")
    arguments = parser.parse_args(argv)

    roots = arguments.root or []
    grants = arguments.grant or []
    if (
        len(roots) != 1
        or not grants
        or any(grant not in _OPERATIONS for grant in grants)
    ):
        raise _StartupError
    return roots[0], frozenset(grants)


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise _RequestError
        result[name] = value
    return result


def _reject_non_json_constant(value: str) -> NoReturn:
    raise _RequestError


def _read_request(source: BinaryIO) -> dict[str, Any]:
    payload = bytearray()
    while len(payload) <= _MAX_INPUT_BYTES:
        try:
            chunk = source.read(_MAX_INPUT_BYTES + 1 - len(payload))
        except (OSError, TypeError, ValueError):
            raise _RequestError from None
        if chunk is None:
            raise _RequestError
        if not isinstance(chunk, bytes):
            raise _RequestError
        if not chunk:
            break
        if len(chunk) > _MAX_INPUT_BYTES + 1 - len(payload):
            raise _RequestError
        payload.extend(chunk)
    if len(payload) > _MAX_INPUT_BYTES:
        raise _RequestError
    try:
        text = payload.decode("utf-8", errors="strict")
        request = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_non_json_constant,
        )
    except (UnicodeError, json.JSONDecodeError, _RequestError):
        raise _RequestError from None
    if not isinstance(request, dict):
        raise _RequestError
    return request


def _validate_request(request: dict[str, Any]) -> tuple[str, str, str | None]:
    operation = request.get("operation")
    if not isinstance(operation, str) or operation not in _OPERATIONS:
        raise _RequestError

    expected_fields = (
        {"operation", "path", "content"}
        if operation == "write"
        else {"operation", "path"}
    )
    if set(request) != expected_fields:
        raise _RequestError

    path = request["path"]
    if not isinstance(path, str):
        raise _RequestError

    content = request.get("content")
    if operation == "write" and not isinstance(content, str):
        raise _RequestError
    return operation, path, content


def _serialize_response(response: dict[str, Any]) -> bytes:
    try:
        payload = (
            json.dumps(
                response,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
    except (TypeError, ValueError, UnicodeError):
        raise _ResponseError from None
    if len(payload) > _MAX_OUTPUT_BYTES:
        raise _ResponseError
    return payload


def _write_payload(destination: BinaryIO, payload: bytes) -> None:
    try:
        offset = 0
        while offset < len(payload):
            written = destination.write(payload[offset:])
            if (
                type(written) is not int
                or written <= 0
                or written > len(payload) - offset
            ):
                raise _ResponseError
            offset += written
        destination.flush()
    except (OSError, TypeError, ValueError, _ResponseError):
        raise _ResponseError from None


def _write_normal_failure(destination: BinaryIO, response: dict[str, Any]) -> None:
    _write_payload(destination, _serialize_response(response))


def _diagnose(destination: TextIO, message: str) -> None:
    try:
        destination.write(message)
        destination.flush()
    except (OSError, ValueError):
        pass


def _request_failure(destination: BinaryIO, diagnostics: TextIO) -> int:
    try:
        _write_normal_failure(destination, _INVALID_REQUEST)
    except _ResponseError:
        _diagnose(diagnostics, "error: response delivery failed\n")
    return 1


def _authority_failure(destination: BinaryIO, diagnostics: TextIO) -> int:
    try:
        _write_normal_failure(destination, _REFUSED_REQUEST)
    except _ResponseError:
        _diagnose(diagnostics, "error: response delivery failed\n")
    return 1


def main(
    argv: Sequence[str] | None = None,
    *,
    _stdin: BinaryIO | None = None,
    _stdout: BinaryIO | None = None,
    _stderr: TextIO | None = None,
) -> int:
    """Run exactly one bounded workspace request and response attempt."""
    source = sys.stdin.buffer if _stdin is None else _stdin
    destination = sys.stdout.buffer if _stdout is None else _stdout
    diagnostics = sys.stderr if _stderr is None else _stderr

    try:
        root, grants = _parse_startup(argv)
        authority = WorkspaceAuthority(root, grants)
    except (SystemExit, _StartupError, WorkspaceAuthorityError):
        _diagnose(diagnostics, "error: invalid carrier startup\n")
        return 1
    except Exception:
        _diagnose(diagnostics, "error: carrier startup failed\n")
        return 1

    try:
        request = _read_request(source)
        operation, path, content = _validate_request(request)
    except _RequestError:
        return _request_failure(destination, diagnostics)
    except Exception:
        _diagnose(diagnostics, "error: carrier request failed\n")
        return 1

    if operation == "write":
        try:
            success_payload = _serialize_response({"ok": True})
        except _ResponseError:
            _diagnose(diagnostics, "error: response serialization failed\n")
            return 1
        try:
            authority.write(path, content)
        except WorkspaceAuthorityError:
            return _authority_failure(destination, diagnostics)
        except Exception:
            _diagnose(diagnostics, "error: workspace operation failed\n")
            return 1
        try:
            _write_payload(destination, success_payload)
        except _ResponseError:
            _diagnose(diagnostics, "error: response delivery failed\n")
            return 1
        return 0

    try:
        if operation == "list":
            entries = authority.list(path)
            response = {
                "ok": True,
                "entries": [
                    {"name": entry.name, "kind": entry.kind} for entry in entries
                ],
            }
        else:
            response = {"ok": True, "content": authority.read(path)}
    except WorkspaceAuthorityError:
        return _authority_failure(destination, diagnostics)
    except Exception:
        _diagnose(diagnostics, "error: workspace operation failed\n")
        return 1

    try:
        success_payload = _serialize_response(response)
    except _ResponseError:
        return _authority_failure(destination, diagnostics)
    try:
        _write_payload(destination, success_payload)
    except _ResponseError:
        _diagnose(diagnostics, "error: response delivery failed\n")
        return 1
    return 0
