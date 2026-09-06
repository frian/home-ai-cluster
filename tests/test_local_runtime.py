import argparse
from pathlib import Path

import pytest
from fastapi import FastAPI

from home_ai_cluster import local_runtime
from home_ai_cluster.adapters.ollama import OllamaAdapter


def test_parse_args_defaults_to_ollama() -> None:
    args = local_runtime.parse_args([])

    assert args.runtime == "ollama"
    assert args.llama_server_base_url is None
    assert args.llama_server_model is None
    assert args.ollama_model is None
    assert args.ollama_disable_thinking is False
    assert args.host == "127.0.0.1"
    assert args.port == 25042


def test_parse_args_accepts_explicit_ollama() -> None:
    args = local_runtime.parse_args(["--runtime", "ollama"])

    assert args.runtime == "ollama"


def test_parse_args_accepts_ollama_disable_thinking() -> None:
    args = local_runtime.parse_args(
        ["--runtime", "ollama", "--ollama-disable-thinking"]
    )

    assert args.ollama_disable_thinking is True


def test_parse_args_rejects_unsupported_runtime() -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(["--runtime", "unsupported"])


@pytest.mark.parametrize(
    ("argv", "error"),
    [
        (
            ["--runtime", "llama-server", "--ollama-model", "configured-model"],
            "ollama arguments require --runtime ollama",
        ),
        (
            ["--runtime", "llama-server", "--ollama-disable-thinking"],
            "ollama arguments require --runtime ollama",
        ),
        (
            ["--runtime", "ollama", "--ollama-model", ""],
            "argument --ollama-model: value must not be empty",
        ),
        (
            [
                "--runtime",
                "ollama",
                "--llama-server-base-url",
                "http://127.0.0.1:8080",
            ],
            "llama-server arguments require --runtime llama-server",
        ),
        (
            ["--runtime", "llama-server"],
            "--llama-server-base-url is required for llama-server",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080",
            ],
            "--llama-server-model is required for llama-server",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "https://127.0.0.1:8080",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://user@127.0.0.1:8080",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://user:secret@127.0.0.1:8080",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080/base",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080?token=x",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080#fragment",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080?",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080#",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:/",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:invalid",
                "--llama-server-model",
                "local-model",
            ],
            "argument --llama-server-base-url: "
            "runtime URL must be an absolute loopback http:// URL",
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080",
                "--llama-server-model",
                "",
            ],
            "argument --llama-server-model: value must not be empty",
        ),
    ],
)
def test_parse_args_preserves_runtime_validation_error_wording(
    argv: list[str],
    error: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(argv)

    assert f"home-ai-cluster-local: error: {error}\n" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv",
    [
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
    ],
)
def test_parse_args_rejects_llama_server_arguments_for_ollama(
    argv: list[str],
) -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(argv)


@pytest.mark.parametrize(
    "argv",
    [
        ["--runtime", "llama-server"],
        [
            "--runtime",
            "llama-server",
            "--llama-server-model",
            "local-model",
        ],
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
def test_parse_args_rejects_invalid_llama_server_composition(
    argv: list[str],
) -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(argv)


def test_parse_args_accepts_explicit_llama_server() -> None:
    args = local_runtime.parse_args(
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://[::1]:8080/",
            "--llama-server-model",
            "local-model",
            "--host",
            "0.0.0.0",
            "--port",
            "8123",
        ]
    )

    assert args.runtime == "llama-server"
    assert args.llama_server_base_url == "http://[::1]:8080"
    assert args.llama_server_model == "local-model"
    assert args.host == "0.0.0.0"
    assert args.port == 8123


def test_create_local_runtime_app_passes_composition_to_create_app(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    captured: dict[str, object] = {}

    def create_app(*, local_app_composition):
        captured["composition"] = local_app_composition
        return app

    monkeypatch.setattr(local_runtime, "create_app", create_app)
    args = local_runtime.parse_args(
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://127.0.0.1:8080",
            "--llama-server-model",
            "local-model",
        ]
    )

    result = local_runtime.create_local_runtime_app(args)

    assert result is app
    node = captured["composition"].node_registry.list_nodes()[0]
    assert node.adapters == ["llama-server"]


def test_create_local_runtime_app_constructs_explicit_vllm_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    captured: dict[str, object] = {}

    def create_app(*, local_app_composition):
        captured["composition"] = local_app_composition
        return app

    monkeypatch.setattr(local_runtime, "create_app", create_app)

    result = local_runtime.create_local_runtime_app(
        local_runtime.parse_args(
            [
                "--runtime",
                "vllm",
                "--vllm-base-url",
                "http://127.0.0.1:8000",
                "--vllm-model",
                "served-name",
            ]
        )
    )

    assert result is app
    adapter = captured["composition"].adapter_registry.list_adapters()[0]
    assert adapter.name == "vllm"
    assert adapter.base_url == "http://127.0.0.1:8000"
    assert adapter.model == "served-name"


def test_create_local_runtime_app_defaults_to_ollama_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    captured: dict[str, object] = {}

    def create_app(*, local_app_composition):
        captured["composition"] = local_app_composition
        return app

    monkeypatch.setattr(local_runtime, "create_app", create_app)

    result = local_runtime.create_local_runtime_app(local_runtime.parse_args([]))

    assert result is app
    node = captured["composition"].node_registry.list_nodes()[0]
    assert node.adapters == ["ollama"]
    adapter = captured["composition"].adapter_registry.list_adapters()[0]
    assert isinstance(adapter, OllamaAdapter)
    assert adapter.model == "llama3.2"
    assert adapter.disable_thinking is False


def test_create_local_runtime_app_passes_explicit_ollama_model_to_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    captured: dict[str, object] = {}

    def create_app(*, local_app_composition):
        captured["composition"] = local_app_composition
        return app

    monkeypatch.setattr(local_runtime, "create_app", create_app)

    result = local_runtime.create_local_runtime_app(
        local_runtime.parse_args(
            ["--runtime", "ollama", "--ollama-model", "configured-model"]
        )
    )

    assert result is app
    adapter = captured["composition"].adapter_registry.list_adapters()[0]
    assert isinstance(adapter, OllamaAdapter)
    assert adapter.model == "configured-model"


def test_create_local_runtime_app_passes_thinking_disable_to_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    captured: dict[str, object] = {}

    def create_app(*, local_app_composition):
        captured["composition"] = local_app_composition
        return app

    monkeypatch.setattr(local_runtime, "create_app", create_app)
    result = local_runtime.create_local_runtime_app(
        local_runtime.parse_args(["--runtime", "ollama", "--ollama-disable-thinking"])
    )

    assert result is app
    adapter = captured["composition"].adapter_registry.list_adapters()[0]
    assert isinstance(adapter, OllamaAdapter)
    assert adapter.disable_thinking is True


@pytest.mark.parametrize(
    ("host", "uses_browser"),
    [
        ("127.0.0.1", True),
        ("0.0.0.0", False),
        ("localhost", False),
        ("::1", False),
    ],
)
def test_create_local_runtime_app_selects_browser_only_for_exact_loopback_host(
    host: str,
    uses_browser: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_app = FastAPI()
    browser_app = FastAPI()
    calls: list[str] = []

    monkeypatch.setattr(
        local_runtime,
        "create_local_runtime_composition",
        lambda **_: object(),
    )
    monkeypatch.setattr(local_runtime, "create_app", lambda **_: api_app)
    monkeypatch.setattr(
        local_runtime,
        "add_loopback_browser_routes",
        lambda app: calls.append("browser") or browser_app,
    )

    result = local_runtime.create_local_runtime_app(
        local_runtime.parse_args(["--host", host])
    )

    assert result is (browser_app if uses_browser else api_app)
    assert calls == (["browser"] if uses_browser else [])


def test_invalid_input_does_not_start_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = False

    def run(*args: object, **kwargs: object) -> None:
        nonlocal started
        started = True

    monkeypatch.setattr(local_runtime.uvicorn, "run", run)

    with pytest.raises(SystemExit):
        local_runtime.main(["--runtime", "llama-server"])

    assert not started


def test_main_starts_default_ollama_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    recorded: dict[str, object] = {}

    def create_local_runtime_app(args: argparse.Namespace) -> FastAPI:
        recorded["runtime"] = args.runtime
        return app

    def run(run_app: FastAPI, *, host: str, port: int) -> None:
        recorded["app"] = run_app
        recorded["host"] = host
        recorded["port"] = port

    monkeypatch.setattr(
        local_runtime,
        "create_local_runtime_app",
        create_local_runtime_app,
    )
    monkeypatch.setattr(local_runtime.uvicorn, "run", run)

    local_runtime.main([])

    assert recorded == {
        "runtime": "ollama",
        "app": app,
        "host": "127.0.0.1",
        "port": 25042,
    }


def test_main_does_not_wrap_uvicorn_owned_startup_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = FastAPI()
    handed_to_uvicorn: dict[str, object] = {}
    failure = RuntimeError()

    monkeypatch.setattr(local_runtime, "create_local_runtime_app", lambda _: app)

    def run(run_app: FastAPI, *, host: str, port: int) -> None:
        handed_to_uvicorn.update(app=run_app, host=host, port=port)
        raise failure

    monkeypatch.setattr(local_runtime.uvicorn, "run", run)

    with pytest.raises(RuntimeError) as raised:
        local_runtime.main([])

    assert raised.value is failure
    assert handed_to_uvicorn == {
        "app": app,
        "host": "127.0.0.1",
        "port": 25042,
    }


@pytest.fixture(autouse=True)
def isolated_retained_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
