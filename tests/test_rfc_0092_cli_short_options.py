"""Focused CLI-contract tests for accepted RFC-0092."""

from pathlib import Path

import pytest

from home_ai_cluster import (
    command,
    local_health_snapshot,
    openai_compatibility,
    static_cluster,
)
from home_ai_cluster.commands import (
    aider_command,
    chat_command,
    classify_command,
    code_command,
    code_file_command,
    external_information_command,
    static_preflight,
    status_command,
    summarize_command,
)


def test_root_short_help_matches_long_help(capsys: pytest.CaptureFixture[str]) -> None:
    command.main(["--help"])
    long = capsys.readouterr()
    command.main(["-h"])
    short = capsys.readouterr()

    assert short == long


def test_root_short_help_with_extra_argument_remains_invalid(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as raised:
        command.main(["-h", "extra"])
    assert raised.value.code == 2
    assert capsys.readouterr().err == "error: unknown command\n"


def test_file_aliases_normalize_like_long_forms(tmp_path: Path) -> None:
    target = tmp_path / "source.txt"
    target.write_text("source", encoding="utf-8")

    assert aider_command._parse_input(["-f", "target.py", "request"]) == (
        aider_command._parse_input(["--file", "target.py", "request"])
    )
    assert code_file_command._parse_input(["-f", "target.py", "request"]) == (
        code_file_command._parse_input(["--file", "target.py", "request"])
    )
    assert summarize_command._parse_input(["-f", str(target)]) == (
        summarize_command._parse_input(["--file", str(target)])
    )
    assert classify_command._parse_input(
        ["-f", str(target), "--label", "one", "--label", "two"]
    ) == classify_command._parse_input(
        ["--file", str(target), "--label", "one", "--label", "two"]
    )


def test_declaration_aliases_normalize_like_long_forms() -> None:
    assert static_cluster.parse_args(["-d", "cluster.toml"]).declaration == Path(
        "cluster.toml"
    )
    assert openai_compatibility.parse_args(["-d", "cluster.toml"]).declaration == Path(
        "cluster.toml"
    )
    assert static_preflight.parse_args(["-d", "cluster.toml"]).declaration == Path(
        "cluster.toml"
    )
    _, status = status_command.parse_args(["-d", "cluster.toml"])
    assert status.declaration == Path("cluster.toml")


def test_short_declaration_retains_inline_topology_conflict() -> None:
    with pytest.raises(SystemExit):
        static_cluster.parse_args(["-d", "cluster.toml", "--remote-node-id", "remote"])


def test_repeated_label_alias_preserves_order() -> None:
    parsed = classify_command._parse_input(
        ["--text", "source", "-l", "first", "-l", "second"]
    )
    assert parsed.request.labels == ["first", "second"]


def test_json_aliases_select_existing_json_mode(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("source", encoding="utf-8")

    assert chat_command._parse_input(["message", "-j"]).output_mode == "json"
    assert code_command._parse_input(["message", "-j"]).output_mode == "json"
    assert (
        external_information_command._parse_input(
            ["--plugin", "plugin", "query", "question", "-j"]
        ).output_mode
        == "json"
    )
    assert (
        summarize_command._parse_input(["-f", str(source), "-j"]).output_mode == "json"
    )
    assert (
        classify_command._parse_input(
            ["-f", str(source), "-l", "one", "-l", "two", "-j"]
        ).output_mode
        == "json"
    )
    assert static_preflight.parse_args(["-j"]).json is True
    assert local_health_snapshot.parse_args(["-j"]).json is True
    _, status = status_command.parse_args(["-d", "cluster.toml", "-j"])
    assert status.json is True


@pytest.mark.parametrize(
    ("parse", "argv", "error"),
    [
        (
            chat_command._parse_input,
            ["message", "-j", "-v"],
            chat_command._InvalidRequestInput,
        ),
        (
            code_command._parse_input,
            ["message", "-j", "-v"],
            chat_command._InvalidRequestInput,
        ),
        (
            external_information_command._parse_input,
            ["--plugin", "plugin", "query", "question", "-j", "-v"],
            external_information_command._InvalidRequestInput,
        ),
        (
            summarize_command._parse_input,
            ["--text", "source", "-j", "-v"],
            summarize_command._InvalidRequestInput,
        ),
        (
            classify_command._parse_input,
            ["--text", "source", "-l", "one", "-l", "two", "-j", "-v"],
            classify_command._InvalidRequestInput,
        ),
    ],
)
def test_json_alias_remains_mutually_exclusive_with_verbose(
    parse: object, argv: list[str], error: type[Exception]
) -> None:
    with pytest.raises(error):
        parse(argv)  # type: ignore[operator]


@pytest.mark.parametrize(
    "parse", [chat_command._parse_input, code_command._parse_input]
)
def test_no_message_json_alias_retains_interactive_rejection(parse: object) -> None:
    with pytest.raises(chat_command._InvalidRequestInput):
        parse(["-j"])  # type: ignore[operator]
