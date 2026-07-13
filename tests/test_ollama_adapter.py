import asyncio
import json

import httpx
import pytest

from home_ai_cluster.adapters.base import (
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    RuntimeResult,
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

    assert result == RuntimeResult(
        content="Hello back",
        adapter="ollama",
        model="llama3.2",
    )
    assert not hasattr(result, "node_id")


def test_ollama_adapter_chat_client_has_no_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_kwargs: dict[str, object] = {}

    class CapturingAsyncClient:
        def __init__(self, **kwargs: object) -> None:
            created_kwargs.update(kwargs)

        async def __aenter__(self) -> "CapturingAsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(self, path: str, *, json: dict[str, object]) -> httpx.Response:
            return httpx.Response(
                200,
                json={"message": {"role": "assistant", "content": "Hi"}},
                request=httpx.Request("POST", "http://localhost:11434/api/chat"),
            )

    monkeypatch.setattr(httpx, "AsyncClient", CapturingAsyncClient)

    asyncio.run(OllamaAdapter().chat(make_request()))

    assert created_kwargs["timeout"] is None


def test_ollama_adapter_chat_translates_connection_failure_before_sending() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    adapter = OllamaAdapter(transport=httpx.MockTransport(handler))

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError) as exc_info:
        asyncio.run(adapter.chat(make_request()))

    assert str(exc_info.value) == (
        "Runtime connection unavailable before request transmission"
    )
    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)


@pytest.mark.parametrize(
    "error_type",
    [
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.WriteTimeout,
        httpx.PoolTimeout,
        httpx.WriteError,
        httpx.ReadError,
        httpx.RemoteProtocolError,
    ],
)
def test_ollama_adapter_chat_does_not_translate_ambiguous_transport_failures(
    error_type: type[httpx.HTTPError],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error_type("transport failed", request=request)

    adapter = OllamaAdapter(transport=httpx.MockTransport(handler))

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(adapter.chat(make_request()))

    assert not isinstance(
        exc_info.value,
        RuntimeConnectionUnavailableBeforeRequestError,
    )
    assert isinstance(exc_info.value.__cause__, error_type)


def test_ollama_adapter_chat_translates_non_2xx_response_to_adapter_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            json={"error": "ollama runtime is warming up"},
            request=request,
        )

    adapter = OllamaAdapter(transport=httpx.MockTransport(handler))

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(adapter.chat(make_request()))

    assert str(exc_info.value) == "Runtime adapter unavailable"
    assert not isinstance(
        exc_info.value,
        RuntimeConnectionUnavailableBeforeRequestError,
    )
    assert isinstance(exc_info.value.__cause__, httpx.HTTPStatusError)
