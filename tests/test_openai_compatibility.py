import asyncio

import httpx
import pytest
from fastapi import HTTPException

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api.openai_compatibility import COMPATIBILITY_MODEL
from home_ai_cluster.core.models import Capability, ClusterRequest, ClusterResult
from home_ai_cluster.core.router import NoMatchingAdapterError
from home_ai_cluster.main import create_app
from home_ai_cluster.openai_compatibility import (
    COMPATIBILITY_HOST,
    create_openai_compatibility_app,
)


def compatibility_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "model": COMPATIBILITY_MODEL,
        "messages": [{"role": "user", "content": "Hello"}],
    }
    payload.update(overrides)
    return payload


def post(
    app,
    *,
    payload: object | None = None,
    content: str | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            if content is not None:
                return await client.post(
                    "/v1/chat/completions",
                    content=content,
                    headers=headers,
                )
            return await client.post(
                "/v1/chat/completions",
                json=payload,
                headers=headers,
            )

    return asyncio.run(send())


@pytest.fixture
def use_cluster_result(monkeypatch: pytest.MonkeyPatch) -> list[ClusterRequest]:
    from home_ai_cluster.api import openai_compatibility

    requests: list[ClusterRequest] = []

    async def handle(request: ClusterRequest, _) -> ClusterResult:
        requests.append(request)
        return ClusterResult(
            content="Cluster response",
            adapter="test-adapter",
            model="actual-model",
            node_id="selected-node",
        )

    monkeypatch.setattr(openai_compatibility, "handle_chat_cluster_request", handle)
    return requests


def test_valid_request_translates_through_cluster_flow(
    use_cluster_result: list[ClusterRequest],
) -> None:
    response = post(
        create_openai_compatibility_app(),
        payload=compatibility_payload(
            messages=[
                {"role": "system", "content": "System"},
                {"role": "user", "content": "User"},
                {"role": "assistant", "content": "Assistant"},
            ],
            stream=False,
            n=1,
        ),
    )

    assert response.status_code == 200
    assert use_cluster_result == [
        ClusterRequest(
            messages=[
                {"role": "system", "content": "System"},
                {"role": "user", "content": "User"},
                {"role": "assistant", "content": "Assistant"},
            ],
            capability=Capability(name="chat"),
        )
    ]
    body = response.json()
    assert body["id"].startswith("chatcmpl-")
    assert isinstance(body["created"], int)
    assert body == {
        "id": body["id"],
        "object": "chat.completion",
        "created": body["created"],
        "model": "actual-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Cluster response"},
                "finish_reason": None,
            }
        ],
    }
    assert not {"usage", "adapter", "node_id", "routing"} & body.keys()


def test_compatibility_app_keeps_default_local_app_composition() -> None:
    app = create_openai_compatibility_app()

    assert app.state.local_app_composition is None


def test_placeholder_bearer_is_accepted(
    use_cluster_result: list[ClusterRequest],
) -> None:
    response = post(
        create_openai_compatibility_app(),
        payload=compatibility_payload(),
        headers={"Authorization": "Bearer placeholder"},
    )

    assert response.status_code == 200
    assert len(use_cluster_result) == 1


@pytest.mark.parametrize("model", [None, ""])
def test_missing_or_empty_result_model_uses_endpoint_identifier(
    monkeypatch: pytest.MonkeyPatch,
    model: str | None,
) -> None:
    from home_ai_cluster.api import openai_compatibility

    async def handle(_, __) -> ClusterResult:
        return ClusterResult(
            content="Cluster response",
            adapter="test-adapter",
            model=model,
            node_id="selected-node",
        )

    monkeypatch.setattr(openai_compatibility, "handle_chat_cluster_request", handle)

    response = post(create_openai_compatibility_app(), payload=compatibility_payload())

    assert response.status_code == 200
    assert response.json()["model"] == COMPATIBILITY_MODEL


def assert_error(
    response: httpx.Response,
    *,
    status_code: int,
    message: str,
    error_type: str,
    param: str | None = None,
) -> None:
    assert response.status_code == status_code
    assert response.json() == {
        "error": {
            "message": message,
            "type": error_type,
            "param": param,
            "code": None,
        }
    }


def test_malformed_json_uses_compatibility_error_envelope() -> None:
    response = post(create_openai_compatibility_app(), content="{")

    assert_error(
        response,
        status_code=400,
        message="Invalid chat completion request",
        error_type="invalid_request_error",
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"model": COMPATIBILITY_MODEL},
        {"messages": [{"role": "user", "content": "Hello"}]},
        compatibility_payload(messages=[]),
        compatibility_payload(messages=[{"role": "user"}]),
        compatibility_payload(messages="not a list"),
    ],
)
def test_invalid_required_input_is_rejected(payload: dict[str, object]) -> None:
    response = post(create_openai_compatibility_app(), payload=payload)

    assert_error(
        response,
        status_code=400,
        message="Invalid chat completion request",
        error_type="invalid_request_error",
    )


def test_wrong_model_identifier_is_rejected() -> None:
    response = post(
        create_openai_compatibility_app(),
        payload=compatibility_payload(model="runtime-model"),
    )

    assert_error(
        response,
        status_code=400,
        message="Unsupported model identifier",
        error_type="invalid_request_error",
        param="model",
    )


def test_streaming_is_rejected_explicitly() -> None:
    response = post(
        create_openai_compatibility_app(),
        payload=compatibility_payload(stream=True),
    )

    assert_error(
        response,
        status_code=400,
        message="Streaming is not supported",
        error_type="invalid_request_error",
        param="stream",
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("temperature", 0.1),
        ("top_p", 0.9),
        ("max_tokens", 10),
        ("stop", "stop"),
        ("tools", []),
        ("tool_choice", "auto"),
        ("response_format", {"type": "json_object"}),
        ("user", "someone"),
        ("unknown", "value"),
        ("n", 2),
        ("stream", "false"),
    ],
)
def test_unsupported_top_level_values_are_rejected(field: str, value: object) -> None:
    response = post(
        create_openai_compatibility_app(),
        payload=compatibility_payload(**{field: value}),
    )

    assert_error(
        response,
        status_code=400,
        message="Unsupported chat completion request value",
        error_type="invalid_request_error",
        param=field,
    )


@pytest.mark.parametrize(
    "message",
    [
        {"role": "developer", "content": "Hello"},
        {"role": "tool", "content": "Hello"},
        {"role": "user", "content": ["not", "text"]},
        {"role": "user", "content": ""},
        {"role": "user", "content": "Hello", "tool_calls": []},
        {"role": "user", "content": "Hello", "unknown": "value"},
    ],
)
def test_unsupported_message_values_are_rejected(message: dict[str, object]) -> None:
    response = post(
        create_openai_compatibility_app(),
        payload=compatibility_payload(messages=[message]),
    )

    assert_error(
        response,
        status_code=400,
        message="Unsupported chat completion request value",
        error_type="invalid_request_error",
        param="messages",
    )


@pytest.mark.parametrize("authorization", ["Basic token", "Bearer ", ""])
def test_invalid_authorization_is_rejected(authorization: str) -> None:
    response = post(
        create_openai_compatibility_app(),
        payload=compatibility_payload(),
        headers={"Authorization": authorization},
    )

    assert_error(
        response,
        status_code=400,
        message="Invalid chat completion request",
        error_type="invalid_request_error",
        param="authorization",
    )


def test_no_matching_chat_capability_is_translated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import openai_compatibility

    async def handle(_, __) -> ClusterResult:
        raise NoMatchingAdapterError("private capability detail")

    monkeypatch.setattr(openai_compatibility, "handle_chat_cluster_request", handle)

    response = post(create_openai_compatibility_app(), payload=compatibility_payload())

    assert_error(
        response,
        status_code=503,
        message="No available chat capability",
        error_type="server_error",
    )


def test_runtime_unavailability_does_not_leak_runtime_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import openai_compatibility

    async def handle(_, __) -> ClusterResult:
        raise RuntimeAdapterUnavailableError("ollama at localhost:11434")

    monkeypatch.setattr(openai_compatibility, "handle_chat_cluster_request", handle)

    response = post(create_openai_compatibility_app(), payload=compatibility_payload())

    assert_error(
        response,
        status_code=503,
        message="Runtime adapter unavailable",
        error_type="server_error",
    )
    assert "ollama" not in response.text
    assert "localhost" not in response.text


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (404, "No available chat capability"),
        (503, "Runtime adapter unavailable"),
    ],
)
def test_cluster_seam_http_errors_are_translated_without_details(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    message: str,
) -> None:
    from home_ai_cluster.api import openai_compatibility

    async def handle(_, __) -> ClusterResult:
        raise HTTPException(status_code, detail="private runtime detail")

    monkeypatch.setattr(openai_compatibility, "handle_chat_cluster_request", handle)

    response = post(create_openai_compatibility_app(), payload=compatibility_payload())

    assert_error(
        response,
        status_code=503,
        message=message,
        error_type="server_error",
    )
    assert "private" not in response.text


def test_unexpected_failure_does_not_leak_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import openai_compatibility

    async def handle(_, __) -> ClusterResult:
        raise RuntimeError("private prompt content")

    monkeypatch.setattr(openai_compatibility, "handle_chat_cluster_request", handle)

    response = post(create_openai_compatibility_app(), payload=compatibility_payload())

    assert_error(
        response,
        status_code=500,
        message="Internal server error",
        error_type="server_error",
    )
    assert "private" not in response.text


def test_ordinary_application_does_not_expose_compatibility_route() -> None:
    response = post(create_app(), payload=compatibility_payload())

    assert response.status_code == 404


def test_compatibility_process_uses_fixed_loopback_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import openai_compatibility

    calls: list[dict[str, object]] = []

    def run(app, *, host: str, port: int) -> None:
        calls.append({"app": app, "host": host, "port": port})

    monkeypatch.setattr(openai_compatibility.uvicorn, "run", run)

    openai_compatibility.main()

    assert calls[0]["host"] == COMPATIBILITY_HOST
    assert calls[0]["host"] == "127.0.0.1"
