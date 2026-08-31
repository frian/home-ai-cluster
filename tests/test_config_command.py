"""Tests for the bounded retained-configuration command."""

import json
from pathlib import Path

import pytest

from home_ai_cluster import config_command
from home_ai_cluster.local_runtime_composition import LocalRuntimeCompositionValues
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
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


def test_config_requires_one_of_the_bounded_surfaces(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(capsys, [])
    assert code == 2
    assert out == ""
    assert "{local,node,external-information,show}" in err


def test_config_help_shows_exactly_the_bounded_surfaces(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(capsys, ["--help"])
    assert code == 0
    assert err == ""
    assert "{local,node,external-information,show}" in out
    assert "edit" not in out


def test_show_empty_output_is_exact(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(capsys, ["show"]) == (
        0,
        "Local:\n  not configured\nRemote nodes:\n  none\n"
        "External information:\n  not configured\n",
        "",
    )


def test_show_rejects_unexpected_options(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = _run(capsys, ["show", "--json"])
    assert code == 2
    assert out == ""
    assert "unrecognized arguments" in err


def test_show_reports_only_the_retained_external_information_plugin(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(capsys, ["external-information", "--plugin", "tavily"])

    assert _run(capsys, ["show"]) == (
        0,
        "Local:\n  not configured\nRemote nodes:\n  none\n"
        "External information:\n  plugin: tavily\n",
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
        "Remote nodes:\n"
        "  none\n"
        "External information:\n"
        "  not configured\n",
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
