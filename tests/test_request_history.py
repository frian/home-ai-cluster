import json
import stat
from pathlib import Path

import pytest

import home_ai_cluster.request_history as request_history
from home_ai_cluster.request_history import (
    CLEAR_FAILURE_MESSAGE,
    HISTORY_LIMIT,
    READ_FAILURE_MESSAGE,
    clear_history_main,
    history_file,
    history_main,
    read_valid_records,
    record_account,
    record_for_account,
)


def successful_account(capability: str = "chat") -> dict[str, object]:
    return {
        "status": "succeeded",
        "routing": {
            "requested_capability": capability,
            "selected_candidate_family": "local",
            "outcome_rule": "local-only",
            "selected_node_id": "private-node",
            "failure_reason": None,
        },
        "result": {
            "content": "generated private response",
            "adapter": "ollama",
            "model": "private-model",
            "node_id": "private-node",
        },
        "failure": None,
    }


def failed_account() -> dict[str, object]:
    return {
        "status": "failed",
        "routing": {
            "requested_capability": "vision",
            "selected_candidate_family": None,
            "outcome_rule": "no-selectable-candidate",
            "selected_node_id": None,
            "failure_reason": "private stable failure reason",
        },
        "result": None,
        "failure": {
            "status": "no-selectable-candidate",
            "reason": "private stable failure reason",
        },
    }


def use_temporary_state(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setenv("HOME", "/not-the-real-home")


def test_history_file_uses_xdg_state_home_without_creating_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    use_temporary_state(monkeypatch, tmp_path)

    path = history_file()

    assert path == tmp_path / "home-ai-cluster" / "request-history.jsonl"
    assert not path.parent.exists()


def test_history_file_uses_home_fallback_when_xdg_state_home_is_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    assert history_file() == (
        tmp_path / ".local" / "state" / "home-ai-cluster" / "request-history.jsonl"
    )


def test_record_derives_only_the_approved_success_fields() -> None:
    record = record_for_account(successful_account())

    assert list(record) == [
        "status",
        "requested_capability",
        "selected_candidate_family",
        "outcome_rule",
        "failure_status",
    ]
    assert record == {
        "status": "succeeded",
        "requested_capability": "chat",
        "selected_candidate_family": "local",
        "outcome_rule": "local-only",
        "failure_status": None,
    }
    serialized = json.dumps(record)
    for forbidden in (
        "generated private response",
        "private-node",
        "ollama",
        "private-model",
        "timestamp",
        "identifier",
    ):
        assert forbidden not in serialized


def test_record_derives_failed_status_without_failure_reason() -> None:
    record = record_for_account(failed_account())

    assert record == {
        "status": "failed",
        "requested_capability": "vision",
        "selected_candidate_family": None,
        "outcome_rule": "no-selectable-candidate",
        "failure_status": "no-selectable-candidate",
    }
    assert "private stable failure reason" not in json.dumps(record)


def test_recording_creates_owner_only_compact_jsonl_in_temporary_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    use_temporary_state(monkeypatch, tmp_path)

    record_account(successful_account())

    path = history_file()
    expected = record_for_account(successful_account())
    assert (
        path.read_text(encoding="utf-8")
        == json.dumps(expected, separators=(",", ":")) + "\n"
    )
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_record_account_has_only_the_explicit_actual_request_production_writer() -> (
    None
):
    source_directory = Path(request_history.__file__).parent
    writers = [
        path.name
        for path in source_directory.rglob("*.py")
        if path.name != "request_history.py"
        and "record_account(" in path.read_text(encoding="utf-8")
    ]

    assert writers == ["actual_request_explanation.py"]


def test_recording_keeps_newest_fifty_records_oldest_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    use_temporary_state(monkeypatch, tmp_path)

    for number in range(HISTORY_LIMIT + 3):
        record_account(successful_account(f"capability-{number}"))

    stored = read_valid_records()

    assert len(stored) == HISTORY_LIMIT
    assert stored[0]["requested_capability"] == "capability-3"
    assert stored[-1]["requested_capability"] == f"capability-{HISTORY_LIMIT + 2}"


def test_recording_omits_invalid_existing_lines_and_uses_same_directory_tempfile(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    use_temporary_state(monkeypatch, tmp_path)
    path = history_file()
    path.parent.mkdir(parents=True)
    valid = record_for_account(successful_account("kept"))
    path.write_text(
        "\n".join(
            [
                json.dumps(valid),
                "not json",
                json.dumps({"status": "succeeded"}),
                json.dumps({**valid, "unexpected": "field"}),
                json.dumps({**valid, "status": "invalid"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    replacement_paths: list[tuple[object, object]] = []
    replace = request_history.os.replace

    def record_replace(source: object, target: object) -> None:
        replacement_paths.append((source, target))
        replace(source, target)

    monkeypatch.setattr(request_history.os, "replace", record_replace)

    record_account(successful_account("new"))

    assert read_valid_records() == [
        record_for_account(successful_account("kept")),
        record_for_account(successful_account("new")),
    ]
    assert len(replacement_paths) == 1
    assert request_history.Path(replacement_paths[0][0]).parent == path.parent
    assert replacement_paths[0][1] == path


def test_history_command_returns_newest_records_first_and_compact_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    use_temporary_state(monkeypatch, tmp_path)
    record_account(successful_account("older"))
    record_account(failed_account())

    history_main([])

    captured = capsys.readouterr()
    assert json.loads(captured.out) == [
        record_for_account(failed_account()),
        record_for_account(successful_account("older")),
    ]
    assert (
        captured.out
        == json.dumps(json.loads(captured.out), separators=(",", ":")) + "\n"
    )
    assert captured.err == ""


@pytest.mark.parametrize("contents", ["", "not json\n", '{"status":"failed"}\n'])
def test_history_command_returns_empty_for_missing_or_wholly_invalid_history(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
    contents: str,
) -> None:
    use_temporary_state(monkeypatch, tmp_path)
    if contents:
        path = history_file()
        path.parent.mkdir(parents=True)
        path.write_text(contents, encoding="utf-8")

    history_main([])

    captured = capsys.readouterr()
    assert captured.out == "[]\n"
    assert captured.err == ""


def test_history_command_reports_safe_error_without_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail_read() -> list[dict[str, str | None]]:
        raise PermissionError("/private/state request-history.jsonl")

    monkeypatch.setattr(request_history, "read_valid_records", fail_read)

    with pytest.raises(SystemExit) as raised:
        history_main([])

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == ""
    assert captured.err == READ_FAILURE_MESSAGE + "\n"
    assert "/private" not in captured.err


def test_clear_history_handles_existing_and_missing_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    use_temporary_state(monkeypatch, tmp_path)
    record_account(successful_account())

    clear_history_main([])
    first = capsys.readouterr()
    clear_history_main([])
    second = capsys.readouterr()

    assert first.out == '{"cleared":true}\n'
    assert first.err == ""
    assert second.out == '{"cleared":true}\n'
    assert second.err == ""
    assert not history_file().exists()


def test_clear_history_reports_safe_error_without_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail_clear() -> None:
        raise PermissionError("/private/state request-history.jsonl")

    monkeypatch.setattr(request_history, "clear_history", fail_clear)

    with pytest.raises(SystemExit) as raised:
        clear_history_main([])

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == ""
    assert captured.err == CLEAR_FAILURE_MESSAGE + "\n"
    assert "/private" not in captured.err


@pytest.mark.parametrize("command", [history_main, clear_history_main])
def test_history_commands_accept_no_options(
    command, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        command(["--unexpected"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err
