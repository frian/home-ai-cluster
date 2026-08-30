"""Startup consumption tests for accepted RFC-0094 retained configuration."""

from pathlib import Path

import pytest

from home_ai_cluster import local_runtime, static_cluster
from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.local_runtime_composition import LocalRuntimeCompositionValues
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedLocalConfiguration,
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
