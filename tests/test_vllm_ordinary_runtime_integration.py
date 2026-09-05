import json
from pathlib import Path

import pytest
from fastapi import FastAPI

from home_ai_cluster import local_runtime, static_cluster
from home_ai_cluster.commands import config_command
from home_ai_cluster.local_runtime_composition import LocalRuntimeCompositionValues
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedLocalConfiguration,
    load_retained_configuration,
    save_retained_configuration,
)


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))


def test_config_local_vllm_retains_execution_limit_and_show(
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_command.main(
        [
            "local",
            "--runtime",
            "vllm",
            "--vllm-base-url",
            "http://127.0.0.1:8000",
            "--vllm-model",
            "served-name",
            "--execution-limit",
            "2",
        ]
    )
    assert capsys.readouterr().out == "local configuration retained\n"

    configuration = load_retained_configuration()
    assert configuration.local == RetainedLocalConfiguration(
        runtime=LocalRuntimeCompositionValues(
            runtime="vllm",
            vllm_base_url="http://127.0.0.1:8000",
            vllm_model="served-name",
        ),
        execution_limit=2,
    )

    config_command.main(["show"])
    assert capsys.readouterr().out == (
        "Local:\n"
        "  runtime: vllm\n"
        "  vLLM base URL: http://127.0.0.1:8000\n"
        "  vLLM model: served-name\n"
        "  caller-local capabilities: not retained\n"
        "  HAC execution limit: 2\n"
        "Remote nodes:\n"
        "  none\n"
        "External information:\n"
        "  not configured\n"
        "Chat external information:\n"
        "  automatic fallback: not authorized\n"
    )


def test_vllm_retained_configuration_round_trips_with_execution_limit(
    tmp_path: Path,
) -> None:
    path = tmp_path / "retained.json"
    configuration = RetainedConfiguration(
        local=RetainedLocalConfiguration(
            runtime=LocalRuntimeCompositionValues(
                runtime="vllm",
                vllm_base_url="http://127.0.0.1:8000",
                vllm_model="served-name",
            ),
            execution_limit=3,
        )
    )

    save_retained_configuration(configuration, path)

    assert load_retained_configuration(path) == configuration
    assert json.loads(path.read_text())["local"] == {
        "runtime": "vllm",
        "ollama_model": None,
        "ollama_disable_thinking": False,
        "llama_server_base_url": None,
        "llama_server_model": None,
        "local_capabilities": None,
        "vllm_base_url": "http://127.0.0.1:8000",
        "vllm_model": "served-name",
        "execution_limit": 3,
    }


def test_vllm_aware_legacy_ollama_shape_loads_without_rewrite(tmp_path: Path) -> None:
    path = tmp_path / "retained.json"
    contents = (
        b'{"local":{"runtime":"ollama","ollama_model":null,'
        b'"ollama_disable_thinking":false,"llama_server_base_url":null,'
        b'"llama_server_model":null,"vllm_base_url":null,"vllm_model":null,'
        b'"local_capabilities":null},"remote_nodes":[],'
        b'"external_information_plugin":null,'
        b'"chat_external_information_fallback":false}\n'
    )
    path.write_bytes(contents)

    loaded = load_retained_configuration(path)

    assert loaded.local is not None
    assert loaded.local.runtime == LocalRuntimeCompositionValues(runtime="ollama")
    assert path.read_bytes() == contents


def test_vllm_runtime_config_keeps_independent_retained_execution_limit(
    tmp_path: Path,
) -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(runtime="ollama"),
                execution_limit=2,
            )
        )
    )
    runtime_config = tmp_path / "vllm.toml"
    runtime_config.write_text(
        'runtime = "vllm"\n\n[vllm]\n'
        'base_url = "http://127.0.0.1:8000"\n'
        'model = "served-name"\n'
    )

    args = local_runtime.parse_args(["--runtime-config", str(runtime_config)])

    assert args.retained_execution_limit == 2


def test_static_cluster_inline_vllm_passes_selected_runtime_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: dict[str, object] = {}
    selected_composition = object()

    def create_local_composition(**kwargs: object) -> object:
        recorded["composition_arguments"] = kwargs
        return selected_composition

    def create_static_app(
        *_: object,
        capabilities: tuple[str, ...],
        local_app_composition: object,
    ) -> FastAPI:
        recorded["remote_capabilities"] = capabilities
        recorded["local_app_composition"] = local_app_composition
        return FastAPI()

    monkeypatch.setattr(
        static_cluster,
        "create_local_runtime_composition",
        create_local_composition,
    )
    monkeypatch.setattr(static_cluster, "create_static_cluster_app", create_static_app)
    monkeypatch.setattr(static_cluster.uvicorn, "run", lambda *_args, **_kwargs: None)

    static_cluster.main(
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.test",
            "--runtime",
            "vllm",
            "--vllm-base-url",
            "http://127.0.0.1:8000",
            "--vllm-model",
            "served-name",
        ]
    )

    assert recorded == {
        "composition_arguments": {
            "runtime": "vllm",
            "ollama_model": None,
            "ollama_disable_thinking": False,
            "llama_server_base_url": None,
            "llama_server_model": None,
            "vllm_base_url": "http://127.0.0.1:8000",
            "vllm_model": "served-name",
            "capabilities": ("chat", "summarize"),
        },
        "remote_capabilities": ("chat", "summarize"),
        "local_app_composition": selected_composition,
    }
