import asyncio
import json

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
from home_ai_cluster.core.models import ClusterRequest, ClusterResult
from home_ai_cluster.core.remote_transport import RemoteTransportError
from home_ai_cluster.main import create_app


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


def test_proof_chat_automatically_executes_one_remote_request() -> None:
    received: list[httpx.Request] = []

    def receiver(request: httpx.Request) -> httpx.Response:
        received.append(request)
        return httpx.Response(
            200,
            json={"content": "remote", "adapter": "fake", "node_id": "reported"},
        )

    async def run() -> httpx.Response:
        remote_client = httpx.AsyncClient(transport=httpx.MockTransport(receiver))
        app = create_automatic_proof_app(
            "http://remote.example:8000", client=remote_client
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://proof"
        ) as client:
            response = await client.post(
                "/v1/chat",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "capability": "chat",
                },
            )
        await remote_client.aclose()
        return response

    response = asyncio.run(run())
    assert response.status_code == 200
    assert response.json()["node_id"] == REMOTE_NODE_ID
    assert len(received) == 1
    assert received[0].url.path == "/internal/cluster/request"
    assert json.loads(received[0].content)["constraints"]["local_only"] is False


def test_proof_chat_failure_attempts_remote_once_without_fallback() -> None:
    attempts = 0

    def receiver(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    async def run() -> None:
        remote_client = httpx.AsyncClient(transport=httpx.MockTransport(receiver))
        app = create_automatic_proof_app(
            "http://remote.example:8000", client=remote_client
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://proof"
        ) as client:
            with pytest.raises(RemoteTransportError):
                await client.post(
                    "/v1/chat",
                    json={
                        "messages": [{"role": "user", "content": "Hello"}],
                        "capability": "chat",
                    },
                )
        await remote_client.aclose()

    asyncio.run(run())
    assert attempts == 1


def test_ordinary_chat_remains_local_only_without_proof_orchestrator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    requests: list[ClusterRequest] = []

    async def record_local_request(request: ClusterRequest) -> ClusterResult:
        requests.append(request)
        return ClusterResult(content="local", adapter="test", node_id="local")

    monkeypatch.setattr(
        routes, "handle_static_local_cluster_request", record_local_request
    )

    async def run() -> httpx.Response:
        app = create_app()
        assert app.state.automatic_proof_orchestrator is None
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://ordinary"
        ) as client:
            return await client.post(
                "/v1/chat",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "capability": "chat",
                },
            )

    response = asyncio.run(run())
    assert response.status_code == 200
    assert response.json()["node_id"] == "local"
    assert len(requests) == 1
    assert requests[0].constraints.local_only is True
