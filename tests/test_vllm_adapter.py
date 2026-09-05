import argparse
import asyncio
import json

import httpx
import pytest

from home_ai_cluster.adapters.base import (
    RuntimeAdapter,
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.adapters.vllm import VllmAdapter
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClassifyRequest,
    ClusterRequest,
    RuntimeResult,
    SummarizeRequest,
)
from home_ai_cluster.local_http import local_http_url


def make_request() -> ClusterRequest:
    return ClusterRequest(
        messages=[
            ChatMessage(role="system", content="Be brief."),
            ChatMessage(role="user", content="My name is André."),
            ChatMessage(role="assistant", content="Hello, André."),
        ],
        capability=Capability(name="chat"),
    )


def make_adapter(
    transport: httpx.AsyncBaseTransport | None = None,
) -> VllmAdapter:
    return VllmAdapter(
        base_url="http://127.0.0.1:8000",
        model="configured-model",
        transport=transport,
    )


def make_summarize_request(text: str = "Source text") -> SummarizeRequest:
    return SummarizeRequest(text=text)


def make_classify_request(
    text: str = "Source text",
    labels: list[str] | None = None,
) -> ClassifyRequest:
    return ClassifyRequest(text=text, labels=labels or ["invoice", "personal"])


def test_vllm_adapter_name_and_complete_capabilities() -> None:
    adapter = make_adapter()

    assert adapter.name == "vllm"
    assert adapter.capabilities() == [
        Capability(name="chat"),
        Capability(name="summarize"),
        Capability(name="classify"),
        Capability(name="code"),
    ]


def test_vllm_adapter_structurally_satisfies_runtime_adapter() -> None:
    adapter: RuntimeAdapter = make_adapter()

    assert adapter.name == "vllm"


def test_vllm_adapter_health_returns_available_when_ready() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/health"
        return httpx.Response(200, json={"status": "ok"})

    assert make_adapter(httpx.MockTransport(handler)).health() == AdapterHealth(
        available=True
    )


@pytest.mark.parametrize("failure", [httpx.ConnectError, httpx.ReadTimeout])
def test_vllm_adapter_health_returns_unavailable_on_http_failure(
    failure: type[httpx.HTTPError],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise failure("runtime unavailable", request=request)

    health = make_adapter(httpx.MockTransport(handler)).health()

    assert health.available is False
    assert health.reason is not None
    assert "runtime unavailable" in health.reason


def test_vllm_adapter_health_client_disables_ambient_http_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_kwargs: dict[str, object] = {}

    class CapturingClient:
        def __init__(self, **kwargs: object) -> None:
            created_kwargs.update(kwargs)

        def __enter__(self) -> "CapturingClient":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def get(self, path: str) -> httpx.Response:
            return httpx.Response(
                200,
                request=httpx.Request("GET", f"http://127.0.0.1:8000{path}"),
            )

    monkeypatch.setattr(httpx, "Client", CapturingClient)

    assert make_adapter().health().available is True
    assert created_kwargs["trust_env"] is False


def test_vllm_adapter_chat_translates_cluster_request() -> None:
    seen_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/chat/completions"
        seen_payloads.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Hello back"}}],
                "model": "loaded-model",
            },
        )

    asyncio.run(make_adapter(httpx.MockTransport(handler)).chat(make_request()))

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


def test_vllm_adapter_chat_normalizes_response_and_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Hello back"}}],
                "model": "loaded-model",
                "usage": {"prompt_tokens": 12},
            },
        )

    result = asyncio.run(
        make_adapter(httpx.MockTransport(handler)).chat(make_request())
    )

    assert result == RuntimeResult(
        content="Hello back",
        adapter="vllm",
        model="loaded-model",
    )
    assert set(result.model_dump()) == {"content", "adapter", "model"}


def test_vllm_adapter_chat_uses_configured_model_when_response_omits_it() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Hello back"}}]},
        )

    result = asyncio.run(
        make_adapter(httpx.MockTransport(handler)).chat(make_request())
    )

    assert result.model == "configured-model"


def test_vllm_adapter_summarize_maps_source_text_to_chat_transport() -> None:
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

    result = asyncio.run(
        make_adapter(httpx.MockTransport(handler)).summarize(
            make_summarize_request(source)
        )
    )

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
        adapter="vllm",
        model="loaded-model",
    )


def test_vllm_adapter_summarize_translates_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError):
        asyncio.run(
            make_adapter(httpx.MockTransport(handler)).summarize(
                make_summarize_request()
            )
        )


def test_vllm_adapter_summarize_translates_non_2xx_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"}, request=request)

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(
            make_adapter(httpx.MockTransport(handler)).summarize(
                make_summarize_request()
            )
        )

    assert isinstance(exc_info.value.__cause__, httpx.HTTPStatusError)


def test_vllm_adapter_summarize_translates_malformed_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    with pytest.raises(RuntimeAdapterUnavailableError):
        asyncio.run(
            make_adapter(httpx.MockTransport(handler)).summarize(
                make_summarize_request()
            )
        )


def test_vllm_adapter_classify_uses_private_structured_choice_output() -> None:
    source = '  Source </source> "quoted" étiquette\n'
    labels = ["invoice", "Invoice", " invoice ", '</label> "étiquette"']
    seen_payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/chat/completions"
        seen_payloads.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "invoice"}}],
                "model": "loaded-model",
            },
        )

    result = asyncio.run(
        make_adapter(httpx.MockTransport(handler)).classify(
            make_classify_request(source, labels)
        )
    )

    assert seen_payloads == [
        {
            "model": "configured-model",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Choose the single best matching label for the source text.\n\n"
                        f"Source text:\n{source}"
                    ),
                }
            ],
            "stream": False,
            "structured_outputs": {"choice": labels},
        }
    ]
    assert result == "invoice"


def test_vllm_adapter_classify_returns_unknown_proposal_without_repair() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "unknown"}}]},
        )

    result = asyncio.run(
        make_adapter(httpx.MockTransport(handler)).classify(make_classify_request())
    )

    assert result == "unknown"


def test_vllm_adapter_classify_translates_malformed_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {}}]})

    with pytest.raises(RuntimeAdapterUnavailableError):
        asyncio.run(
            make_adapter(httpx.MockTransport(handler)).classify(make_classify_request())
        )


def test_vllm_adapter_code_uses_existing_chat_transport() -> None:
    request = ClusterRequest(
        messages=[ChatMessage(role="user", content="Write a function.")],
        capability=Capability(name="code"),
    )
    seen_payloads: list[dict[str, object]] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        assert http_request.url.path == "/v1/chat/completions"
        seen_payloads.append(json.loads(http_request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "def f(): pass"}}]},
        )

    result = asyncio.run(make_adapter(httpx.MockTransport(handler)).chat(request))

    assert seen_payloads == [
        {
            "model": "configured-model",
            "messages": [{"role": "user", "content": "Write a function."}],
            "stream": False,
        }
    ]
    assert result == RuntimeResult(
        content="def f(): pass",
        adapter="vllm",
        model="configured-model",
    )


def test_vllm_adapter_chat_client_disables_ambient_http_environment(
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
                request=httpx.Request("POST", f"http://127.0.0.1:8000{path}"),
            )

    monkeypatch.setattr(httpx, "AsyncClient", CapturingAsyncClient)

    asyncio.run(make_adapter().chat(make_request()))

    assert created_kwargs["trust_env"] is False
    assert created_kwargs["timeout"] is None


def test_vllm_adapter_chat_translates_pre_request_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError) as exc_info:
        asyncio.run(make_adapter(httpx.MockTransport(handler)).chat(make_request()))

    assert str(exc_info.value) == (
        "Runtime connection unavailable before request transmission"
    )
    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)


@pytest.mark.parametrize(
    "failure",
    [httpx.ReadTimeout, httpx.RemoteProtocolError],
)
def test_vllm_adapter_chat_translates_other_http_failures(
    failure: type[httpx.HTTPError],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise failure("transport failed", request=request)

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(make_adapter(httpx.MockTransport(handler)).chat(make_request()))

    assert not isinstance(
        exc_info.value, RuntimeConnectionUnavailableBeforeRequestError
    )
    assert isinstance(exc_info.value.__cause__, failure)


def test_vllm_adapter_chat_translates_non_2xx_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"}, request=request)

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(make_adapter(httpx.MockTransport(handler)).chat(make_request()))

    assert isinstance(exc_info.value.__cause__, httpx.HTTPStatusError)


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"choices": []},
        {"choices": [{}]},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": 42}}]},
        {"choices": [{"message": {"content": "Hello"}}], "model": 42},
    ],
)
def test_vllm_adapter_chat_translates_malformed_response(body: object) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    with pytest.raises(RuntimeAdapterUnavailableError) as exc_info:
        asyncio.run(make_adapter(httpx.MockTransport(handler)).chat(make_request()))

    assert str(exc_info.value) == "Runtime adapter unavailable"
    assert isinstance(
        exc_info.value.__cause__,
        (IndexError, KeyError, TypeError, ValueError),
    )


def test_vllm_adapter_base_url_uses_existing_loopback_validation_boundary() -> None:
    assert local_http_url("http://127.0.0.1:8000") == "http://127.0.0.1:8000"

    with pytest.raises(argparse.ArgumentTypeError):
        local_http_url("http://runtime.example:8000")
