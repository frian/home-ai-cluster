"""Tests for the bounded retained-configuration command."""

import json
import os
from pathlib import Path

import pytest

from home_ai_cluster import local_runtime_composition
from home_ai_cluster.commands import (
    config_command,
    external_information_command,
)
from home_ai_cluster.local_runtime_composition import LocalRuntimeCompositionValues
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedConfigurationError,
    RetainedLocalConfiguration,
    load_retained_configuration,
    retained_configuration_file,
    save_retained_configuration,
)
from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration


def _run(capsys: pytest.CaptureFixture[str], argv: list[str]) -> tuple[int, str, str]:
    try:
        config_command.main(argv)
    except SystemExit as error:
        code = error.code
    else:
        code = 0
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))


@pytest.mark.parametrize("argv", ([], ["--help"], ["-h"]))
def test_config_discovery_shows_exactly_the_bounded_surfaces(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(capsys, argv)
    assert code == 0
    assert err == ""
    assert "{local,node,external-information,chat,reset,show}" in out
    assert "edit" not in out


def test_bare_config_discovery_does_not_access_retained_state(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("bare config discovery must not access retained state")

    monkeypatch.setattr(config_command, "load_retained_configuration", forbidden)
    monkeypatch.setattr(config_command, "save_retained_configuration", forbidden)
    monkeypatch.setattr(config_command, "remove_retained_configuration", forbidden)

    code, out, err = _run(capsys, [])
    assert code == 0
    assert err == ""
    assert "{local,node,external-information,chat,reset,show}" in out


@pytest.mark.parametrize("argv", (["unknown"], ["local"], ["node"]))
def test_concrete_or_unknown_config_actions_remain_parser_errors(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, err = _run(capsys, argv)
    assert code == 2
    assert out == ""
    assert "error:" in err


def test_show_empty_output_is_exact(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(capsys, ["show"]) == (
        0,
        "Local:\n  not configured\nRemote nodes:\n  none\n"
        "External information:\n  not configured\n"
        "Chat external information:\n  automatic fallback: not authorized\n",
        "",
    )


def test_show_does_not_construct_runtime_or_exercise_plugin_or_credential_authority(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    invoked: list[str] = []

    def forbidden(authority: str):
        def fail(*args: object, **kwargs: object) -> None:
            invoked.append(authority)
            raise AssertionError(f"config show must not use {authority}")

        return fail

    monkeypatch.setattr(
        local_runtime_composition,
        "create_local_runtime_composition",
        forbidden("runtime construction"),
    )
    monkeypatch.setattr(
        external_information_command.importlib.metadata,
        "entry_points",
        forbidden("plugin discovery"),
    )
    monkeypatch.setattr(
        os,
        "getenv",
        forbidden("provider credential lookup"),
    )

    assert _run(capsys, ["show"]) == (
        0,
        "Local:\n  not configured\nRemote nodes:\n  none\n"
        "External information:\n  not configured\n"
        "Chat external information:\n  automatic fallback: not authorized\n",
        "",
    )
    assert invoked == []


def test_show_rejects_unexpected_options(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, ["show", "--json"])
    assert code == 2
    assert out == ""
    assert "unrecognized arguments" in err


def test_whole_reset_removes_valid_configuration_and_show_is_empty(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(capsys, ["local", "--runtime", "ollama"])
    _run(capsys, ["node", "one", "--base-url", "http://192.0.2.1:25042"])
    _run(capsys, ["external-information", "--plugin", "tavily"])
    _run(capsys, ["chat", "--external-information-fallback"])

    assert _run(capsys, ["reset"]) == (0, "retained configuration reset\n", "")
    assert _run(capsys, ["show"]) == (
        0,
        "Local:\n  not configured\nRemote nodes:\n  none\n"
        "External information:\n  not configured\n"
        "Chat external information:\n  automatic fallback: not authorized\n",
        "",
    )


@pytest.mark.parametrize("contents", [b"not json", b'{"local":null}\n'])
def test_whole_reset_removes_unloadable_state_without_loading(
    capsys: pytest.CaptureFixture[str], contents: bytes
) -> None:
    path = retained_configuration_file()
    path.parent.mkdir(parents=True)
    path.write_bytes(contents)

    assert _run(capsys, ["reset"]) == (0, "retained configuration reset\n", "")
    assert not path.exists()


def test_whole_reset_does_not_load_retained_configuration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        config_command,
        "load_retained_configuration",
        lambda: (_ for _ in ()).throw(AssertionError("must not load retained state")),
    )

    assert _run(capsys, ["reset"]) == (0, "retained configuration reset\n", "")


def test_whole_reset_is_idempotent_without_creating_configuration_directory(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = retained_configuration_file()

    assert _run(capsys, ["reset"]) == (0, "retained configuration reset\n", "")
    assert not path.parent.exists()


def test_whole_reset_reports_bounded_removal_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        config_command,
        "remove_retained_configuration",
        lambda: (_ for _ in ()).throw(
            RetainedConfigurationError("unable to remove retained configuration")
        ),
    )

    assert _run(capsys, ["reset"]) == (
        1,
        "",
        "error: unable to remove retained configuration\n",
    )


@pytest.mark.parametrize(
    "argv",
    [
        ["local", "--reset"],
        ["node", "one", "--remove"],
        ["external-information", "--reset"],
        ["chat", "--reset"],
    ],
)
def test_selective_operations_keep_failing_on_unloadable_state(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    path = retained_configuration_file()
    path.parent.mkdir(parents=True)
    contents = b'{"local":null}\n'
    path.write_bytes(contents)

    code, out, err = _run(capsys, argv)

    assert (code, out, err) == (1, "", "error: invalid retained configuration shape\n")
    assert path.read_bytes() == contents


def test_show_reports_only_the_retained_external_information_plugin(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(capsys, ["external-information", "--plugin", "tavily"])

    assert _run(capsys, ["show"]) == (
        0,
        "Local:\n  not configured\nRemote nodes:\n  none\n"
        "External information:\n  plugin: tavily\n"
        "Chat external information:\n  automatic fallback: not authorized\n",
        "",
    )


def test_show_reports_chat_authorization_only_as_a_retained_fact(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(capsys, ["chat", "--external-information-fallback"])

    assert _run(capsys, ["show"]) == (
        0,
        "Local:\n  not configured\nRemote nodes:\n  none\n"
        "External information:\n  not configured\n"
        "Chat external information:\n  automatic fallback: authorized\n",
        "",
    )


def test_local_ollama_replacement_and_optional_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _run(
        capsys,
        [
            "local",
            "--runtime",
            "ollama",
            "--ollama-model",
            "a",
            "--ollama-disable-thinking",
            "--local-capability",
            "code",
        ],
    ) == (0, "local configuration retained\n", "")
    assert _run(capsys, ["local", "--runtime", "ollama", "--ollama-model", "b"]) == (
        0,
        "local configuration retained\n",
        "",
    )
    local = load_retained_configuration().local
    assert local == RetainedLocalConfiguration(
        runtime=LocalRuntimeCompositionValues(runtime="ollama", ollama_model="b"),
        local_capabilities=None,
    )


def test_local_runtime_validation_and_reset_conflicts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _run(capsys, ["local", "--ollama-model", "model"])[0] == 2
    assert _run(capsys, ["local", "--runtime", "llama-server"])[0] == 2
    assert (
        _run(capsys, ["local", "--runtime", "ollama", "--llama-server-model", "model"])[
            0
        ]
        == 2
    )
    assert _run(capsys, ["local", "--reset", "--runtime", "ollama"])[0] == 2
    assert _run(capsys, ["local", "--reset", "--execution-limit", "2"])[0] == 2


def test_local_execution_limit_is_retained_and_shown_as_retained_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _run(
        capsys,
        ["local", "--runtime", "ollama", "--execution-limit", "2"],
    ) == (0, "local configuration retained\n", "")
    assert load_retained_configuration().local is not None
    assert load_retained_configuration().local.execution_limit == 2
    assert "HAC execution limit: 2" in _run(capsys, ["show"])[1]

    _run(capsys, ["local", "--runtime", "ollama"])

    assert "HAC execution limit: not retained" in _run(capsys, ["show"])[1]


def test_llama_server_uses_existing_normalization(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _run(
        capsys,
        [
            "local",
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://127.0.0.1:8080/",
            "--llama-server-model",
            "model",
        ],
    ) == (0, "local configuration retained\n", "")
    assert load_retained_configuration().local == RetainedLocalConfiguration(
        runtime=LocalRuntimeCompositionValues(
            runtime="llama-server",
            llama_server_base_url="http://127.0.0.1:8080",
            llama_server_model="model",
        )
    )


def test_local_reset_is_idempotent_and_preserves_nodes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(capsys, ["local", "--runtime", "ollama"])
    _run(capsys, ["node", "one", "--base-url", "http://192.0.2.1:25042"])
    assert _run(capsys, ["local", "--reset"]) == (0, "local configuration reset\n", "")
    assert _run(capsys, ["local", "--reset"]) == (0, "local configuration reset\n", "")
    assert [node.node_id for node in load_retained_configuration().remote_nodes] == [
        "one"
    ]


def test_local_mutations_preserve_external_information_plugin(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(capsys, ["external-information", "--plugin", "tavily"])
    _run(capsys, ["local", "--runtime", "ollama"])
    _run(capsys, ["local", "--reset"])

    assert load_retained_configuration().external_information_plugin == "tavily"


def test_node_upsert_default_capabilities_and_order(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(capsys, ["node", "one", "--base-url", "http://192.0.2.1:25042"])
    _run(
        capsys,
        [
            "node",
            "two",
            "--base-url",
            "http://192.0.2.2:25042",
            "--capability",
            "code",
            "--capability",
            "chat",
        ],
    )
    assert _run(
        capsys,
        [
            "node",
            "one",
            "--base-url",
            "http://192.0.2.3:25042",
            "--capability",
            "classify",
        ],
    ) == (0, "node configuration retained\n", "")
    nodes = load_retained_configuration().remote_nodes
    assert [(node.node_id, node.base_url, node.capabilities) for node in nodes] == [
        ("one", "http://192.0.2.3:25042", ("classify",)),
        ("two", "http://192.0.2.2:25042", ("code", "chat")),
    ]


def test_node_remove_conflicts_and_unknown_node_fail(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        _run(
            capsys, ["node", "one", "--remove", "--base-url", "http://192.0.2.1:25042"]
        )[0]
        == 2
    )
    assert _run(capsys, ["node", "unknown", "--remove"]) == (
        1,
        "",
        "error: retained node not found\n",
    )


def test_node_removal_preserves_local_and_remaining_order(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(capsys, ["local", "--runtime", "ollama"])
    for node_id, url in (
        ("one", "http://192.0.2.1:25042"),
        ("two", "http://192.0.2.2:25042"),
        ("three", "http://192.0.2.3:25042"),
    ):
        _run(capsys, ["node", node_id, "--base-url", url])
    assert _run(capsys, ["node", "two", "--remove"]) == (
        0,
        "node configuration removed\n",
        "",
    )
    configuration = load_retained_configuration()
    assert configuration.local is not None
    assert [node.node_id for node in configuration.remote_nodes] == ["one", "three"]


def test_node_mutations_preserve_external_information_plugin(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(capsys, ["external-information", "--plugin", "tavily"])
    _run(capsys, ["node", "one", "--base-url", "http://192.0.2.1:25042"])
    _run(capsys, ["node", "one", "--base-url", "http://192.0.2.2:25042"])
    _run(capsys, ["node", "one", "--remove"])

    assert load_retained_configuration().external_information_plugin == "tavily"


def test_external_information_set_replace_reset_and_preservation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(capsys, ["local", "--runtime", "ollama"])
    _run(capsys, ["node", "one", "--base-url", "http://192.0.2.1:25042"])
    assert _run(capsys, ["external-information", "--plugin", "tavily"]) == (
        0,
        "external-information configuration retained\n",
        "",
    )
    assert _run(capsys, ["external-information", "--plugin", "searxng"]) == (
        0,
        "external-information configuration retained\n",
        "",
    )
    configuration = load_retained_configuration()
    assert configuration.external_information_plugin == "searxng"
    assert configuration.local is not None
    assert [node.node_id for node in configuration.remote_nodes] == ["one"]
    assert _run(capsys, ["external-information", "--reset"]) == (
        0,
        "external-information configuration reset\n",
        "",
    )
    assert _run(capsys, ["external-information", "--reset"]) == (
        0,
        "external-information configuration reset\n",
        "",
    )
    configuration = load_retained_configuration()
    assert configuration.external_information_plugin is None
    assert configuration.local is not None
    assert [node.node_id for node in configuration.remote_nodes] == ["one"]


@pytest.mark.parametrize(
    "argv",
    [
        ["external-information"],
        ["external-information", "--reset", "--plugin", "tavily"],
        ["external-information", "--plugin", "   "],
        ["external-information", "--plugin", "x" * 65],
    ],
)
def test_external_information_invalid_input_does_not_write(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    before = load_retained_configuration()

    assert _run(capsys, argv)[0] == 2
    assert load_retained_configuration() == before


def test_chat_authorization_set_reset_and_preservation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(capsys, ["local", "--runtime", "ollama"])
    _run(capsys, ["node", "one", "--base-url", "http://192.0.2.1:25042"])
    _run(capsys, ["external-information", "--plugin", "tavily"])

    assert _run(capsys, ["chat", "--external-information-fallback"]) == (
        0,
        "chat configuration retained\n",
        "",
    )
    assert _run(capsys, ["chat", "--external-information-fallback"]) == (
        0,
        "chat configuration retained\n",
        "",
    )
    configuration = load_retained_configuration()
    assert configuration.chat_external_information_fallback is True
    assert configuration.local is not None
    assert [node.node_id for node in configuration.remote_nodes] == ["one"]
    assert configuration.external_information_plugin == "tavily"

    assert _run(capsys, ["chat", "--reset"]) == (0, "chat configuration reset\n", "")
    assert _run(capsys, ["chat", "--reset"]) == (0, "chat configuration reset\n", "")
    assert load_retained_configuration().chat_external_information_fallback is False


@pytest.mark.parametrize(
    "argv",
    [
        ["chat"],
        ["chat", "--reset", "--external-information-fallback"],
    ],
)
def test_invalid_chat_configuration_does_not_write(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    before = load_retained_configuration()

    assert _run(capsys, argv)[0] == 2
    assert load_retained_configuration() == before


@pytest.mark.parametrize(
    "argv",
    [
        ["local", "--runtime", "ollama"],
        ["local", "--reset"],
        ["node", "one", "--base-url", "http://192.0.2.1:25042"],
        ["node", "one", "--remove"],
        ["external-information", "--plugin", "tavily"],
        ["external-information", "--reset"],
    ],
)
def test_existing_mutations_preserve_chat_authorization(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    if argv[:2] == ["node", "one"] and argv[-1] == "--remove":
        _run(capsys, ["node", "one", "--base-url", "http://192.0.2.1:25042"])
    _run(capsys, ["chat", "--external-information-fallback"])

    _run(capsys, argv)

    assert load_retained_configuration().chat_external_information_fallback is True


def test_duplicate_node_url_fails_without_changing_valid_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(capsys, ["node", "one", "--base-url", "http://192.0.2.1:25042"])
    before = load_retained_configuration()
    code, out, err = _run(
        capsys, ["node", "two", "--base-url", "http://192.0.2.1:25042"]
    )
    assert code == 1
    assert out == ""
    assert "error: duplicate retained remote base URL" in err
    assert load_retained_configuration() == before


def test_show_preserves_retained_fact_order(capsys: pytest.CaptureFixture[str]) -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(runtime="ollama"),
                local_capabilities=("code", "chat"),
            ),
            remote_nodes=(
                RemoteNodeDeclaration(
                    "second", "http://192.0.2.2:25042", ("code", "chat")
                ),
                RemoteNodeDeclaration(
                    "first", "http://192.0.2.1:25042", ("summarize",)
                ),
            ),
        )
    )
    path = retained_configuration_file()
    contents_before_show = path.read_bytes()
    code, out, err = _run(capsys, ["show"])
    assert (code, err) == (0, "")
    assert path.read_bytes() == contents_before_show
    assert out.index("  second") < out.index("  first")
    assert "caller-local capabilities: code, chat" in out
    assert "capabilities: code, chat" in out


def test_show_llama_server_retained_facts(capsys: pytest.CaptureFixture[str]) -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(
                    runtime="llama-server",
                    llama_server_base_url="http://127.0.0.1:8080",
                    llama_server_model="model",
                )
            )
        )
    )
    assert _run(capsys, ["show"]) == (
        0,
        "Local:\n"
        "  runtime: llama-server\n"
        "  llama-server base URL: http://127.0.0.1:8080\n"
        "  llama-server model: model\n"
        "  caller-local capabilities: not retained\n"
        "  HAC execution limit: not retained\n"
        "Remote nodes:\n"
        "  none\n"
        "External information:\n"
        "  not configured\n"
        "Chat external information:\n"
        "  automatic fallback: not authorized\n",
        "",
    )


def test_corrupt_configuration_fails_safely(capsys: pytest.CaptureFixture[str]) -> None:
    path = retained_configuration_file()
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"private": "value"}), encoding="utf-8")
    code, out, err = _run(capsys, ["show"])
    assert (code, out) == (1, "")
    assert err == "error: invalid retained configuration shape\n"
    assert str(path) not in err
