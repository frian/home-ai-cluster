"""Bounded prompt-free local history for explicit request accounts."""

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

HISTORY_DIRECTORY = "home-ai-cluster"
HISTORY_FILENAME = "request-history.jsonl"
HISTORY_LIMIT = 50
RECORD_KEYS = (
    "status",
    "requested_capability",
    "selected_candidate_family",
    "outcome_rule",
    "failure_status",
)
FAILURE_STATUSES = {
    "no-selectable-candidate",
    "runtime-unavailable",
    "execution-failed",
}
READ_FAILURE_MESSAGE = "error: unable to read request history"
CLEAR_FAILURE_MESSAGE = "error: unable to clear request history"


def history_file() -> Path:
    """Return the RFC-0035 local state file without creating it."""
    state_home = os.environ.get("XDG_STATE_HOME")
    if state_home is None:
        state_home = str(Path(os.environ["HOME"]) / ".local" / "state")
    return Path(state_home) / HISTORY_DIRECTORY / HISTORY_FILENAME


def record_for_account(account: Mapping[str, Any]) -> dict[str, str | None]:
    """Derive the only five account fields RFC-0035 permits retaining."""
    routing = account["routing"]
    failure = account["failure"]
    if not isinstance(routing, Mapping):
        raise ValueError("request account routing must be an object")
    if failure is not None and not isinstance(failure, Mapping):
        raise ValueError("request account failure must be an object or null")

    record = {
        "status": account["status"],
        "requested_capability": routing["requested_capability"],
        "selected_candidate_family": routing["selected_candidate_family"],
        "outcome_rule": routing["outcome_rule"],
        "failure_status": None if failure is None else failure["status"],
    }
    if not _valid_record(record):
        raise ValueError("request account cannot produce a valid history record")
    return record


def record_account(account: Mapping[str, Any]) -> None:
    """Append one allowlisted record with bounded full-file replacement.

    Concurrent explicit writers may race; RFC-0035 intentionally adds no locking.
    """
    path = history_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    records = read_valid_records(path)
    records.append(record_for_account(account))
    _replace_records(path, records[-HISTORY_LIMIT:])


def read_valid_records(path: Path | None = None) -> list[dict[str, str | None]]:
    """Read valid records oldest first, silently omitting malformed lines."""
    file_path = path or history_file()
    try:
        with file_path.open(encoding="utf-8", errors="replace") as history:
            return [
                record
                for line in history
                if (record := _record_from_line(line)) is not None
            ]
    except FileNotFoundError:
        return []


def _record_from_line(line: str) -> dict[str, str | None] | None:
    if not line.strip():
        return None
    try:
        value = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict) or not _valid_record(value):
        return None
    return {key: value[key] for key in RECORD_KEYS}


def _valid_record(record: Mapping[str, object]) -> bool:
    if list(record) != list(RECORD_KEYS) and set(record) != set(RECORD_KEYS):
        return False
    if record["status"] not in {"succeeded", "failed"}:
        return False
    if not isinstance(record["requested_capability"], str):
        return False
    if not _nullable_string(record["selected_candidate_family"]):
        return False
    if not isinstance(record["outcome_rule"], str):
        return False
    failure_status = record["failure_status"]
    if failure_status is not None and failure_status not in FAILURE_STATUSES:
        return False
    return (record["status"] == "succeeded") == (failure_status is None)


def _nullable_string(value: object) -> bool:
    return value is None or isinstance(value, str)


def _replace_records(path: Path, records: list[dict[str, str | None]]) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".request-history-",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            os.chmod(temporary_path, 0o600)
            for record in records:
                temporary.write(json.dumps(record, separators=(",", ":")) + "\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def history_main(argv: Sequence[str] | None = None) -> None:
    """Emit valid history records newest first."""
    _parse_no_options("home-ai-cluster-history", argv)
    try:
        records = read_valid_records()
    except OSError as error:
        print(READ_FAILURE_MESSAGE, file=sys.stderr)
        raise SystemExit(1) from error
    print(json.dumps(list(reversed(records)), separators=(",", ":")))


def clear_history() -> None:
    """Remove only the RFC-0035 state file when it is present."""
    try:
        history_file().unlink()
    except FileNotFoundError:
        pass


def clear_history_main(argv: Sequence[str] | None = None) -> None:
    """Clear the explicit local request history."""
    _parse_no_options("home-ai-cluster-clear-history", argv)
    try:
        clear_history()
    except OSError as error:
        print(CLEAR_FAILURE_MESSAGE, file=sys.stderr)
        raise SystemExit(1) from error
    print('{"cleared":true}')


def _parse_no_options(prog: str, argv: Sequence[str] | None) -> None:
    argparse.ArgumentParser(prog=prog).parse_args(argv)
