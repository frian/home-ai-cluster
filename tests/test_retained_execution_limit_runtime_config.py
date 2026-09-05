"""Focused RFC-0106 proof for retained execution limits with runtime config."""

import asyncio
from pathlib import Path

import pytest

from home_ai_cluster import local_runtime, static_cluster
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.local_runtime_composition import LocalRuntimeCompositionValues
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedLocalConfiguration,
    save_retained_configuration,
)


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))


def _assert_limit_two(intervals: object) -> None:
    assert asyncio.run(intervals.try_enter()) is True
    assert asyncio.run(intervals.try_enter()) is True
    assert asyncio.run(intervals.try_enter()) is False
    asyncio.run(intervals.exit())
    asyncio.run(intervals.exit())


def _retain_limit_two_with_different_runtime() -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(
                    runtime="llama-server",
                    llama_server_base_url="http://127.0.0.1:8080",
                    llama_server_model="retained-model",
                ),
                execution_limit=2,
            )
        )
    )


def test_local_runtime_config_replaces_runtime_but_preserves_retained_limit(
    tmp_path: Path,
) -> None:
    _retain_limit_two_with_different_runtime()
    runtime_config = tmp_path / "runtime.toml"
    runtime_config.write_text('runtime = "ollama"\n', encoding="utf-8")

    app = local_runtime.create_local_runtime_app(
        local_runtime.parse_args(["--runtime-config", str(runtime_config)])
    )
    composition = app.state.local_app_composition
    adapter = composition.adapter_registry.list_adapters()[0]

    assert isinstance(adapter, OllamaAdapter)
    _assert_limit_two(composition.execution_intervals)


def test_static_cluster_runtime_config_preserves_retained_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _retain_limit_two_with_different_runtime()
    runtime_config = tmp_path / "runtime.toml"
    runtime_config.write_text('runtime = "ollama"\n', encoding="utf-8")
    declaration = tmp_path / "cluster.toml"
    declaration.write_text(
        '[[remote_nodes]]\nnode_id = "declared"\nbase_url = "http://192.0.2.20:25042"\n',
        encoding="utf-8",
    )
    captured = []
    monkeypatch.setattr(
        static_cluster.uvicorn, "run", lambda app, **_: captured.append(app)
    )

    static_cluster.main(
        ["--runtime-config", str(runtime_config), "--declaration", str(declaration)]
    )

    composition = captured[0].state.local_app_composition
    adapter = composition.adapter_registry.list_adapters()[0]
    assert isinstance(adapter, OllamaAdapter)
    _assert_limit_two(composition.execution_intervals)
