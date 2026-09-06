import argparse
from pathlib import Path

import pytest

from home_ai_cluster import local_runtime, local_runtime_composition, static_cluster
from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.core.models import Capability


def write_runtime_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "runtime.toml"
    path.write_text(content)
    return path


def parser_and_args(
    argv: list[str],
) -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    parser = argparse.ArgumentParser(prog="hac local")
    local_runtime_composition.add_local_runtime_arguments(parser)
    return parser, parser.parse_args(argv)


def test_load_runtime_config_accepts_minimal_ollama(tmp_path: Path) -> None:
    values = local_runtime_composition.load_local_runtime_config(
        write_runtime_config(tmp_path, 'runtime = "ollama"\n')
    )

    assert values == local_runtime_composition.LocalRuntimeCompositionValues(
        runtime="ollama"
    )


def test_load_runtime_config_accepts_ollama_options(tmp_path: Path) -> None:
    values = local_runtime_composition.load_local_runtime_config(
        write_runtime_config(
            tmp_path,
            'runtime = "ollama"\n[ollama]\nmodel = "local-model"\n'
            "disable_thinking = true\n",
        )
    )

    assert values == local_runtime_composition.LocalRuntimeCompositionValues(
        runtime="ollama", ollama_model="local-model", ollama_disable_thinking=True
    )


def test_load_runtime_config_preserves_explicit_ollama_thinking_false(
    tmp_path: Path,
) -> None:
    values = local_runtime_composition.load_local_runtime_config(
        write_runtime_config(
            tmp_path,
            'runtime = "ollama"\n[ollama]\ndisable_thinking = false\n',
        )
    )

    assert values.ollama_disable_thinking is False


def test_load_runtime_config_accepts_and_normalizes_llama_server(
    tmp_path: Path,
) -> None:
    values = local_runtime_composition.load_local_runtime_config(
        write_runtime_config(
            tmp_path,
            'runtime = "llama-server"\n[llama_server]\n'
            'base_url = "http://127.0.0.1:8080/"\nmodel = "local-model"\n',
        )
    )

    assert values == local_runtime_composition.LocalRuntimeCompositionValues(
        runtime="llama-server",
        llama_server_base_url="http://127.0.0.1:8080",
        llama_server_model="local-model",
    )


@pytest.mark.parametrize(
    "content",
    [
        'runtime = "ollama"\nunknown = true\n',
        'runtime = "unsupported"\n',
        'runtime = "ollama"\n[llama_server]\n',
        'runtime = "llama-server"\n[ollama]\n',
        'runtime = "ollama"\n[ollama]\nunknown = true\n',
        'runtime = "llama-server"\n[llama_server]\nunknown = true\n',
        'runtime = "ollama"\n[ollama]\nmodel = "  "\n',
        'runtime = "ollama"\n[ollama]\ndisable_thinking = "false"\n',
        'runtime = "llama-server"\n[llama_server]\nmodel = "local-model"\n',
        'runtime = "llama-server"\n[llama_server]\nbase_url = "http://127.0.0.1"\n',
        'runtime = "llama-server"\n[llama_server]\nbase_url = "https://127.0.0.1"\n'
        'model = "local-model"\n',
        'runtime = "llama-server"\n[llama_server]\nbase_url = "http://example.com"\n'
        'model = "local-model"\n',
        'runtime = "llama-server"\n[llama_server]\n'
        'base_url = "http://127.0.0.1:8080#fragment"\nmodel = "local-model"\n',
        'runtime = "ollama"\n[ollama\n',
    ],
)
def test_load_runtime_config_rejects_invalid_closed_schema(
    tmp_path: Path, content: str
) -> None:
    with pytest.raises(local_runtime_composition.LocalRuntimeCompositionError):
        local_runtime_composition.load_local_runtime_config(
            write_runtime_config(tmp_path, content)
        )


def test_load_runtime_config_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(local_runtime_composition.LocalRuntimeCompositionError):
        local_runtime_composition.load_local_runtime_config(tmp_path / "missing.toml")


def test_load_runtime_config_rejects_missing_top_level_runtime(tmp_path: Path) -> None:
    with pytest.raises(local_runtime_composition.LocalRuntimeCompositionError):
        local_runtime_composition.load_local_runtime_config(
            write_runtime_config(tmp_path, '[ollama]\nmodel = "local-model"\n')
        )


@pytest.mark.parametrize(
    "content",
    [
        "runtime = true\n",
        'runtime = "ollama"\n[ollama]\nmodel = true\n',
        'runtime = "llama-server"\n[llama_server]\nbase_url = true\n'
        'model = "local-model"\n',
        'runtime = "llama-server"\n[llama_server]\n'
        'base_url = "http://127.0.0.1:8080"\nmodel = true\n',
    ],
)
def test_load_runtime_config_rejects_required_wrong_toml_types(
    tmp_path: Path, content: str
) -> None:
    with pytest.raises(local_runtime_composition.LocalRuntimeCompositionError):
        local_runtime_composition.load_local_runtime_config(
            write_runtime_config(tmp_path, content)
        )


def test_runtime_config_does_not_conflict_with_implicit_cli_defaults(
    tmp_path: Path,
) -> None:
    config = write_runtime_config(tmp_path, 'runtime = "ollama"\n')
    parser, args = parser_and_args(["--runtime-config", str(config)])

    assert (
        local_runtime_composition.resolve_local_runtime_composition_values(
            parser, args
        ).runtime
        == "ollama"
    )


@pytest.mark.parametrize(
    "argument",
    [
        ["--runtime", "ollama"],
        ["--ollama-model", "local-model"],
        ["--ollama-disable-thinking"],
        ["--llama-server-base-url", "http://127.0.0.1:8080"],
        ["--llama-server-model", "local-model"],
    ],
)
def test_runtime_config_rejects_explicit_runtime_composition_arguments(
    tmp_path: Path, argument: list[str]
) -> None:
    config = write_runtime_config(tmp_path, 'runtime = "ollama"\n')
    parser, args = parser_and_args(["--runtime-config", str(config), *argument])

    with pytest.raises(SystemExit):
        local_runtime_composition.resolve_local_runtime_composition_values(parser, args)


def test_runtime_config_values_construct_the_existing_composition(
    tmp_path: Path,
) -> None:
    values = local_runtime_composition.load_local_runtime_config(
        write_runtime_config(
            tmp_path,
            'runtime = "ollama"\n[ollama]\nmodel = "local-model"\n'
            "disable_thinking = true\n",
        )
    )

    composition = local_runtime_composition.create_local_runtime_composition(
        runtime=values.runtime,
        ollama_model=values.ollama_model,
        ollama_disable_thinking=values.ollama_disable_thinking,
        llama_server_base_url=values.llama_server_base_url,
        llama_server_model=values.llama_server_model,
    )

    adapter = composition.adapter_registry.list_adapters()[0]
    assert adapter.model == "local-model"
    assert adapter.disable_thinking is True


def test_llama_server_runtime_config_constructs_existing_adapter(
    tmp_path: Path,
) -> None:
    values = local_runtime_composition.load_local_runtime_config(
        write_runtime_config(
            tmp_path,
            'runtime = "llama-server"\n[llama_server]\n'
            'base_url = "http://127.0.0.1:8080/"\nmodel = "local-model"\n',
        )
    )

    composition = local_runtime_composition.create_local_runtime_composition(
        runtime=values.runtime,
        ollama_model=values.ollama_model,
        ollama_disable_thinking=values.ollama_disable_thinking,
        llama_server_base_url=values.llama_server_base_url,
        llama_server_model=values.llama_server_model,
    )

    adapter = composition.adapter_registry.list_adapters()[0]
    assert isinstance(adapter, LlamaServerAdapter)
    assert adapter.base_url == "http://127.0.0.1:8080"
    assert adapter.model == "local-model"


def test_local_command_consumes_runtime_config_without_explicit_runtime(
    tmp_path: Path,
) -> None:
    config = write_runtime_config(
        tmp_path,
        'runtime = "ollama"\n[ollama]\nmodel = "local-model"\n'
        "disable_thinking = true\n",
    )

    app = local_runtime.create_local_runtime_app(
        local_runtime.parse_args(["--runtime-config", str(config)])
    )

    adapter = app.state.local_app_composition.adapter_registry.list_adapters()[0]
    assert adapter.model == "local-model"
    assert adapter.disable_thinking is True


def test_static_cluster_inline_mode_consumes_runtime_config(tmp_path: Path) -> None:
    config = write_runtime_config(
        tmp_path,
        'runtime = "llama-server"\n[llama_server]\n'
        'base_url = "http://127.0.0.1:8080"\nmodel = "local-model"\n',
    )
    args = static_cluster.parse_args(
        [
            "--runtime-config",
            str(config),
            "--remote-node-id",
            "remote-a",
            "--remote-base-url",
            "http://remote-a.test:8000",
        ]
    )

    parser = static_cluster._create_argument_parser()
    values = local_runtime_composition.resolve_local_runtime_composition_values(
        parser, args
    )
    assert values.runtime == "llama-server"
    assert values.llama_server_model == "local-model"


def test_static_cluster_declaration_mode_consumes_separate_runtime_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fastapi import FastAPI

    declaration = tmp_path / "cluster.toml"
    declaration.write_text(
        'remote_node_id = "remote-a"\nremote_base_url = "http://remote-a.test:8000"\n',
        encoding="utf-8",
    )
    config = tmp_path / "runtime-static.toml"
    config.write_text(
        'runtime = "llama-server"\n[llama_server]\n'
        'base_url = "http://127.0.0.1:8080/"\nmodel = "local-model"\n',
        encoding="utf-8",
    )
    recorded: dict[str, object] = {}

    def create_composition(**kwargs: object) -> object:
        recorded["composition"] = kwargs
        return object()

    def create_app(remote_nodes: object, **kwargs: object) -> FastAPI:
        recorded["remote_nodes"] = remote_nodes
        recorded["app_kwargs"] = kwargs
        return FastAPI()

    monkeypatch.setattr(
        static_cluster, "create_local_runtime_composition", create_composition
    )
    monkeypatch.setattr(
        static_cluster, "create_static_cluster_collection_app", create_app
    )
    monkeypatch.setattr(static_cluster.uvicorn, "run", lambda *_args, **_kwargs: None)

    static_cluster.main(
        ["--declaration", str(declaration), "--runtime-config", str(config)]
    )

    assert recorded["composition"] == {
        "runtime": "llama-server",
        "ollama_model": None,
        "ollama_disable_thinking": False,
        "llama_server_base_url": "http://127.0.0.1:8080",
        "llama_server_model": "local-model",
        "vllm_base_url": None,
        "vllm_model": None,
        "capabilities": ("chat", "summarize"),
    }

    remote_nodes = recorded["remote_nodes"]
    assert [(node.node_id, node.base_url) for node in remote_nodes] == [
        ("remote-a", "http://remote-a.test:8000")
    ]


def test_load_runtime_config_accepts_closed_vllm_shape(tmp_path: Path) -> None:
    values = local_runtime_composition.load_local_runtime_config(
        write_runtime_config(
            tmp_path,
            'runtime = "vllm"\n[vllm]\nbase_url = "http://127.0.0.1:8000"\n'
            'model = "served-name"\n',
        )
    )

    assert values == local_runtime_composition.LocalRuntimeCompositionValues(
        runtime="vllm",
        vllm_base_url="http://127.0.0.1:8000",
        vllm_model="served-name",
    )


@pytest.mark.parametrize(
    "document",
    [
        'runtime = "vllm"\n',
        'runtime = "vllm"\n[vllm]\nmodel = "served-name"\n',
        'runtime = "vllm"\n[vllm]\nbase_url = "http://127.0.0.1:8000"\n',
        'runtime = "vllm"\n[vllm]\nbase_url = "http://127.0.0.1:8000"\n'
        'model = "served-name"\nextra = true\n',
        'runtime = "vllm"\n[vllm]\nbase_url = "http://runtime.example:8000"\n'
        'model = "served-name"\n',
        'runtime = "vllm"\n[vllm]\nbase_url = "http://127.0.0.1:8000"\nmodel = " "\n',
        'runtime = "vllm"\n[llama_server]\nbase_url = "http://127.0.0.1:8080"\n'
        'model = "local-model"\n',
    ],
)
def test_load_runtime_config_rejects_invalid_vllm_shapes(
    tmp_path: Path, document: str
) -> None:
    with pytest.raises(local_runtime_composition.LocalRuntimeCompositionError):
        local_runtime_composition.load_local_runtime_config(
            write_runtime_config(tmp_path, document)
        )


def test_status_command_consumes_runtime_config_before_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from home_ai_cluster.commands import status_command

    declaration = write_runtime_config(
        tmp_path,
        'remote_node_id = "remote-a"\nremote_base_url = "http://remote-a.test:8000"\n',
    )
    config = tmp_path / "runtime-status.toml"
    config.write_text(
        'runtime = "ollama"\n[ollama]\nmodel = "status-model"\n', encoding="utf-8"
    )
    recorded: dict[str, object] = {}

    def create_composition(**kwargs: object) -> object:
        recorded.update(kwargs)
        return object()

    async def fail_observation(*_: object) -> object:
        raise RuntimeError("stop after composition")

    monkeypatch.setattr(
        status_command, "create_local_runtime_composition", create_composition
    )
    monkeypatch.setattr(
        status_command, "evaluate_static_cluster_status", fail_observation
    )

    with pytest.raises(SystemExit, match="1"):
        status_command.main(
            [
                "--declaration",
                str(declaration),
                "--runtime-config",
                str(config),
            ]
        )

    assert recorded["runtime"] == "ollama"
    assert recorded["ollama_model"] == "status-model"
    assert recorded["ollama_disable_thinking"] is False


def test_status_runtime_config_passes_thinking_disable_to_composition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from home_ai_cluster.commands import status_command

    declaration = tmp_path / "cluster.toml"
    declaration.write_text(
        'remote_node_id = "remote-a"\nremote_base_url = "http://remote-a.test:8000"\n',
        encoding="utf-8",
    )
    config = tmp_path / "runtime-status.toml"
    config.write_text(
        'runtime = "ollama"\n[ollama]\ndisable_thinking = true\n',
        encoding="utf-8",
    )
    recorded: dict[str, object] = {}

    def create_composition(**kwargs: object) -> object:
        recorded.update(kwargs)
        return object()

    async def fail_observation(*_: object) -> object:
        raise RuntimeError("stop after composition")

    monkeypatch.setattr(
        status_command, "create_local_runtime_composition", create_composition
    )
    monkeypatch.setattr(
        status_command, "evaluate_static_cluster_status", fail_observation
    )

    with pytest.raises(SystemExit, match="1"):
        status_command.main(
            [
                "--declaration",
                str(declaration),
                "--runtime-config",
                str(config),
            ]
        )

    assert recorded["ollama_disable_thinking"] is True


def test_multi_binding_runtime_config_constructs_one_node_and_exact_bindings(
    tmp_path: Path,
) -> None:
    values = local_runtime_composition.load_local_runtime_config(
        write_runtime_config(
            tmp_path,
            '[[bindings]]\ncapabilities = ["chat"]\nruntime = "ollama"\n'
            'model = "chat-model"\n\n[[bindings]]\ncapabilities = ["code"]\n'
            'runtime = "ollama"\nmodel = "code-model"\n',
        )
    )

    assert isinstance(
        values, local_runtime_composition.MultiBindingRuntimeCompositionValues
    )
    composition = local_runtime_composition.create_multi_binding_local_app_composition(
        values
    )
    adapters = composition.adapter_registry.list_adapters()

    assert len(composition.node_registry.list_nodes()) == 1
    assert [
        capability.name
        for capability in composition.node_registry.list_nodes()[0].capabilities
    ] == [
        "chat",
        "code",
    ]
    assert len(adapters) == 2
    assert all(isinstance(adapter, OllamaAdapter) for adapter in adapters)
    assert adapters[0] is not adapters[1]
    assert adapters[0].name == adapters[1].name == "ollama"
    assert adapters[0].model == "chat-model"
    assert adapters[1].model == "code-model"
    assert (
        composition.adapter_registry.bound_adapter_for(Capability(name="chat"))
        is adapters[0]
    )
    assert (
        composition.adapter_registry.bound_adapter_for(Capability(name="code"))
        is adapters[1]
    )


@pytest.mark.parametrize(
    "content",
    [
        "bindings = []\n",
        '[[bindings]]\ncapabilities = []\nruntime = "ollama"\n',
        '[[bindings]]\ncapabilities = ["chat", "chat"]\nruntime = "ollama"\n',
        '[[bindings]]\ncapabilities = ["chat"]\nruntime = "ollama"\n\n'
        '[[bindings]]\ncapabilities = ["chat"]\nruntime = "vllm"\n'
        'base_url = "http://127.0.0.1:8000"\nmodel = "served"\n',
        '[[bindings]]\ncapabilities = ["unknown"]\nruntime = "ollama"\n',
        '[[bindings]]\ncapabilities = ["chat"]\nruntime = "ollama"\n'
        'base_url = "http://127.0.0.1:8000"\n',
        'runtime = "ollama"\n[[bindings]]\ncapabilities = ["chat"]\n'
        'runtime = "ollama"\n',
    ],
)
def test_multi_binding_runtime_config_rejects_invalid_shapes(
    tmp_path: Path, content: str
) -> None:
    with pytest.raises(local_runtime_composition.LocalRuntimeCompositionError):
        local_runtime_composition.load_local_runtime_config(
            write_runtime_config(tmp_path, content)
        )


def test_local_command_accepts_multi_binding_runtime_config(tmp_path: Path) -> None:
    config = write_runtime_config(
        tmp_path,
        '[[bindings]]\ncapabilities = ["chat"]\nruntime = "ollama"\n\n'
        '[[bindings]]\ncapabilities = ["summarize"]\nruntime = "llama-server"\n'
        'base_url = "http://127.0.0.1:8080"\nmodel = "summary-model"\n',
    )

    app = local_runtime.create_local_runtime_app(
        local_runtime.parse_args(["--runtime-config", str(config)])
    )
    composition = app.state.local_app_composition

    assert [
        adapter.name for adapter in composition.adapter_registry.list_adapters()
    ] == [
        "ollama",
        "llama-server",
    ]
    assert [
        capability.name
        for capability in composition.node_registry.list_nodes()[0].capabilities
    ] == [
        "chat",
        "summarize",
    ]


def test_static_cluster_keeps_caller_permission_separate_from_bindings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fastapi import FastAPI

    declaration = tmp_path / "cluster.toml"
    declaration.write_text(
        'local_capabilities = ["chat", "classify"]\n\n[[remote_nodes]]\n'
        'node_id = "remote-a"\nbase_url = "http://remote-a.test:8000"\n'
        'capabilities = ["summarize"]\n',
        encoding="utf-8",
    )
    config = write_runtime_config(
        tmp_path,
        '[[bindings]]\ncapabilities = ["chat"]\nruntime = "ollama"\n\n'
        '[[bindings]]\ncapabilities = ["summarize"]\nruntime = "ollama"\n'
        'model = "summary-model"\n',
    )
    recorded: dict[str, object] = {}

    def create_app(*_args: object, **kwargs: object) -> FastAPI:
        recorded.update(kwargs)
        return FastAPI()

    monkeypatch.setattr(
        static_cluster, "create_static_cluster_collection_app", create_app
    )
    monkeypatch.setattr(static_cluster.uvicorn, "run", lambda *_args, **_kwargs: None)

    static_cluster.main(
        ["--declaration", str(declaration), "--runtime-config", str(config)]
    )

    composition = recorded["local_app_composition"]
    assert isinstance(composition, object)
    local_node = composition.node_registry.list_nodes()[0]
    assert [capability.name for capability in local_node.capabilities] == ["chat"]
    assert (
        composition.adapter_registry.bound_adapter_for(Capability(name="summarize"))
        is not None
    )
    assert (
        composition.adapter_registry.bound_adapter_for(Capability(name="classify"))
        is None
    )


def test_status_rejects_multi_binding_runtime_config_before_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from home_ai_cluster.commands import status_command

    declaration = tmp_path / "cluster.toml"
    declaration.write_text(
        'remote_node_id = "remote-a"\nremote_base_url = "http://remote-a.test:8000"\n',
        encoding="utf-8",
    )
    config = write_runtime_config(
        tmp_path, '[[bindings]]\ncapabilities = ["chat"]\nruntime = "ollama"\n'
    )

    async def fail_observation(*_: object) -> object:
        raise AssertionError("status observation must not run")

    monkeypatch.setattr(
        status_command, "evaluate_static_cluster_status", fail_observation
    )
    with pytest.raises(SystemExit, match="2"):
        status_command.main(
            ["--declaration", str(declaration), "--runtime-config", str(config)]
        )
