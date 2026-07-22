"""Tests for the additive RFC-0050 root command."""

from pathlib import Path

import pytest

from home_ai_cluster import command

HELP = """usage: home-ai-cluster <command> [arguments...]

Foreground process commands:
  local           Run one local runtime process.
  static-cluster  Run one static-cluster process.
  compatibility   Run one loopback compatibility process.

Finite commands:
  chat            Send one ordinary chat request.
  preflight       Inspect static declaration coherence.
  health          Observe local runtime health.
  status          Inspect static-cluster status.

Use 'home-ai-cluster <command> --help' for command-specific help.
"""


def test_project_script_entry_exists() -> None:
    project = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'home-ai-cluster = "home_ai_cluster.command:main"' in project


@pytest.mark.parametrize("argv", ([], ["--help"]))
def test_no_arguments_and_help_emit_static_root_help(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    command.main(argv)

    captured = capsys.readouterr()

    assert captured.out == HELP
    assert captured.err == ""


def test_version_emits_only_installed_package_version(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(command, "version", lambda name: "9.8.7")

    command.main(["--version"])

    captured = capsys.readouterr()

    assert captured.out == "9.8.7\n"
    assert captured.err == ""


@pytest.mark.parametrize(
    "argv",
    (
        ["unknown"],
        ["--unknown"],
        ["--help", "extra"],
        ["loc"],
        ["openai"],
        ["static-proof"],
        ["history"],
        ["explain-routing"],
    ),
)
def test_invalid_root_forms_use_the_exact_unknown_command_failure(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as raised:
        command.main(argv)

    captured = capsys.readouterr()

    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == "error: unknown command\n"


@pytest.mark.parametrize(
    ("name", "arguments"),
    (
        ("local", ["--runtime", "ollama"]),
        ("static-cluster", ["--declaration", "cluster.toml"]),
        ("compatibility", ["--declaration", "cluster.toml"]),
        ("chat", ["--message", "Hello"]),
        ("preflight", ["--json"]),
        ("health", ["--json"]),
        ("status", ["--declaration", "cluster.toml", "--json"]),
    ),
)
def test_subcommands_delegate_the_exact_remaining_arguments(
    name: str, arguments: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    received: list[tuple[str, list[str]]] = []

    def make_delegate(command_name: str):
        def delegate(argv: list[str] | None = None) -> None:
            assert argv is not None
            received.append((command_name, argv))

        return delegate

    for command_name in command._COMMANDS:
        monkeypatch.setitem(
            command._COMMANDS, command_name, make_delegate(command_name)
        )

    command.main([name, *arguments])

    assert received == [(name, arguments)]


def test_subcommand_system_exit_propagates_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def delegate(argv: list[str] | None = None) -> None:
        raise SystemExit(17)

    monkeypatch.setitem(command._COMMANDS, "chat", delegate)

    with pytest.raises(SystemExit) as raised:
        command.main(["chat", "--message", "Hello"])

    assert raised.value.code == 17


@pytest.mark.parametrize(
    ("name", "target"),
    (
        ("local", command.local_runtime.main),
        ("static-cluster", command.static_cluster.main),
        ("compatibility", command.openai_compatibility.main),
        ("chat", command.chat_command.main),
        ("preflight", command.static_preflight.main),
        ("health", command.local_health_snapshot.main),
        ("status", command.status_command.main),
    ),
)
def test_dispatch_table_uses_existing_command_main_functions(name: str, target) -> None:
    assert command._COMMANDS[name] is target
