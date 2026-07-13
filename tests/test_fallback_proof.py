import asyncio
import json

import httpx
import pytest

from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.fallback_proof import (
    PROOF_HOST,
    PROOF_PORT,
    REMOTE_NODE_ID,
    create_fallback_proof_app,
    main,
    parse_args,
)


def test_fallback_proof_requires_one_absolute_http_address() -> None:
    with pytest.raises(SystemExit):
        parse_args([])
    with pytest.raises(SystemExit):
        parse_args(["https://remote.example:8000"])
    assert parse_args(["http://remote.example:8000/"]).remote_address == (
        "http://remote.example:8000"
    )


def test_fallback_proof_composes_matching_local_and_declared_remote() -> None:
    client = httpx.AsyncClient()
    app = create_fallback_proof_app("http://remote.example:8000", client=client)
    declarations = app.state.fallback_proof_remote_registry.list_declarations()

    assert len(declarations) == 1
    assert declarations[0].node.id == REMOTE_NODE_ID
    assert declarations[0].node.capabilities[0].name == "chat"
    asyncio.run(client.aclose())


def test_fallback_proof_chat_falls_back_once_after_narrow_local_failure() -> None:
    remote_requests: list[httpx.Request] = []

    def local_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    def remote_handler(request: httpx.Request) -> httpx.Response:
        remote_requests.append(request)
        return httpx.Response(
            200,
            json={"content": "remote", "adapter": "fake", "node_id": "reported"},
        )

    async def run() -> httpx.Response:
        remote_client = httpx.AsyncClient(transport=httpx.MockTransport(remote_handler))
        app = create_fallback_proof_app(
            "http://remote.example:8000",
            client=remote_client,
            local_adapter=OllamaAdapter(transport=httpx.MockTransport(local_handler)),
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
    assert len(remote_requests) == 1
    assert json.loads(remote_requests[0].content)["constraints"]["local_only"] is False


def test_main_uses_fixed_loopback_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    from home_ai_cluster import fallback_proof

    app = object()
    recorded: dict[str, object] = {}
    monkeypatch.setattr(fallback_proof, "create_fallback_proof_app", lambda _: app)
    monkeypatch.setattr(
        fallback_proof.uvicorn,
        "run",
        lambda run_app, *, host, port: recorded.update(
            app=run_app, host=host, port=port
        ),
    )

    main(["http://remote.example:8000"])

    assert recorded == {"app": app, "host": PROOF_HOST, "port": PROOF_PORT}
