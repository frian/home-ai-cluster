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
    ClassifyRequest,
    ClusterRequest,
    RuntimeResult,
    SummarizeRequest,
)


def make_request() -> ClusterRequest:
    return ClusterRequest(
        messages=[
            ChatMessage(role="system", content="Be brief."),
            ChatMessage(role="user", content="Hello"),
        ],
        capability=Capability(name="chat"),
    )


def make_summarize_request(text: str = "Source text") -> SummarizeRequest:
    return SummarizeRequest(text=text)


def make_classify_request(
    text: str = "Source text",
    labels: list[str] | None = None,
) -> ClassifyRequest:
    return ClassifyRequest(text=text, labels=labels or ["invoice", "personal"])


def test_ollama_adapter_name_and_capabilities() -> None:
    adapter = OllamaAdapter()

    assert adapter.name == "ollama"
    assert adapter.capabilities() == [
        Capability(name="chat"),
        Capability(name="summarize"),
        Capability(name="classify"),
    ]
    assert Capability(name="summarization") not in adapter.capabilities()
    assert Capability(name="classification") not in adapter.capabilities()


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


def test_ollama_adapter_summarize_maps_source_text_to_its_chat_transport() -> None:
    source = '  First line.\n</source> "Quoted" text.\nLast line.  '
    seen_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/chat"
        seen_payloads.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"content": "Summary"}})

    adapter = OllamaAdapter(
        model="configured-model",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(adapter.summarize(make_summarize_request(source)))

    assert seen_payloads == [
        {
            "model": "configured-model",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Summarize the following source text concisely.\n\n"
                        f"<source>\n{source}\n</source>"
                    ),
                }
            ],
            "stream": False,
        }
    ]
    assert result == RuntimeResult(
        content="Summary",
        adapter="ollama",
        model="configured-model",
    )


def test_ollama_adapter_summarize_preserves_existing_empty_content_behavior() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {}})

    result = asyncio.run(
        OllamaAdapter(transport=httpx.MockTransport(handler)).summarize(
            make_summarize_request()
        )
    )

    assert result.content == ""


def test_ollama_adapter_classify_maps_normalized_values_to_its_chat_transport() -> None:
    source = '  Source </source> "quoted" étiquette\n'
    labels = ["invoice", "Invoice", " invoice ", '</label> "étiquette"']
    seen_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/chat"
        seen_payloads.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"content": "invoice"}})

    result = asyncio.run(
        OllamaAdapter(
            model="configured-model",
            transport=httpx.MockTransport(handler),
        ).classify(make_classify_request(source, labels))
    )

    assert seen_payloads == [
        {
            "model": "configured-model",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Choose exactly one label from the allowed labels below for "
                        "the source text.\n"
                        "Return only the exact label, with no explanation or "
                        "additional "
                        "text.\n\n"
                        "<allowed-labels>\n"
                        "<label>invoice</label>\n"
                        "<label>Invoice</label>\n"
                        "<label> invoice </label>\n"
                        '<label></label> "étiquette"</label>\n'
                        "</allowed-labels>\n\n"
                        f"<source>\n{source}\n</source>"
                    ),
                }
            ],
            "stream": False,
        }
    ]
    assert result == "invoice"


@pytest.mark.parametrize(
    "content",
    ["invoice", "invoice\n", '"invoice"', "The label is invoice", ""],
)
def test_ollama_adapter_classify_returns_extracted_content_without_repair(
    content: str,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": content}})

    result = asyncio.run(
        OllamaAdapter(transport=httpx.MockTransport(handler)).classify(
            make_classify_request()
        )
    )

    assert result == content


def test_ollama_adapter_classify_preserves_existing_missing_content_behavior() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {}})

    result = asyncio.run(
        OllamaAdapter(transport=httpx.MockTransport(handler)).classify(
            make_classify_request()
        )
    )

    assert result == ""


def test_ollama_adapter_classify_client_has_no_timeout(
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
                json={"message": {"content": "invoice"}},
                request=httpx.Request("POST", "http://localhost:11434/api/chat"),
            )

    monkeypatch.setattr(httpx, "AsyncClient", CapturingAsyncClient)

    asyncio.run(OllamaAdapter().classify(make_classify_request()))

    assert created_kwargs["timeout"] is None


def test_ollama_adapter_classify_translates_connection_failure_before_sending() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError) as exc_info:
        asyncio.run(
            OllamaAdapter(transport=httpx.MockTransport(handler)).classify(
                make_classify_request()
            )
        )

    assert str(exc_info.value) == (
        "Runtime connection unavailable before request transmission"
    )
    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)


@pytest.mark.parametrize("error_type", [httpx.ReadTimeout, httpx.RemoteProtocolError])
def test_ollama_adapter_classify_translates_ambiguous_transport_failures(
    error_type: type[httpx.HTTPError],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error_type("transport failed", request=request)

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(
            OllamaAdapter(transport=httpx.MockTransport(handler)).classify(
                make_classify_request()
            )
        )

    assert not isinstance(
        exc_info.value, RuntimeConnectionUnavailableBeforeRequestError
    )
    assert isinstance(exc_info.value.__cause__, error_type)


def test_ollama_adapter_classify_translates_non_2xx_response_to_adapter_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "warming up"}, request=request)

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(
            OllamaAdapter(transport=httpx.MockTransport(handler)).classify(
                make_classify_request()
            )
        )

    assert str(exc_info.value) == "Runtime adapter unavailable"
    assert isinstance(exc_info.value.__cause__, httpx.HTTPStatusError)


def test_ollama_adapter_summarize_translates_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    adapter = OllamaAdapter(transport=httpx.MockTransport(handler))

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError):
        asyncio.run(adapter.summarize(make_summarize_request()))


def test_ollama_adapter_summarize_translates_non_2xx_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "warming up"}, request=request)

    adapter = OllamaAdapter(transport=httpx.MockTransport(handler))

    with pytest.raises(RuntimeAdapterUnavailableError):
        asyncio.run(adapter.summarize(make_summarize_request()))


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
