import asyncio

import httpx

from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.api.wiring import (
    create_static_local_node_announcement,
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
)
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
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

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.chat_requests.append(request)
        return RuntimeResult(content="local result", adapter=self.name)


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
        return ClusterResult(
            content="remote result", adapter="remote", node_id="remote-response"
        )


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


def post_chat(payload: dict[str, object]) -> httpx.Response:
    async def post() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app())

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.post("/v1/chat", json=payload)

    return asyncio.run(post())


def test_create_static_runtime_adapter_registry_contains_ollama_adapter() -> None:
    registry = create_static_runtime_adapter_registry()

    adapters = registry.list_adapters()

    assert len(adapters) == 1
    assert isinstance(adapters[0], OllamaAdapter)
    assert adapters[0].name == "ollama"
    assert registry.adapters_for(Capability(name="chat")) == adapters


def test_create_static_local_node_announcement_returns_explicit_declaration() -> None:
    announcement = create_static_local_node_announcement()

    assert announcement.id == "local"
    assert announcement.name == "Local node"
    assert announcement.availability == "available"
    assert announcement.health == NodeHealth(healthy=True)
    assert announcement.capabilities == [
        Capability(name="chat"),
        Capability(name="summarize"),
    ]
    assert announcement.adapters == ["ollama"]
    assert "models" not in NodeDescription.model_fields


def test_create_static_local_node_registry_contains_static_local_node() -> None:
    registry = create_static_local_node_registry()
    announcement = create_static_local_node_announcement()

    nodes = registry.list_nodes()

    assert len(nodes) == 1
    assert nodes[0] == announcement
    assert nodes[0].model_dump() == {
        "id": "local",
        "name": "Local node",
        "availability": "available",
        "health": {"healthy": True, "reason": None},
        "capabilities": [{"name": "chat"}, {"name": "summarize"}],
        "adapters": ["ollama"],
    }
    assert "models" not in NodeDescription.model_fields
