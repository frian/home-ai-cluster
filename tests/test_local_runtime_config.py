import argparse
from pathlib import Path

import pytest

from home_ai_cluster import local_runtime, local_runtime_composition, static_cluster


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


def test_runtime_config_does_not_conflict_with_implicit_cli_defaults(
    tmp_path: Path,
) -> None:
    config = write_runtime_config(tmp_path, 'runtime = "ollama"\n')
    parser, args = parser_and_args(["--runtime-config", str(config)])

    assert local_runtime_composition.resolve_local_runtime_composition_values(
        parser, args
    ).runtime == "ollama"


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


def test_status_command_consumes_runtime_config_before_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from home_ai_cluster import status_command

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
