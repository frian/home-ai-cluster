"""One-shot RFC-0080 whole-file caller edge."""

import argparse
import json
import os
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from pydantic import ValidationError

from home_ai_cluster import chat_command, code_command
from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
)

_SYSTEM_INSTRUCTION = (
    'Return exactly one JSON object with exactly the keys "version" and "content": '
    '{"version":1,"content":"..."}. "content" must be the complete replacement '
    "text. Return no Markdown, prose, path, filename, language, patch, or additional "
    "fields."
)
_MAX_CONTENT_BYTES = 65_536
_INVALID_TARGET = "error: invalid code-file target"
_INVALID_RESPONSE = "error: invalid code-file response"
_REPLACEMENT_FAILED = "error: code-file replacement failed"


@dataclass(frozen=True)
class _CodeFileInput:
    target: Path
    message: str
    timeout_seconds: float


class _ArgumentParser(argparse.ArgumentParser):
    """Convert parser failures into the existing native input boundary."""

    def error(self, message: str) -> None:
        raise chat_command._InvalidRequestInput from None


class _InvalidEnvelope(ValueError):
    """Raised for a response outside RFC-0080's closed JSON envelope."""


def _parse_input(argv: Sequence[str] | None) -> _CodeFileInput:
    parser = _ArgumentParser(prog="home-ai-cluster code-file")
    parser.add_argument("--file", action="append")
    parser.add_argument("message_positional", nargs="?")
    parser.add_argument("--message", action="append")
    parser.add_argument("--timeout-seconds")
    args = parser.parse_args(argv)

    targets = args.file or []
    option_messages = args.message or []
    if args.message_positional is not None:
        if option_messages:
            raise chat_command._InvalidRequestInput
        message = args.message_positional
    elif len(option_messages) == 1:
        message = option_messages[0]
    else:
        raise chat_command._InvalidRequestInput

    if len(targets) != 1 or not message.strip():
        raise chat_command._InvalidRequestInput
    try:
        timeout_seconds = (
            chat_command._REQUEST_TIMEOUT_SECONDS
            if args.timeout_seconds is None
            else chat_command._parse_timeout_seconds(args.timeout_seconds)
        )
    except ValueError:
        raise chat_command._InvalidRequestInput from None
    return _CodeFileInput(Path(targets[0]), message, timeout_seconds)


def _read_target(target: Path) -> tuple[str, int]:
    """Read one existing non-symlink UTF-8 file without newline conversion."""
    try:
        if target.is_symlink() or not target.is_file():
            raise OSError
        mode = target.stat().st_mode & 0o777
        with target.open("r", encoding="utf-8", errors="strict", newline="") as source:
            return source.read(), mode
    except (OSError, UnicodeError):
        raise ValueError from None


def _create_missing_target(target: Path) -> int:
    """Create one selected empty leaf exclusively and return its ordinary mode."""
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    except OSError:
        raise ValueError from None
    try:
        os.close(descriptor)
        return target.stat().st_mode & 0o777
    except OSError:
        raise ValueError from None


def _native_request(instruction: str, current_content: str) -> dict[str, Any]:
    request = ClusterRequest(
        messages=[
            ChatMessage(role="system", content=_SYSTEM_INSTRUCTION),
            ChatMessage(
                role="user",
                content=json.dumps(
                    {"instruction": instruction, "current_content": current_content},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            ),
        ],
        capability=Capability(name="code"),
    )
    return {
        "messages": [message.model_dump() for message in request.messages],
        "capability": request.capability.name,
    }


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _InvalidEnvelope
        result[key] = value
    return result


def _replacement_content(value: str) -> str:
    try:
        envelope = json.loads(value, object_pairs_hook=_object_without_duplicate_keys)
    except (json.JSONDecodeError, _InvalidEnvelope):
        raise _InvalidEnvelope from None
    if (
        type(envelope) is not dict
        or set(envelope) != {"version", "content"}
        or type(envelope["version"]) is not int
        or envelope["version"] != 1
        or type(envelope["content"]) is not str
    ):
        raise _InvalidEnvelope
    return envelope["content"]


def _atomic_replace(
    target: Path,
    content: bytes,
    mode: int,
    *,
    mkstemp: Callable[..., tuple[int, str]] = tempfile.mkstemp,
    fdopen: Callable[..., Any] = os.fdopen,
    fsync: Callable[[int], None] = os.fsync,
    chmod: Callable[[str, int], None] = os.chmod,
    replace: Callable[[str, Path], None] = os.replace,
    unlink: Callable[[str], None] = os.unlink,
) -> bool:
    """Prepare one private sibling completely before its sole replacement."""
    temporary_name: str | None = None
    descriptor: int | None = None
    try:
        descriptor, temporary_name = mkstemp(
            prefix=".hac-code-file-", dir=target.parent
        )
        with fdopen(descriptor, "wb") as temporary:
            descriptor = None
            temporary.write(content)
            temporary.flush()
            fsync(temporary.fileno())
        chmod(temporary_name, mode & 0o777)
        replace(temporary_name, target)
        temporary_name = None
        return True
    except OSError:
        return False
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary_name is not None:
            try:
                unlink(temporary_name)
            except OSError:
                pass


def main(
    argv: Sequence[str] | None = None,
    *,
    _client_factory: Callable[..., httpx.Client] = httpx.Client,
) -> None:
    """Replace one selected file from exactly one validated native result."""
    try:
        command_input = _parse_input(argv)
    except chat_command._InvalidRequestInput:
        chat_command._exit_with_failure(chat_command._INVALID_INPUT, 2)

    if command_input.target.is_symlink():
        chat_command._exit_with_failure(_INVALID_TARGET, 1)
    if command_input.target.exists():
        try:
            current_content, mode = _read_target(command_input.target)
        except ValueError:
            chat_command._exit_with_failure(_INVALID_TARGET, 1)
        try:
            request = _native_request(command_input.message, current_content)
        except ValueError:
            chat_command._exit_with_failure(chat_command._INVALID_INPUT, 2)
    else:
        if not command_input.target.parent.is_dir():
            chat_command._exit_with_failure(_INVALID_TARGET, 1)
        try:
            request = _native_request(command_input.message, "")
        except ValueError:
            chat_command._exit_with_failure(chat_command._INVALID_INPUT, 2)
        try:
            mode = _create_missing_target(command_input.target)
        except ValueError:
            chat_command._exit_with_failure(_INVALID_TARGET, 1)

    try:
        response = chat_command._post_native_request(
            request,
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

    failure = code_command._failure_for_status(response.status_code)
    if failure is not None:
        chat_command._exit_with_failure(failure, 1)
    try:
        result = ClusterResult.model_validate(response.json())
    except (ValidationError, ValueError):
        chat_command._exit_with_failure(chat_command._INVALID_CLUSTER_RESPONSE, 1)
    except Exception:
        chat_command._exit_with_failure(chat_command._ORDINARY_REQUEST_FAILED, 1)
    try:
        replacement = _replacement_content(result.content)
        replacement_bytes = replacement.encode("utf-8", errors="strict")
        if len(replacement_bytes) > _MAX_CONTENT_BYTES:
            raise ValueError
    except (UnicodeError, ValueError):
        chat_command._exit_with_failure(_INVALID_RESPONSE, 1)

    if not _atomic_replace(command_input.target, replacement_bytes, mode):
        chat_command._exit_with_failure(_REPLACEMENT_FAILED, 1)
