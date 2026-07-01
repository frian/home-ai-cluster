import asyncio
import json

import httpx
import pytest

from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
)


def make_request() -> ClusterRequest:
    return ClusterRequest(
        messages=[
            ChatMessage(role="system", content="Be brief."),
            ChatMessage(role="user", content="Hello"),
        ],
        capability=Capability(name="chat"),
    )


def test_ollama_adapter_name_and_capabilities() -> None:
    adapter = OllamaAdapter()

    assert adapter.name == "ollama"
    assert adapter.capabilities() == [Capability(name="chat")]


def test_ollama_adapter_health_returns_available_when_version_responds() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/version"
        return httpx.Response(200, json={"version": "0.0.0"})

    adapter = OllamaAdapter(transport=httpx.MockTransport(handler))

    assert adapter.health() == AdapterHealth(available=True)


def test_ollama_adapter_health_returns_unavailable_when_ollama_is_unreachable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    adapter = OllamaAdapter(transport=httpx.MockTransport(handler))

    health = adapter.health()

    assert health.available is False
    assert health.reason is not None
    assert "connection refused" in health.reason


@pytest.mark.parametrize("model", ["llama3.2", "custom-model"])
def test_ollama_adapter_chat_translates_cluster_request_to_ollama(
    model: str,
) -> None:
    seen_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/chat"
        seen_payloads.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": "Hi"}},
        )

    adapter = OllamaAdapter(model=model, transport=httpx.MockTransport(handler))

    asyncio.run(adapter.chat(make_request()))

    assert seen_payloads == [
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "Be brief."},
                {"role": "user", "content": "Hello"},
            ],
            "stream": False,
        }
    ]


def test_ollama_adapter_chat_returns_cluster_result_from_ollama_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": "Hello back"}},
        )

    adapter = OllamaAdapter(
        model="llama3.2",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(adapter.chat(make_request()))

    assert result == ClusterResult(
        content="Hello back",
        adapter="ollama",
        model="llama3.2",
    )
