import argparse

import pytest
from fastapi import FastAPI

from home_ai_cluster import local_runtime
from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    RuntimeResult,
)


def test_parse_args_defaults_to_ollama() -> None:
    args = local_runtime.parse_args([])

    assert args.runtime == "ollama"
    assert args.llama_server_base_url is None
    assert args.llama_server_model is None
    assert args.host == "127.0.0.1"
    assert args.port == 8000


def test_parse_args_accepts_explicit_ollama() -> None:
    args = local_runtime.parse_args(["--runtime", "ollama"])

    assert args.runtime == "ollama"


def test_parse_args_rejects_unsupported_runtime() -> None:
    with pytest.raises(SystemExit):
        local_runtime.parse_args(["--runtime", "unsupported"])


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
            "http://127.0.0.1:8080/",
            "--llama-server-model",
            "local-model",
            "--host",
            "0.0.0.0",
            "--port",
            "8123",
        ]
    )

    assert args.runtime == "llama-server"
    assert args.llama_server_base_url == "http://127.0.0.1:8080"
    assert args.llama_server_model == "local-model"
    assert args.host == "0.0.0.0"
    assert args.port == 8123


def assert_ordinary_local_node(composition, adapter_name: str) -> None:
    nodes = composition.node_registry.list_nodes()

    assert len(nodes) == 1
    assert nodes[0].id == "local"
    assert nodes[0].name == "Local node"
    assert nodes[0].availability == "available"
    assert nodes[0].health.healthy is True
    assert nodes[0].capabilities == [Capability(name="chat")]
    assert nodes[0].adapters == [adapter_name]


def test_create_ollama_local_app_composition_uses_one_default_adapter() -> None:
    composition = local_runtime.create_ollama_local_app_composition()

    assert_ordinary_local_node(composition, "ollama")
    adapters = composition.adapter_registry.list_adapters()
    assert len(adapters) == 1
    assert isinstance(adapters[0], OllamaAdapter)
    assert adapters[0].name == "ollama"


def test_create_llama_server_local_app_composition_uses_one_adapter() -> None:
    composition = local_runtime.create_llama_server_local_app_composition(
        base_url="http://127.0.0.1:8080",
        model="local-model",
    )

    assert_ordinary_local_node(composition, "llama-server")
    adapters = composition.adapter_registry.list_adapters()
    assert len(adapters) == 1
    assert isinstance(adapters[0], LlamaServerAdapter)
    assert adapters[0].name == "llama-server"
    assert adapters[0].base_url == "http://127.0.0.1:8080"
    assert adapters[0].model == "local-model"


class RecordingLlamaServerAdapter:
    def __init__(self, *, base_url: str, model: str) -> None:
        self.base_url = base_url
        self.model = model
        self.health_calls = 0
        self.chat_calls = 0

    @property
    def name(self) -> str:
        return "llama-server"

    def health(self) -> AdapterHealth:
        self.health_calls += 1
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.chat_calls += 1
        return RuntimeResult(content="unused", adapter=self.name)


def test_composition_construction_does_not_probe_or_execute_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[RecordingLlamaServerAdapter] = []

    def create_adapter(*, base_url: str, model: str) -> RecordingLlamaServerAdapter:
        adapter = RecordingLlamaServerAdapter(base_url=base_url, model=model)
        created.append(adapter)
        return adapter

    monkeypatch.setattr(local_runtime, "LlamaServerAdapter", create_adapter)

    local_runtime.create_llama_server_local_app_composition(
        base_url="http://127.0.0.1:8080",
        model="local-model",
    )

    assert len(created) == 1
    assert created[0].health_calls == 0
    assert created[0].chat_calls == 0


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
    assert_ordinary_local_node(captured["composition"], "llama-server")


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
    assert_ordinary_local_node(captured["composition"], "ollama")
    adapter = captured["composition"].adapter_registry.list_adapters()[0]
    assert isinstance(adapter, OllamaAdapter)


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
        "port": 8000,
    }
