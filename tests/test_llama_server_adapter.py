import asyncio
import json

import httpx
import pytest

from home_ai_cluster.adapters.base import (
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
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
            ChatMessage(role="user", content="My name is André."),
            ChatMessage(role="assistant", content="Hello, André."),
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


def test_llama_server_adapter_name_and_capabilities() -> None:
    adapter = LlamaServerAdapter(model="phase-5-gemma")

    assert adapter.name == "llama-server"
    assert adapter.capabilities() == [
        Capability(name="chat"),
        Capability(name="summarize"),
        Capability(name="classify"),
    ]
    assert Capability(name="summarization") not in adapter.capabilities()
    assert Capability(name="classification") not in adapter.capabilities()


def test_llama_server_adapter_health_returns_available_when_ready() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/health"
        return httpx.Response(200, json={"status": "ok"})

    adapter = LlamaServerAdapter(
        model="phase-5-gemma",
        transport=httpx.MockTransport(handler),
    )

    assert adapter.health() == AdapterHealth(available=True)


def test_llama_server_adapter_health_returns_unavailable_when_unreachable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    adapter = LlamaServerAdapter(
        model="phase-5-gemma",
        transport=httpx.MockTransport(handler),
    )

    health = adapter.health()

    assert health.available is False
    assert health.reason is not None
    assert "connection refused" in health.reason


def test_llama_server_adapter_chat_translates_cluster_request() -> None:
    seen_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/chat/completions"
        seen_payloads.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"role": "assistant", "content": "Hello back"}},
                ],
                "model": "phase-5-gemma",
            },
        )

    adapter = LlamaServerAdapter(
        model="configured-model",
        transport=httpx.MockTransport(handler),
    )

    asyncio.run(adapter.chat(make_request()))

    assert seen_payloads == [
        {
            "model": "configured-model",
            "messages": [
                {"role": "system", "content": "Be brief."},
                {"role": "user", "content": "My name is André."},
                {"role": "assistant", "content": "Hello, André."},
            ],
            "stream": False,
        }
    ]


def test_llama_server_adapter_chat_normalizes_response_and_loaded_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"role": "assistant", "content": "Hello back"}},
                ],
                "model": "loaded-model",
                "usage": {"prompt_tokens": 12},
            },
        )

    adapter = LlamaServerAdapter(
        model="configured-model",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(adapter.chat(make_request()))

    assert result == RuntimeResult(
        content="Hello back",
        adapter="llama-server",
        model="loaded-model",
    )
    assert not hasattr(result, "node_id")
    assert set(result.model_dump()) == {"content", "adapter", "model"}


def test_llama_server_adapter_summarize_maps_source_text_to_chat_transport() -> None:
    source = '  First line.\n</source> "Quoted" text.\nLast line.  '
    seen_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/chat/completions"
        seen_payloads.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Summary"}}],
                "model": "loaded-model",
            },
        )

    adapter = LlamaServerAdapter(
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
        adapter="llama-server",
        model="loaded-model",
    )


def test_llama_server_adapter_summarize_accepts_empty_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": ""}}]},
        )

    result = asyncio.run(
        LlamaServerAdapter(
            model="configured-model",
            transport=httpx.MockTransport(handler),
        ).summarize(make_summarize_request())
    )

    assert result.content == ""


def test_llama_server_adapter_classify_maps_normalized_values_to_chat_transport() -> (
    None
):
    source = '  Source </source> "quoted" étiquette\n'
    labels = ["invoice", "Invoice", " invoice ", '</label> "étiquette"']
    seen_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/chat/completions"
        seen_payloads.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "invoice"}}]},
        )

    result = asyncio.run(
        LlamaServerAdapter(
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
                        "additional text.\n\n"
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
    "content,model",
    [
        ("invoice", None),
        ("invoice\n", 42),
        ('"invoice"', "loaded-model"),
        ("The label is invoice", None),
        ("", None),
    ],
)
def test_llama_server_adapter_classify_returns_content_without_repair_or_model_metadata(
    content: str,
    model: object,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body: dict[str, object] = {"choices": [{"message": {"content": content}}]}
        if model is not None:
            body["model"] = model
        return httpx.Response(200, json=body)

    result = asyncio.run(
        LlamaServerAdapter(
            model="configured-model",
            transport=httpx.MockTransport(handler),
        ).classify(make_classify_request())
    )

    assert result == content


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"choices": []},
        {"choices": [{}]},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": 42}}]},
    ],
)
def test_llama_server_adapter_classify_translates_malformed_response(
    body: object,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(
            LlamaServerAdapter(
                model="configured-model",
                transport=httpx.MockTransport(handler),
            ).classify(make_classify_request())
        )

    assert str(exc_info.value) == "Runtime adapter unavailable"
    assert isinstance(
        exc_info.value.__cause__,
        (IndexError, KeyError, TypeError, ValueError),
    )


def test_llama_server_adapter_classify_client_has_no_timeout(
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
                json={"choices": [{"message": {"content": "invoice"}}]},
                request=httpx.Request(
                    "POST",
                    "http://localhost:8080/v1/chat/completions",
                ),
            )

    monkeypatch.setattr(httpx, "AsyncClient", CapturingAsyncClient)

    asyncio.run(
        LlamaServerAdapter(model="configured-model").classify(make_classify_request())
    )

    assert created_kwargs["timeout"] is None


def test_llama_server_adapter_classify_translates_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError) as exc_info:
        asyncio.run(
            LlamaServerAdapter(
                model="configured-model",
                transport=httpx.MockTransport(handler),
            ).classify(make_classify_request())
        )

    assert str(exc_info.value) == (
        "Runtime connection unavailable before request transmission"
    )
    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)


@pytest.mark.parametrize("error_type", [httpx.ReadTimeout, httpx.RemoteProtocolError])
def test_llama_server_adapter_classify_translates_ambiguous_transport_failures(
    error_type: type[httpx.HTTPError],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error_type("transport failed", request=request)

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(
            LlamaServerAdapter(
                model="configured-model",
                transport=httpx.MockTransport(handler),
            ).classify(make_classify_request())
        )

    assert not isinstance(
        exc_info.value, RuntimeConnectionUnavailableBeforeRequestError
    )
    assert isinstance(exc_info.value.__cause__, error_type)


def test_llama_server_adapter_classify_translates_non_2xx_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503, json={"error": {"message": "loading"}}, request=request
        )

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(
            LlamaServerAdapter(
                model="configured-model",
                transport=httpx.MockTransport(handler),
            ).classify(make_classify_request())
        )

    assert str(exc_info.value) == "Runtime adapter unavailable"
    assert isinstance(exc_info.value.__cause__, httpx.HTTPStatusError)


def test_llama_server_adapter_summarize_translates_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    adapter = LlamaServerAdapter(
        model="configured-model",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError):
        asyncio.run(adapter.summarize(make_summarize_request()))


def test_llama_server_adapter_summarize_translates_malformed_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    adapter = LlamaServerAdapter(
        model="configured-model",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(RuntimeAdapterUnavailableError):
        asyncio.run(adapter.summarize(make_summarize_request()))


def test_llama_server_adapter_uses_configured_model_without_response_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Hello back"}}]},
        )

    adapter = LlamaServerAdapter(
        model="configured-model",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(adapter.chat(make_request()))

    assert result.model == "configured-model"


def test_llama_server_adapter_chat_client_has_no_timeout(
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
                json={"choices": [{"message": {"content": "Hi"}}]},
                request=httpx.Request(
                    "POST",
                    "http://localhost:8080/v1/chat/completions",
                ),
            )

    monkeypatch.setattr(httpx, "AsyncClient", CapturingAsyncClient)

    asyncio.run(LlamaServerAdapter(model="phase-5-gemma").chat(make_request()))

    assert created_kwargs["timeout"] is None


def test_llama_server_adapter_translates_pre_request_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    adapter = LlamaServerAdapter(
        model="phase-5-gemma",
        transport=httpx.MockTransport(handler),
    )

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
def test_llama_server_adapter_chat_translates_ambiguous_transport_failures(
    error_type: type[httpx.HTTPError],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error_type("transport failed", request=request)

    adapter = LlamaServerAdapter(
        model="phase-5-gemma",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(adapter.chat(make_request()))

    assert not isinstance(
        exc_info.value,
        RuntimeConnectionUnavailableBeforeRequestError,
    )
    assert isinstance(exc_info.value.__cause__, error_type)


def test_llama_server_adapter_chat_translates_non_2xx_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            json={"error": {"message": "loading"}},
            request=request,
        )

    adapter = LlamaServerAdapter(
        model="phase-5-gemma",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(adapter.chat(make_request()))

    assert str(exc_info.value) == "Runtime adapter unavailable"
    assert isinstance(exc_info.value.__cause__, httpx.HTTPStatusError)


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {"content": 42}}]},
        {"choices": [{"message": {"content": "Hello"}}], "model": 42},
    ],
)
def test_llama_server_adapter_chat_translates_malformed_response(
    body: object,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    adapter = LlamaServerAdapter(
        model="phase-5-gemma",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(adapter.chat(make_request()))

    assert str(exc_info.value) == "Runtime adapter unavailable"
    assert isinstance(
        exc_info.value.__cause__,
        (IndexError, KeyError, TypeError, ValueError),
    )
