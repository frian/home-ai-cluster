"""Regression coverage for clean root-command interruption."""

import pytest

from home_ai_cluster import command


def test_root_command_keyboard_interrupt_exits_130_without_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def interrupted(_: list[str] | None = None) -> None:
        raise KeyboardInterrupt

    monkeypatch.setitem(command._COMMANDS, "summarize", interrupted)

    with pytest.raises(SystemExit) as raised:
        command.main(["summarize", "--text", "Source text"])

    captured = capsys.readouterr()

    assert raised.value.code == 130
    assert captured.out == ""
    assert captured.err == ""


def test_root_local_receiver_keyboard_interrupt_exits_130_without_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def interrupted(_: list[str] | None = None) -> None:
        raise KeyboardInterrupt

    monkeypatch.setitem(command._COMMANDS, "local", interrupted)

    with pytest.raises(SystemExit) as raised:
        command.main(["local", "--receiver-host", "192.0.2.10"])

    captured = capsys.readouterr()

    assert raised.value.code == 130
    assert captured.out == ""
    assert captured.err == ""
