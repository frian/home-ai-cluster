import argparse

import pytest

from home_ai_cluster import local_runtime_composition
from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    RuntimeResult,
)


def assert_ordinary_local_node(composition, adapter_name: str) -> None:
    nodes = composition.node_registry.list_nodes()

    assert len(nodes) == 1
    assert nodes[0].id == "local"
    assert nodes[0].name == "Local node"
    assert nodes[0].availability == "available"
    assert nodes[0].health.healthy is True
    assert nodes[0].capabilities == [
        Capability(name="chat"),
        Capability(name="summarize"),
    ]
    assert nodes[0].adapters == [adapter_name]


def test_shared_runtime_arguments_work_with_an_ordinary_parser() -> None:
    parser = argparse.ArgumentParser()
    local_runtime_composition.add_local_runtime_arguments(parser)

    args = parser.parse_args(
        [
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://127.0.0.1:8080/",
            "--llama-server-model",
            "local-model",
        ]
    )
    local_runtime_composition.validate_local_runtime_arguments(parser, args)

    assert args.runtime == "llama-server"
    assert args.llama_server_base_url == "http://127.0.0.1:8080"
    assert args.llama_server_model == "local-model"


def test_shared_runtime_argument_validation_uses_supplied_parser_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = argparse.ArgumentParser(prog="ordinary-parser")
    local_runtime_composition.add_local_runtime_arguments(parser)
    args = parser.parse_args(
        [
            "--runtime",
            "ollama",
            "--llama-server-model",
            "local-model",
        ]
    )

    with pytest.raises(SystemExit):
        local_runtime_composition.validate_local_runtime_arguments(parser, args)

    captured_error = capsys.readouterr().err
    assert captured_error.endswith(
        "ordinary-parser: error: "
        "llama-server arguments require --runtime llama-server\n"
    )


def test_shared_composition_constructs_one_ordinary_ollama_node_and_adapter() -> None:
    composition = local_runtime_composition.create_local_runtime_composition(
        runtime="ollama"
    )

    assert_ordinary_local_node(composition, "ollama")
    adapters = composition.adapter_registry.list_adapters()
    assert len(adapters) == 1
    assert isinstance(adapters[0], OllamaAdapter)
    assert adapters[0].name == "ollama"


@pytest.mark.parametrize(
    ("capabilities", "expected"),
    [
        (("chat",), [Capability(name="chat")]),
        (("summarize",), [Capability(name="summarize")]),
        (("classify",), [Capability(name="classify")]),
        (
            ("summarize", "classify", "chat"),
            [
                Capability(name="summarize"),
                Capability(name="classify"),
                Capability(name="chat"),
            ],
        ),
    ],
)
def test_shared_composition_accepts_explicit_caller_local_capabilities(
    capabilities: tuple[str, ...],
    expected: list[Capability],
) -> None:
    composition = local_runtime_composition.create_local_runtime_composition(
        runtime="ollama",
        capabilities=capabilities,
    )

    assert composition.node_registry.list_nodes()[0].capabilities == expected


def test_shared_composition_constructs_one_ordinary_llama_server_node_and_adapter() -> (
    None
):
    composition = local_runtime_composition.create_local_runtime_composition(
        runtime="llama-server",
        llama_server_base_url="http://127.0.0.1:8080/",
        llama_server_model="local-model",
    )

    assert_ordinary_local_node(composition, "llama-server")
    adapters = composition.adapter_registry.list_adapters()
    assert len(adapters) == 1
    assert isinstance(adapters[0], LlamaServerAdapter)
    assert adapters[0].name == "llama-server"
    assert adapters[0].base_url == "http://127.0.0.1:8080"
    assert adapters[0].model == "local-model"


@pytest.mark.parametrize(
    ("runtime", "base_url", "model"),
    [
        ("unsupported", None, None),
        ("ollama", "http://127.0.0.1:8080", None),
        ("llama-server", None, "local-model"),
        ("llama-server", "http://127.0.0.1:8080", None),
        ("llama-server", "https://127.0.0.1:8080", "local-model"),
        ("llama-server", "http://runtime.example:8080", "local-model"),
        ("llama-server", "http://127.0.0.1:8080", ""),
    ],
)
def test_shared_composition_rejects_invalid_runtime_specific_values(
    runtime: str,
    base_url: str | None,
    model: str | None,
) -> None:
    with pytest.raises(local_runtime_composition.LocalRuntimeCompositionError):
        local_runtime_composition.create_local_runtime_composition(
            runtime=runtime,
            llama_server_base_url=base_url,
            llama_server_model=model,
        )


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


def test_shared_composition_construction_does_not_probe_or_execute_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[RecordingLlamaServerAdapter] = []

    def create_adapter(*, base_url: str, model: str) -> RecordingLlamaServerAdapter:
        adapter = RecordingLlamaServerAdapter(base_url=base_url, model=model)
        created.append(adapter)
        return adapter

    monkeypatch.setattr(
        local_runtime_composition,
        "LlamaServerAdapter",
        create_adapter,
    )

    local_runtime_composition.create_local_runtime_composition(
        runtime="llama-server",
        llama_server_base_url="http://127.0.0.1:8080",
        llama_server_model="local-model",
    )

    assert len(created) == 1
    assert created[0].health_calls == 0
    assert created[0].chat_calls == 0
