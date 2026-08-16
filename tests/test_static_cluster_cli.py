from pathlib import Path

import pytest
from fastapi import FastAPI

from home_ai_cluster import local_runtime
from home_ai_cluster.local_runtime_composition import create_local_runtime_composition
from home_ai_cluster.static_cluster import (
    STATIC_CLUSTER_HOST,
    STATIC_CLUSTER_PORT,
    create_remote_declaration,
    main,
    parse_args,
)
from home_ai_cluster.static_cluster_declaration import load_static_cluster_declaration


def test_parse_args_accepts_inline_mode() -> None:
    args = parse_args(
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000/",
        ]
    )

    assert args.declaration is None
    assert args.remote_node_id == "operator-remote"
    assert args.remote_base_url == "https://remote.example:8000"
    assert args.local_capability == ("chat", "summarize")
    assert args.remote_capability == ("chat", "summarize")
    assert args.runtime == "ollama"
    assert args.llama_server_base_url is None
    assert args.llama_server_model is None
    assert args.ollama_model is None


def test_parse_args_accepts_declaration_mode_without_loading_file(
    tmp_path: Path,
) -> None:
    declaration_path = tmp_path / "cluster.toml"

    args = parse_args(["--declaration", str(declaration_path)])

    assert args.declaration == declaration_path
    assert args.remote_node_id is None
    assert args.remote_base_url is None
    assert args.runtime == "ollama"


def test_parse_args_accepts_explicit_ollama_runtime() -> None:
    args = parse_args(
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000",
            "--runtime",
            "ollama",
        ]
    )

    assert args.runtime == "ollama"
    assert args.llama_server_base_url is None
    assert args.llama_server_model is None
    assert args.ollama_model is None


@pytest.mark.parametrize(
    ("capabilities", "expected"),
    [
        (["chat"], ("chat",)),
        (["summarize"], ("summarize",)),
        (["classify"], ("classify",)),
        (["classify", "chat", "summarize"], ("classify", "chat", "summarize")),
    ],
)
def test_parse_args_accepts_explicit_inline_remote_capabilities(
    capabilities: list[str],
    expected: tuple[str, ...],
) -> None:
    args = parse_args(
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000",
            *[
                option
                for capability in capabilities
                for option in ("--remote-capability", capability)
            ],
        ]
    )

    assert args.remote_capability == expected


@pytest.mark.parametrize(
    ("capabilities", "expected"),
    [
        (["chat"], ("chat",)),
        (["summarize"], ("summarize",)),
        (["summarize", "classify", "chat"], ("summarize", "classify", "chat")),
    ],
)
def test_parse_args_accepts_explicit_inline_local_capabilities(
    capabilities: list[str],
    expected: tuple[str, ...],
) -> None:
    args = parse_args(
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000",
            *[
                option
                for capability in capabilities
                for option in ("--local-capability", capability)
            ],
        ]
    )

    assert args.local_capability == expected


def test_parse_args_accepts_llama_server_with_declaration_topology(
    tmp_path: Path,
) -> None:
    declaration_path = tmp_path / "cluster.toml"

    args = parse_args(
        [
            "--declaration",
            str(declaration_path),
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://127.0.0.1:8080/",
            "--llama-server-model",
            "local-model",
        ]
    )

    assert args.declaration == declaration_path
    assert args.runtime == "llama-server"
    assert args.llama_server_base_url == "http://127.0.0.1:8080"
    assert args.llama_server_model == "local-model"


def test_parse_args_accepts_llama_server_with_inline_topology() -> None:
    args = parse_args(
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000",
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://127.0.0.1:8080",
            "--llama-server-model",
            "local-model",
        ]
    )

    assert args.runtime == "llama-server"
    assert args.llama_server_base_url == "http://127.0.0.1:8080"
    assert args.llama_server_model == "local-model"


@pytest.mark.parametrize(
    "runtime_argv",
    [
        ["--runtime", "unsupported"],
        [
            "--runtime",
            "ollama",
            "--llama-server-base-url",
            "http://127.0.0.1:8080",
        ],
        [
            "--runtime",
            "ollama",
            "--llama-server-model",
            "local-model",
        ],
        ["--runtime", "llama-server"],
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://127.0.0.1:8080",
        ],
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "https://127.0.0.1:8080",
            "--llama-server-model",
            "local-model",
        ],
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://runtime.example:8080",
            "--llama-server-model",
            "local-model",
        ],
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://127.0.0.1:8080",
            "--llama-server-model",
            "",
        ],
    ],
)
def test_parse_args_matches_standalone_runtime_validation_errors(
    runtime_argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(runtime_argv)
    standalone_error = capsys.readouterr().err.rsplit(": error: ", 1)[1]

    with pytest.raises(SystemExit):
        parse_args(
            [
                "--remote-node-id",
                "operator-remote",
                "--remote-base-url",
                "https://remote.example:8000",
                *runtime_argv,
            ]
        )
    static_cluster_error = capsys.readouterr().err.rsplit(": error: ", 1)[1]

    assert static_cluster_error == standalone_error


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--remote-node-id", "operator-remote"],
        ["--remote-base-url", "https://remote.example:8000"],
        [
            "--declaration",
            "cluster.toml",
            "--remote-node-id",
            "operator-remote",
        ],
        [
            "--declaration",
            "cluster.toml",
            "--remote-base-url",
            "https://remote.example:8000",
        ],
        ["--remote-capability", "chat"],
        ["--local-capability", "chat"],
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-capability",
            "chat",
        ],
        [
            "--remote-base-url",
            "https://remote.example:8000",
            "--remote-capability",
            "chat",
        ],
        [
            "--declaration",
            "cluster.toml",
            "--remote-capability",
            "chat",
        ],
        [
            "--declaration",
            "cluster.toml",
            "--local-capability",
            "chat",
        ],
        [
            "--remote-node-id",
            "operator-remote",
            "--local-capability",
            "chat",
        ],
        [
            "--remote-base-url",
            "https://remote.example:8000",
            "--local-capability",
            "chat",
        ],
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000",
            "--local-capability",
            "chat",
            "--local-capability",
            "chat",
        ],
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000",
            "--local-capability",
            "unknown",
        ],
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000",
            "--remote-capability",
            "chat",
            "--remote-capability",
            "chat",
        ],
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000",
            "--remote-capability",
            "unknown",
        ],
        [
            "--declaration",
            "cluster.toml",
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000",
        ],
    ],
)
def test_parse_args_rejects_incomplete_or_combined_modes(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        parse_args(argv)


def test_inline_and_flat_toml_capabilities_construct_equivalent_remotes(
    tmp_path: Path,
) -> None:
    declaration_path = tmp_path / "cluster.toml"
    declaration_path.write_text(
        'remote_node_id = "operator-remote"\n'
        'remote_base_url = "https://remote.example:8000/"\n'
        'local_capabilities = ["chat"]\n'
        'remote_capabilities = ["chat", "summarize"]\n',
        encoding="utf-8",
    )
    toml = load_static_cluster_declaration(declaration_path)
    args = parse_args(
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000/",
            "--local-capability",
            "chat",
            "--remote-capability",
            "chat",
            "--remote-capability",
            "summarize",
        ]
    )

    inline_remote = create_remote_declaration(
        args.remote_node_id,
        args.remote_base_url,
        args.remote_capability,
    )
    toml_remote = create_remote_declaration(
        toml.remote_node_id,
        toml.remote_base_url,
        toml.remote_capabilities,
    )

    assert inline_remote == toml_remote
    assert args.local_capability == toml.local_capabilities
    inline_local = create_local_runtime_composition(
        runtime="ollama",
        capabilities=args.local_capability,
    )
    toml_local = create_local_runtime_composition(
        runtime="ollama",
        capabilities=toml.local_capabilities,
    )
    assert (
        inline_local.node_registry.list_nodes() == toml_local.node_registry.list_nodes()
    )


def test_main_loads_single_declaration_collection_before_starting_server(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import static_cluster

    declaration_path = tmp_path / "cluster.toml"
    declaration_path.write_text(
        'remote_node_id = "operator-remote"\n'
        'remote_base_url = "https://remote.example:8000/"\n',
        encoding="utf-8",
    )
    app = FastAPI()
    recorded: dict[str, object] = {}
    local_composition = create_local_runtime_composition(runtime="ollama")

    def create_app(
        remote_nodes: object,
        *,
        local_app_composition: object,
    ) -> FastAPI:
        recorded["remote_nodes"] = remote_nodes
        recorded["local_app_composition"] = local_app_composition
        return app

    monkeypatch.setattr(
        static_cluster,
        "create_static_cluster_collection_app",
        create_app,
    )

    def create_local_composition(
        *,
        runtime: str,
        ollama_model: str | None,
        llama_server_base_url: str | None,
        llama_server_model: str | None,
        capabilities: tuple[str, ...],
    ) -> object:
        recorded["composition_arguments"] = {
            "runtime": runtime,
            "ollama_model": ollama_model,
            "llama_server_base_url": llama_server_base_url,
            "llama_server_model": llama_server_model,
            "capabilities": capabilities,
        }
        return local_composition

    monkeypatch.setattr(
        static_cluster,
        "create_local_runtime_composition",
        create_local_composition,
    )
    monkeypatch.setattr(
        static_cluster.uvicorn,
        "run",
        lambda run_app, *, host, port: recorded.update(
            app=run_app, host=host, port=port
        ),
    )

    main(
        [
            "--declaration",
            str(declaration_path),
            "--runtime",
            "ollama",
            "--ollama-model",
            "configured-model",
        ]
    )

    remote_nodes = recorded["remote_nodes"]
    assert [(remote.node_id, remote.base_url) for remote in remote_nodes] == [
        ("operator-remote", "https://remote.example:8000")
    ]
    assert recorded["composition_arguments"] == {
        "runtime": "ollama",
        "ollama_model": "configured-model",
        "llama_server_base_url": None,
        "llama_server_model": None,
        "capabilities": ("chat", "summarize"),
    }
    assert recorded["local_app_composition"] is local_composition
    assert recorded["app"] is app
    assert recorded["host"] == STATIC_CLUSTER_HOST
    assert recorded["port"] == STATIC_CLUSTER_PORT


def test_main_passes_llama_server_composition_to_declaration_constructor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import static_cluster

    declaration_path = tmp_path / "cluster.toml"
    declaration_path.write_text(
        'remote_node_id = "operator-remote"\n'
        'remote_base_url = "https://remote.example:8000"\n',
        encoding="utf-8",
    )
    app = FastAPI()
    selected_composition = object()
    recorded: dict[str, object] = {}

    def create_local_composition(**kwargs: object) -> object:
        recorded["composition_arguments"] = kwargs
        return selected_composition

    def create_app(
        remote_nodes: object,
        *,
        local_app_composition: object,
    ) -> FastAPI:
        recorded["remote_nodes"] = remote_nodes
        recorded["local_app_composition"] = local_app_composition
        return app

    monkeypatch.setattr(
        static_cluster,
        "create_local_runtime_composition",
        create_local_composition,
    )
    monkeypatch.setattr(
        static_cluster,
        "create_static_cluster_collection_app",
        create_app,
    )
    monkeypatch.setattr(
        static_cluster.uvicorn,
        "run",
        lambda run_app, *, host, port: recorded.update(
            app=run_app,
            host=host,
            port=port,
        ),
    )

    main(
        [
            "--declaration",
            str(declaration_path),
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://127.0.0.1:8080",
            "--llama-server-model",
            "local-model",
        ]
    )

    assert recorded["composition_arguments"] == {
        "runtime": "llama-server",
        "ollama_model": None,
        "llama_server_base_url": "http://127.0.0.1:8080",
        "llama_server_model": "local-model",
        "capabilities": ("chat", "summarize"),
    }
    assert recorded["local_app_composition"] is selected_composition
    assert [vars(remote) for remote in recorded["remote_nodes"]] == [
        {
            "node_id": "operator-remote",
            "base_url": "https://remote.example:8000",
            "capabilities": ("chat", "summarize"),
        }
    ]
    assert recorded["app"] is app
    assert recorded["host"] == STATIC_CLUSTER_HOST
    assert recorded["port"] == STATIC_CLUSTER_PORT


def test_invalid_runtime_input_stops_before_loading_or_starting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import static_cluster

    declaration_path = tmp_path / "cluster.toml"
    calls: list[str] = []

    monkeypatch.setattr(
        static_cluster,
        "load_static_cluster_declarations",
        lambda _: calls.append("declaration") or None,
    )
    monkeypatch.setattr(
        static_cluster,
        "create_local_runtime_composition",
        lambda **_: calls.append("composition") or None,
    )
    monkeypatch.setattr(
        static_cluster.uvicorn,
        "run",
        lambda *_args, **_kwargs: calls.append("server"),
    )

    with pytest.raises(SystemExit):
        main(
            [
                "--declaration",
                str(declaration_path),
                "--runtime",
                "llama-server",
            ]
        )

    assert calls == []


def test_main_preserves_multiple_declaration_order_before_starting_server(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import static_cluster

    declaration_path = tmp_path / "cluster.toml"
    declaration_path.write_text(
        '[[remote_nodes]]\nnode_id = "remote-a"\n'
        'base_url = "https://remote-a.example:8000/"\n'
        '[[remote_nodes]]\nnode_id = "remote-b"\n'
        'base_url = "https://remote-b.example:8000"\n',
        encoding="utf-8",
    )
    app = FastAPI()
    recorded: dict[str, object] = {}

    def create_app(
        remote_nodes: object,
        *,
        local_app_composition: object,
    ) -> FastAPI:
        recorded["remote_nodes"] = remote_nodes
        recorded["local_app_composition"] = local_app_composition
        return app

    monkeypatch.setattr(
        static_cluster,
        "create_static_cluster_collection_app",
        create_app,
    )
    monkeypatch.setattr(
        static_cluster.uvicorn,
        "run",
        lambda run_app, *, host, port: recorded.update(app=run_app),
    )

    main(["--declaration", str(declaration_path)])

    remote_nodes = recorded["remote_nodes"]
    assert [(remote.node_id, remote.base_url) for remote in remote_nodes] == [
        ("remote-a", "https://remote-a.example:8000"),
        ("remote-b", "https://remote-b.example:8000"),
    ]
    assert recorded["app"] is app


def test_main_does_not_start_server_when_declaration_loading_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster import static_cluster

    declaration_path = tmp_path / "cluster.toml"
    private_url = "private.example:9443"
    declaration_path.write_text(
        f'remote_node_id = "operator-remote"\nremote_base_url = "{private_url}"\n',
        encoding="utf-8",
    )
    started = False

    def run(*args: object, **kwargs: object) -> None:
        nonlocal started
        started = True

    monkeypatch.setattr(static_cluster.uvicorn, "run", run)

    with pytest.raises(SystemExit):
        main(["--declaration", str(declaration_path)])

    captured = capsys.readouterr()
    assert not started
    assert "invalid remote base URL declaration" in captured.err
    assert private_url not in captured.err
    assert "private.example" not in captured.err
