import asyncio

import httpx
import pytest
from pydantic import ValidationError

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api.routes import InternalClusterStatusResponse
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
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

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        user_messages = [
            message.content for message in request.messages if message.role == "user"
        ]
        content = user_messages[-1] if user_messages else request.messages[-1].content

        return RuntimeResult(content=content, adapter=self.name)


class UnavailableChatAdapter(TestChatAdapter):
    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        raise RuntimeAdapterUnavailableError("Runtime adapter unavailable")


class RuntimeSpecificUnavailableChatAdapter(TestChatAdapter):
    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        cause = RuntimeError("ollama connection refused on localhost:11434")
        raise RuntimeAdapterUnavailableError("ollama leaked detail") from cause


class StatusAdapter:
    def __init__(self, health_result: AdapterHealth | Exception) -> None:
        self._health_result = health_result
        self.health_calls = 0
        self.chat_calls = 0

    @property
    def name(self) -> str:
        return "private-adapter-name"

    def health(self) -> AdapterHealth:
        self.health_calls += 1
        if isinstance(self._health_result, Exception):
            raise self._health_result
        return self._health_result

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.chat_calls += 1
        raise AssertionError("status endpoint must not execute chat")


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


def create_status_node_registry() -> NodeRegistry:
    return NodeRegistry(
        [
            NodeDescription(
                id="private-machine-name",
                name="Private machine name",
                availability="available",
                health=NodeHealth(healthy=True),
                capabilities=[Capability(name="chat")],
                adapters=["private-adapter-name"],
            )
        ]
    )


async def post_async(path: str, payload: dict[str, object]) -> httpx.Response:
    transport = httpx.ASGITransport(app=create_app())

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.post(path, json=payload)


async def post_chat_async(payload: dict[str, object]) -> httpx.Response:
    return await post_async("/v1/chat", payload)


def post_chat(payload: dict[str, object]) -> httpx.Response:
    return asyncio.run(post_chat_async(payload))


async def post_internal_cluster_request_async(
    payload: dict[str, object],
) -> httpx.Response:
    return await post_async("/internal/cluster/request", payload)


def post_internal_cluster_request(payload: dict[str, object]) -> httpx.Response:
    return asyncio.run(post_internal_cluster_request_async(payload))


async def get_internal_cluster_status_async() -> httpx.Response:
    transport = httpx.ASGITransport(app=create_app())

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.get("/internal/cluster/status")


def get_internal_cluster_status() -> httpx.Response:
    return asyncio.run(get_internal_cluster_status_async())


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
        "node_id": "local",
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


def test_internal_cluster_request_endpoint_accepts_normalized_cluster_request(
    use_test_registry: None,
) -> None:
    response = post_internal_cluster_request(
        {
            "messages": [{"role": "user", "content": "Hello internal"}],
            "capability": {"name": "chat"},
            "constraints": {"local_only": True},
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "content": "Hello internal",
        "adapter": "test",
        "model": None,
        "node_id": "local",
    }


def test_internal_cluster_request_endpoint_rejects_unsupported_capability(
    use_test_registry: None,
) -> None:
    response = post_internal_cluster_request(
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": {"name": "embeddings"},
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No adapter provides capability: embeddings",
    }


@pytest.mark.parametrize(
    ("health_result", "expected_runtime_status"),
    [
        (AdapterHealth(available=True), "available"),
        (AdapterHealth(available=False), "unavailable"),
        (
            RuntimeError("http://private-host:11434 authorization=secret"),
            "observation-failed",
        ),
    ],
)
def test_internal_cluster_status_returns_one_normalized_local_observation(
    monkeypatch: pytest.MonkeyPatch,
    health_result: AdapterHealth | Exception,
    expected_runtime_status: str,
) -> None:
    from home_ai_cluster.api import routes

    adapter = StatusAdapter(health_result)
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_status_node_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = get_internal_cluster_status()

    assert response.status_code == 200
    assert response.json() == {"runtime_status": expected_runtime_status}
    assert adapter.health_calls == 1
    assert adapter.chat_calls == 0


def test_internal_cluster_status_hides_local_runtime_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    adapter = StatusAdapter(
        RuntimeError("http://private-host:11434 authorization=secret")
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_status_node_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = get_internal_cluster_status()

    assert set(response.json()) == {"runtime_status"}
    assert response.json() == {"runtime_status": "observation-failed"}
    for forbidden in (
        "private-machine-name",
        "Private machine name",
        "private-adapter-name",
        "private-host",
        "authorization",
        "secret",
        "node_id",
        "application_status",
        "declaration_status",
        "reason",
        "model",
        "url",
    ):
        assert forbidden not in response.text


def test_internal_cluster_status_returns_safe_error_when_snapshot_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    def fail_snapshot(*_: object, **__: object) -> dict[str, object]:
        raise RuntimeError("http://private-host:11434 authorization=secret")

    monkeypatch.setattr(routes, "project_health_snapshot", fail_snapshot)

    response = get_internal_cluster_status()

    assert response.status_code == 500
    assert response.json() == {"detail": "Unable to inspect local runtime status"}
    assert "private-host" not in response.text
    assert "authorization" not in response.text


def test_internal_cluster_status_response_is_closed_and_immutable() -> None:
    response = InternalClusterStatusResponse(runtime_status="available")

    with pytest.raises(ValidationError):
        InternalClusterStatusResponse(
            runtime_status="unknown",
            node_id="local",
        )
    with pytest.raises(ValidationError):
        response.runtime_status = "unavailable"  # type: ignore[misc]
