import asyncio

import httpx
import pytest
from fastapi import FastAPI

from home_ai_cluster.automatic_proof import (
    PROOF_HOST,
    PROOF_PORT,
    REMOTE_NODE_ID,
    create_automatic_proof_app,
    main,
    parse_args,
)


def test_automatic_proof_requires_one_absolute_http_address() -> None:
    with pytest.raises(SystemExit):
        parse_args([])
    with pytest.raises(SystemExit):
        parse_args(["https://remote.example:8000"])
    assert (
        parse_args(["http://remote.example:8000/"]).remote_address
        == "http://remote.example:8000"
    )


def test_automatic_proof_composes_one_remote_and_no_local_candidates() -> None:
    client = httpx.AsyncClient()
    app = create_automatic_proof_app("http://remote.example:8000", client=client)
    declarations = app.state.automatic_proof_remote_registry.list_declarations()
    assert len(declarations) == 1
    assert declarations[0].node.id == REMOTE_NODE_ID
    assert declarations[0].node.capabilities[0].name == "chat"
    assert declarations[0].transport_address == "http://remote.example:8000"
    asyncio.run(client.aclose())


def test_automatic_proof_closes_its_client() -> None:
    client = httpx.AsyncClient()
    app = create_automatic_proof_app("http://remote.example:8000", client=client)
    asyncio.run(_run_lifespan(app))
    assert client.is_closed


async def _run_lifespan(app: FastAPI) -> None:
    async with app.router.lifespan_context(app):
        pass


def test_main_uses_fixed_loopback_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    from home_ai_cluster import automatic_proof

    app = FastAPI()
    recorded: dict[str, object] = {}
    monkeypatch.setattr(automatic_proof, "create_automatic_proof_app", lambda _: app)
    monkeypatch.setattr(
        automatic_proof.uvicorn,
        "run",
        lambda run_app, *, host, port: recorded.update(
            app=run_app, host=host, port=port
        ),
    )
    main(["http://remote.example:8000"])
    assert recorded == {"app": app, "host": PROOF_HOST, "port": PROOF_PORT}
