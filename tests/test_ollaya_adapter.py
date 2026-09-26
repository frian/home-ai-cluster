import asyncio
import json

import httpx
import pytest

from home_ai_cluster.adapters.base import (
    ClassifyExecutionAdapter,
    InvalidClassificationResultError,
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.adapters.ollaya import OllayaAdapter
from home_ai_cluster.core.executor import (
    InvalidClassificationLabelError,
    execute_local_routing_decision,
)
from home_ai_cluster.core.local_capability_binding import (
    LocalCapabilityBinding,
    LocalCapabilityBindings,
)
from home_ai_cluster.core.models import (
    Capability,
    ClassifyRequest,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.router import route_request


def request() -> ClassifyRequest:
    return ClassifyRequest(text="billing refund", labels=["invoice", "refund"])


def response(choice: object = "refund") -> dict[str, object]:
    return {
        "answers": {
            "classification": {
                "choice": choice,
                "confidence": 0.1,
                "probabilities": {"refund": 0.1},
            }
        },
        "model": "ignored",
    }


def adapter(transport: httpx.AsyncBaseTransport | None = None) -> OllayaAdapter:
    return OllayaAdapter(
        base_url="http://127.0.0.1:11435", model="explicit-model", transport=transport
    )


def test_identity_capability_contract_and_explicit_construction() -> None:
    instance = adapter()
    assert instance.name == "ollaya"
    assert instance.capabilities() == [Capability(name="classify")]
    assert isinstance(instance, ClassifyExecutionAdapter)
    assert not any(
        hasattr(instance, name) for name in ("chat", "summarize", "generate_image")
    )
    with pytest.raises(TypeError):
        OllayaAdapter(base_url="http://127.0.0.1:11435")  # type: ignore[call-arg]


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:11435",
        "http://192.168.1.2:11435",
        "http://example.test:11435",
        "http://127.0.0.1:11435/path",
        "http://127.0.0.1:11435?query=x",
        "http://user@127.0.0.1:11435",
    ],
)
def test_loopback_origin_is_required(url: str) -> None:
    with pytest.raises(Exception, match="absolute loopback http"):
        OllayaAdapter(base_url=url, model="explicit-model")


def test_native_choice_request_preserves_model_state_and_labels() -> None:
    seen: list[dict[str, object]] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        assert http_request.url.path == "/api/decide"
        seen.append(json.loads(http_request.content))
        return httpx.Response(200, json=response())

    result = asyncio.run(adapter(httpx.MockTransport(handler)).classify(request()))

    assert result == "refund"
    assert seen == [
        {
            "model": "explicit-model",
            "state": "billing refund",
            "questions": {
                "classification": {
                    "type": "choice",
                    "criteria": ["invoice", "refund"],
                }
            },
        }
    ]


@pytest.mark.parametrize(
    "body",
    [{}, {"answers": {}}, {"answers": {"classification": {}}}, response(2)],
)
def test_successful_unusable_response_is_invalid_classification_result(
    body: object,
) -> None:
    with pytest.raises(InvalidClassificationResultError):
        asyncio.run(
            adapter(
                httpx.MockTransport(lambda _: httpx.Response(200, json=body))
            ).classify(request())
        )


def test_out_of_set_choice_is_returned_unchanged() -> None:
    result = asyncio.run(
        adapter(
            httpx.MockTransport(lambda _: httpx.Response(200, json=response("unknown")))
        ).classify(request())
    )
    assert result == "unknown"


def test_transport_failure_semantics() -> None:
    def connection(request_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request_)

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError):
        asyncio.run(adapter(httpx.MockTransport(connection)).classify(request()))

    with pytest.raises(RuntimeAdapterUnavailableError):
        asyncio.run(
            adapter(httpx.MockTransport(lambda _: httpx.Response(503))).classify(
                request()
            )
        )


def test_client_disables_environment_and_has_no_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options: dict[str, object] = {}
    original = httpx.AsyncClient

    def create_client(**kwargs: object) -> httpx.AsyncClient:
        options.update(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(
        "home_ai_cluster.adapters.ollaya.httpx.AsyncClient", create_client
    )
    asyncio.run(
        adapter(
            httpx.MockTransport(lambda _: httpx.Response(200, json=response()))
        ).classify(request())
    )
    assert options["trust_env"] is False
    assert options["timeout"] is None


def test_programmatic_classify_binding_routes_and_executes() -> None:
    instance = adapter(
        httpx.MockTransport(lambda _: httpx.Response(200, json=response()))
    )
    binding = LocalCapabilityBinding(frozenset({"classify"}), instance)
    registry = AdapterRegistry(
        [instance], local_capability_bindings=LocalCapabilityBindings([binding])
    )
    node = NodeDescription(
        id="local",
        name="Local",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="classify")],
        adapters=[instance.name],
    )
    classify_request = request()
    decision = route_request(classify_request, NodeRegistry([node]), registry)
    assert decision.adapter is instance
    assert (
        asyncio.run(
            execute_local_routing_decision(classify_request, decision)
        ).selected_label
        == "refund"
    )
    with pytest.raises(InvalidClassificationLabelError):
        bad = adapter(
            httpx.MockTransport(lambda _: httpx.Response(200, json=response("unknown")))
        )
        bad_binding = LocalCapabilityBinding(frozenset({"classify"}), bad)
        bad_registry = AdapterRegistry(
            [bad], local_capability_bindings=LocalCapabilityBindings([bad_binding])
        )
        bad_decision = route_request(
            classify_request, NodeRegistry([node]), bad_registry
        )
        asyncio.run(execute_local_routing_decision(classify_request, bad_decision))
