"""Startup consumption tests for accepted RFC-0094 retained configuration."""

import json
from pathlib import Path

import pytest

from home_ai_cluster import local_runtime, static_cluster
from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.local_runtime_composition import LocalRuntimeCompositionValues
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedLocalConfiguration,
    retained_configuration_file,
    save_retained_configuration,
)
from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))


def test_local_uses_retained_llama_server_despite_ollama_parser_default() -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(
                    runtime="llama-server",
                    llama_server_base_url="http://127.0.0.1:8080",
                    llama_server_model="retained-model",
                )
            )
        )
    )

    app = local_runtime.create_local_runtime_app(local_runtime.parse_args([]))
    adapter = app.state.local_app_composition.adapter_registry.list_adapters()[0]

    assert isinstance(adapter, LlamaServerAdapter)
    assert adapter.base_url == "http://127.0.0.1:8080"
    assert adapter.model == "retained-model"


def test_local_same_runtime_override_keeps_compatible_retained_fields() -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(
                    runtime="ollama",
                    ollama_model="retained-model",
                    ollama_disable_thinking=True,
                )
            )
        )
    )

    app = local_runtime.create_local_runtime_app(
        local_runtime.parse_args(["--ollama-model", "temporary-model"])
    )
    adapter = app.state.local_app_composition.adapter_registry.list_adapters()[0]

    assert isinstance(adapter, OllamaAdapter)
    assert adapter.model == "temporary-model"
    assert adapter.disable_thinking is True


def test_local_uses_all_retained_ollama_facts_without_runtime_options() -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(
                    runtime="ollama",
                    ollama_model="retained-model",
                    ollama_disable_thinking=True,
                )
            )
        )
    )

    before = retained_configuration_file().read_bytes()
    app = local_runtime.create_local_runtime_app(local_runtime.parse_args([]))
    adapter = app.state.local_app_composition.adapter_registry.list_adapters()[0]

    assert isinstance(adapter, OllamaAdapter)
    assert (adapter.model, adapter.disable_thinking) == ("retained-model", True)
    assert retained_configuration_file().read_bytes() == before


@pytest.mark.parametrize(
    ("argv", "base_url", "model"),
    [
        (
            ["--llama-server-model", "temporary-model"],
            "http://127.0.0.1:8080",
            "temporary-model",
        ),
        (
            ["--llama-server-base-url", "http://127.0.0.1:8081"],
            "http://127.0.0.1:8081",
            "retained-model",
        ),
    ],
)
def test_local_llama_server_same_runtime_override_keeps_other_retained_field(
    argv: list[str], base_url: str, model: str
) -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(
                    runtime="llama-server",
                    llama_server_base_url="http://127.0.0.1:8080",
                    llama_server_model="retained-model",
                )
            )
        )
    )
    app = local_runtime.create_local_runtime_app(local_runtime.parse_args(argv))
    adapter = app.state.local_app_composition.adapter_registry.list_adapters()[0]
    assert isinstance(adapter, LlamaServerAdapter)
    assert (adapter.base_url, adapter.model) == (base_url, model)


@pytest.mark.parametrize(
    ("retained", "argv", "adapter_type"),
    [
        (
            LocalRuntimeCompositionValues(
                runtime="ollama", ollama_model="retained", ollama_disable_thinking=True
            ),
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080",
                "--llama-server-model",
                "target",
            ],
            LlamaServerAdapter,
        ),
        (
            LocalRuntimeCompositionValues(
                runtime="llama-server",
                llama_server_base_url="http://127.0.0.1:8080",
                llama_server_model="retained",
            ),
            ["--runtime", "ollama"],
            OllamaAdapter,
        ),
    ],
)
def test_explicit_different_runtime_replaces_retained_domain(
    retained: LocalRuntimeCompositionValues, argv: list[str], adapter_type: type
) -> None:
    save_retained_configuration(
        RetainedConfiguration(local=RetainedLocalConfiguration(runtime=retained))
    )
    app = local_runtime.create_local_runtime_app(local_runtime.parse_args(argv))
    adapter = app.state.local_app_composition.adapter_registry.list_adapters()[0]
    assert isinstance(adapter, adapter_type)


def test_different_runtime_switch_keeps_target_values_required() -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(runtime="ollama")
            )
        )
    )
    with pytest.raises(SystemExit):
        local_runtime.parse_args(["--runtime", "llama-server"])


def test_local_runtime_config_bypasses_retained_loader(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runtime_config = tmp_path / "runtime.toml"
    runtime_config.write_text('runtime = "ollama"\n', encoding="utf-8")
    monkeypatch.setattr(
        local_runtime,
        "load_retained_configuration",
        lambda: (_ for _ in ()).throw(AssertionError("must not load retained state")),
    )
    assert (
        local_runtime.parse_args(
            ["--runtime-config", str(runtime_config)]
        ).runtime_config
        == runtime_config
    )


def test_static_runtime_config_and_declaration_bypass_retained_loader(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runtime_config = tmp_path / "runtime.toml"
    runtime_config.write_text('runtime = "ollama"\n', encoding="utf-8")
    declaration = tmp_path / "cluster.toml"
    declaration.write_text(
        '[[remote_nodes]]\nnode_id = "declared"\nbase_url = "http://192.0.2.20:25042"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        static_cluster,
        "load_retained_configuration",
        lambda: (_ for _ in ()).throw(AssertionError("must not load retained state")),
    )
    monkeypatch.setattr(static_cluster.uvicorn, "run", lambda *_args, **_kwargs: None)
    static_cluster.main(
        ["--runtime-config", str(runtime_config), "--declaration", str(declaration)]
    )


def test_explicit_declaration_replaces_retained_topology_and_capabilities(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(runtime="ollama"),
                local_capabilities=("code",),
            ),
            remote_nodes=(
                RemoteNodeDeclaration("retained", "http://192.0.2.10:25042", ("code",)),
            ),
        )
    )
    declaration = tmp_path / "cluster.toml"
    declaration.write_text(
        'local_capabilities = ["chat"]\n\n'
        "[[remote_nodes]]\n"
        'node_id = "declared"\n'
        'base_url = "http://192.0.2.20:25042"\n',
        encoding="utf-8",
    )
    captured = []
    monkeypatch.setattr(
        static_cluster.uvicorn, "run", lambda app, **_: captured.append(app)
    )
    static_cluster.main(["--declaration", str(declaration)])
    wiring = captured[0].state.static_remote_collection_wiring
    assert [node.node.id for node in wiring.remote_registry.list_declarations()] == [
        "declared"
    ]
    assert [
        capability.name
        for capability in wiring.node_registry.list_nodes()[0].capabilities
    ] == ["chat"]


def test_incompatible_runtime_field_without_explicit_switch_fails() -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(
                    runtime="llama-server",
                    llama_server_base_url="http://127.0.0.1:8080",
                    llama_server_model="retained-model",
                )
            )
        )
    )

    with pytest.raises(SystemExit):
        local_runtime.parse_args(["--ollama-model", "temporary-model"])


def test_static_cluster_uses_retained_ordered_topology_without_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    save_retained_configuration(
        RetainedConfiguration(
            remote_nodes=(
                RemoteNodeDeclaration("node-a", "http://192.0.2.10:25042", ("chat",)),
                RemoteNodeDeclaration("node-b", "http://192.0.2.11:25042", ("code",)),
            )
        )
    )
    captured = []

    def run(app, **_: object) -> None:
        captured.append(app)

    monkeypatch.setattr(static_cluster.uvicorn, "run", run)
    static_cluster.main([])

    nodes = captured[
        0
    ].state.static_remote_collection_wiring.remote_registry.list_declarations()
    assert [node.node.id for node in nodes] == ["node-a", "node-b"]


def test_explicit_inline_topology_replaces_retained_topology(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    save_retained_configuration(
        RetainedConfiguration(
            remote_nodes=(
                RemoteNodeDeclaration("retained", "http://192.0.2.10:25042", ("chat",)),
            )
        )
    )
    captured = []
    monkeypatch.setattr(
        static_cluster.uvicorn, "run", lambda app, **_: captured.append(app)
    )
    static_cluster.main(
        ["--remote-node-id", "inline", "--remote-base-url", "http://192.0.2.11:25042"]
    )

    nodes = captured[0].state.static_remote_wiring.remote_registry.list_declarations()
    assert [node.node.id for node in nodes] == ["inline"]
    assert [capability.name for capability in nodes[0].node.capabilities] == [
        "chat",
        "summarize",
    ]


def test_retained_topology_applies_local_capabilities_and_does_not_mutate() -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(runtime="ollama"),
                local_capabilities=("code",),
            ),
            remote_nodes=(
                RemoteNodeDeclaration("remote", "http://192.0.2.10:25042", ("chat",)),
            ),
        )
    )
    before = retained_configuration_file().read_bytes()
    args = static_cluster.parse_args([])
    composition = static_cluster.create_local_runtime_composition(
        runtime="ollama", capabilities=args.local_capability
    )
    assert [
        capability.name
        for capability in composition.node_registry.list_nodes()[0].capabilities
    ] == ["code"]
    assert retained_configuration_file().read_bytes() == before


def test_retained_topology_omitted_local_capabilities_uses_default() -> None:
    save_retained_configuration(
        RetainedConfiguration(
            remote_nodes=(
                RemoteNodeDeclaration("remote", "http://192.0.2.10:25042", ("chat",)),
            )
        )
    )
    assert static_cluster.parse_args([]).local_capability == ("chat", "summarize")


@pytest.mark.parametrize("option", ["--local-capability", "--remote-capability"])
def test_standalone_topology_options_do_not_patch_retained_topology(
    option: str,
) -> None:
    save_retained_configuration(
        RetainedConfiguration(
            remote_nodes=(
                RemoteNodeDeclaration("remote", "http://192.0.2.10:25042", ("chat",)),
            )
        )
    )
    with pytest.raises(SystemExit):
        static_cluster.parse_args([option, "code"])


def test_malformed_retained_state_fails_without_exposing_path_or_contents(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = retained_configuration_file()
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"private": "content"}), encoding="utf-8")
    with pytest.raises(SystemExit):
        local_runtime.parse_args([])
    error = capsys.readouterr().err
    assert str(path) not in error
    assert "private" not in error
