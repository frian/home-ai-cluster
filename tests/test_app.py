import asyncio

import httpx
import pytest
from fastapi import FastAPI

from home_ai_cluster.api.wiring import build_static_remote_proof_wiring
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.main import create_app


class RecordingAdapter:
    def __init__(self) -> None:
        self.chat_requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return "recording"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        self.chat_requests.append(request)
        return ClusterResult(content="local result", adapter=self.name)


class RecordingRemoteTransport:
    def __init__(self) -> None:
        self.requests: list[ClusterRequest] = []
        self.declarations: list[RemoteNodeDeclaration] = []

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        self.requests.append(request)
        self.declarations.append(declaration)
        return ClusterResult(content="remote result", adapter="remote")


def make_node(node_id: str, adapter_name: str = "recording") -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=[adapter_name],
    )


def make_remote_declaration() -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node("remote", "remote-adapter"),
        transport_address="http://remote.local:8000",
    )


def make_static_remote_proof_wiring(
    transport: RecordingRemoteTransport,
    adapter: RecordingAdapter | None = None,
):
    return build_static_remote_proof_wiring(
        node_registry=NodeRegistry([make_node("local")]),
        adapter_registry=AdapterRegistry([adapter or RecordingAdapter()]),
        remote_declaration=make_remote_declaration(),
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
    )


def test_create_app_returns_fastapi_application() -> None:
    app = create_app()

    assert isinstance(app, FastAPI)
    assert app.title == "Home AI Cluster"


def test_create_app_without_static_remote_proof_wiring_stores_none() -> None:
    app = create_app()

    assert app.state.static_remote_proof_wiring is None


def test_create_app_accepts_static_remote_proof_wiring() -> None:
    transport = RecordingRemoteTransport()
    wiring = make_static_remote_proof_wiring(transport)

    app = create_app(static_remote_proof_wiring=wiring)

    assert app.state.static_remote_proof_wiring is wiring
    assert transport.requests == []
    assert transport.declarations == []


def test_create_app_with_static_remote_proof_wiring_keeps_chat_local_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    adapter = RecordingAdapter()
    transport = RecordingRemoteTransport()
    wiring = make_static_remote_proof_wiring(transport, adapter)
    app = create_app(static_remote_proof_wiring=wiring)

    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        lambda: NodeRegistry([make_node("local")]),
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    async def post_chat() -> httpx.Response:
        asgi_transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=asgi_transport,
            base_url="http://testserver",
        ) as client:
            return await client.post(
                "/v1/chat",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "capability": "chat",
                },
            )

    response = asyncio.run(post_chat())

    assert response.status_code == 200
    assert response.json()["adapter"] == "recording"
    assert len(adapter.chat_requests) == 1
    assert transport.requests == []
    assert transport.declarations == []
