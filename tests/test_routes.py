import asyncio

import httpx
import pytest

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.main import create_app


class TestChatAdapter:
    @property
    def name(self) -> str:
        return "test"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        user_messages = [
            message.content
            for message in request.messages
            if message.role == "user"
        ]
        content = user_messages[-1] if user_messages else request.messages[-1].content

        return ClusterResult(content=content, adapter=self.name)


class UnavailableChatAdapter(TestChatAdapter):
    async def chat(self, request: ClusterRequest) -> ClusterResult:
        raise RuntimeAdapterUnavailableError("Runtime adapter unavailable")


class RuntimeSpecificUnavailableChatAdapter(TestChatAdapter):
    async def chat(self, request: ClusterRequest) -> ClusterResult:
        cause = RuntimeError("ollama connection refused on localhost:11434")
        raise RuntimeAdapterUnavailableError("ollama leaked detail") from cause


def create_test_registry() -> AdapterRegistry:
    return AdapterRegistry([TestChatAdapter()])


def create_unavailable_registry() -> AdapterRegistry:
    return AdapterRegistry([UnavailableChatAdapter()])


def create_runtime_specific_unavailable_registry() -> AdapterRegistry:
    return AdapterRegistry([RuntimeSpecificUnavailableChatAdapter()])


def create_test_node_registry() -> NodeRegistry:
    return NodeRegistry(
        [
            NodeDescription(
                id="local",
                name="Local node",
                availability="available",
                health=NodeHealth(healthy=True),
                capabilities=[Capability(name="chat")],
                adapters=["test"],
            )
        ]
    )


async def post_chat_async(payload: dict[str, object]) -> httpx.Response:
    transport = httpx.ASGITransport(app=create_app())

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.post("/v1/chat", json=payload)


def post_chat(payload: dict[str, object]) -> httpx.Response:
    return asyncio.run(post_chat_async(payload))


@pytest.fixture
def use_test_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    from home_ai_cluster.api import routes

    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        create_test_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_test_node_registry,
    )


def test_chat_endpoint_returns_cluster_result_json(use_test_registry: None) -> None:
    response = post_chat(
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": "chat",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "content": "Hello",
        "adapter": "test",
        "model": None,
    }
    assert "reason" not in response.json()
    assert "node" not in response.json()
    assert "selected_node" not in response.json()
    assert "routing" not in response.json()
    assert "health" not in response.json()


def test_chat_endpoint_uses_last_user_message(use_test_registry: None) -> None:
    response = post_chat(
        {
            "messages": [
                {"role": "user", "content": "First"},
                {"role": "assistant", "content": "Middle"},
                {"role": "user", "content": "Second"},
            ],
            "capability": "chat",
        },
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Second"


def test_chat_endpoint_rejects_unsupported_capability(
    use_test_registry: None,
) -> None:
    response = post_chat(
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": "embeddings",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No adapter provides capability: embeddings",
    }


def test_chat_endpoint_returns_503_when_runtime_adapter_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        create_unavailable_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_test_node_registry,
    )
    response = post_chat(
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": "chat",
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Runtime adapter unavailable"}


def test_chat_endpoint_hides_runtime_specific_unavailable_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        create_runtime_specific_unavailable_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_test_node_registry,
    )
    response = post_chat(
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": "chat",
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Runtime adapter unavailable"}
    assert "ollama" not in response.text
    assert "localhost:11434" not in response.text
    assert "connection refused" not in response.text
