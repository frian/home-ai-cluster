import asyncio

import httpx
import pytest
from fastapi import FastAPI

from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.static_proof import (
    PROOF_HOST,
    PROOF_PORT,
    REMOTE_NODE_ID,
    create_static_proof_app,
    main,
    parse_args,
)


def test_parse_args_requires_explicit_remote_address() -> None:
    with pytest.raises(SystemExit):
        parse_args([])


def test_parse_args_rejects_non_http_address() -> None:
    with pytest.raises(SystemExit):
        parse_args(["remote.local:8000"])


def test_parse_args_accepts_and_normalizes_remote_address() -> None:
    args = parse_args(["http://192.168.1.20:8000/"])

    assert args.remote_address == "http://192.168.1.20:8000"


def test_create_static_proof_app_builds_one_declared_remote() -> None:
    client = httpx.AsyncClient()
    app = create_static_proof_app("http://192.168.1.20:8000", client=client)

    wiring = app.state.static_remote_proof_wiring
    declarations = wiring.remote_registry.list_declarations()

    assert isinstance(app, FastAPI)
    assert wiring.selection_mode is RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY
    assert len(declarations) == 1
    assert declarations[0].node.id == REMOTE_NODE_ID
    assert declarations[0].transport_address == "http://192.168.1.20:8000"
    assert app.state.static_proof_http_client is client

    asyncio.run(client.aclose())


def test_static_proof_app_closes_process_http_client_on_shutdown() -> None:
    client = httpx.AsyncClient()
    app = create_static_proof_app("http://192.168.1.20:8000", client=client)

    async def run_lifespan() -> None:
        async with app.router.lifespan_context(app):
            assert not client.is_closed

    asyncio.run(run_lifespan())

    assert client.is_closed


def test_main_runs_fixed_local_proof_server(monkeypatch: pytest.MonkeyPatch) -> None:
    from home_ai_cluster import static_proof

    app = FastAPI()
    recorded: dict[str, object] = {}

    def fake_create_static_proof_app(address: str) -> FastAPI:
        recorded["address"] = address
        return app

    def fake_run(run_app: FastAPI, *, host: str, port: int) -> None:
        recorded["app"] = run_app
        recorded["host"] = host
        recorded["port"] = port

    monkeypatch.setattr(
        static_proof,
        "create_static_proof_app",
        fake_create_static_proof_app,
    )
    monkeypatch.setattr(static_proof.uvicorn, "run", fake_run)

    main(["http://192.168.1.20:8000"])

    assert recorded == {
        "address": "http://192.168.1.20:8000",
        "app": app,
        "host": PROOF_HOST,
        "port": PROOF_PORT,
    }
