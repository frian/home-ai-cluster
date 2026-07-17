import pytest
from fastapi import FastAPI

from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
from home_ai_cluster.core.models import Capability
from home_ai_cluster.main import create_app
from home_ai_cluster.phase_12_heterogeneous_runtime_cluster_proof import (
    PROOF_RECEIVER_HOST,
    PROOF_RECEIVER_NODE_ID,
    PROOF_RECEIVER_PORT,
    create_phase_12_receiver_app,
    main,
    parse_args,
)


def test_parse_args_uses_explicit_receiver_runtime_values() -> None:
    args = parse_args(
        [
            "--host",
            "0.0.0.0",
            "--port",
            "8123",
            "--llama-server-base-url",
            "http://127.0.0.1:8080/",
            "--llama-server-model",
            "proof-model",
        ]
    )

    assert args.host == "0.0.0.0"
    assert args.port == 8123
    assert args.llama_server_base_url == "http://127.0.0.1:8080"
    assert args.llama_server_model == "proof-model"


def test_parse_args_requires_explicit_llama_server_values() -> None:
    with pytest.raises(SystemExit):
        parse_args([])


def test_parse_args_rejects_non_loopback_llama_server_url() -> None:
    with pytest.raises(SystemExit):
        parse_args(
            [
                "--llama-server-base-url",
                "http://receiver.test:8080",
                "--llama-server-model",
                "proof-model",
            ]
        )


def test_create_phase_12_receiver_app_constructs_matching_llama_server_wiring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import phase_12_heterogeneous_runtime_cluster_proof as proof

    receiver_app = FastAPI()
    captured: dict[str, object] = {}

    def fake_create_proof_receiving_app(*, node_registry, adapter_registry):
        captured["node_registry"] = node_registry
        captured["adapter_registry"] = adapter_registry
        return receiver_app

    monkeypatch.setattr(
        proof,
        "create_proof_receiving_app",
        fake_create_proof_receiving_app,
    )

    app = create_phase_12_receiver_app(
        llama_server_base_url="http://127.0.0.1:8080",
        llama_server_model="proof-model",
    )

    node = captured["node_registry"].list_nodes()[0]
    adapter = captured["adapter_registry"].list_adapters()[0]

    assert app is receiver_app
    assert isinstance(adapter, LlamaServerAdapter)
    assert adapter.base_url == "http://127.0.0.1:8080"
    assert adapter.model == "proof-model"
    assert node.id == PROOF_RECEIVER_NODE_ID
    assert node.capabilities == [Capability(name="chat")]
    assert node.adapters == [adapter.name]


def test_ordinary_application_construction_remains_unchanged() -> None:
    app = create_app()

    assert app.state.proof_receiving_app_wiring is None


def test_main_runs_receiver_with_explicit_bind_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import phase_12_heterogeneous_runtime_cluster_proof as proof

    receiver_app = FastAPI()
    recorded: dict[str, object] = {}

    def fake_create_phase_12_receiver_app(*, llama_server_base_url, llama_server_model):
        recorded["llama_server_base_url"] = llama_server_base_url
        recorded["llama_server_model"] = llama_server_model
        return receiver_app

    def fake_run(app: FastAPI, *, host: str, port: int) -> None:
        recorded["app"] = app
        recorded["host"] = host
        recorded["port"] = port

    monkeypatch.setattr(
        proof,
        "create_phase_12_receiver_app",
        fake_create_phase_12_receiver_app,
    )
    monkeypatch.setattr(proof.uvicorn, "run", fake_run)

    main(
        [
            "--llama-server-base-url",
            "http://127.0.0.1:8080",
            "--llama-server-model",
            "proof-model",
        ]
    )

    assert recorded == {
        "llama_server_base_url": "http://127.0.0.1:8080",
        "llama_server_model": "proof-model",
        "app": receiver_app,
        "host": PROOF_RECEIVER_HOST,
        "port": PROOF_RECEIVER_PORT,
    }
