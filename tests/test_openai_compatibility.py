import asyncio
import socket
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, HTTPException

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api.openai_compatibility import COMPATIBILITY_MODEL
from home_ai_cluster.core.models import Capability, ClusterRequest, ClusterResult
from home_ai_cluster.core.router import NoMatchingAdapterError
from home_ai_cluster.local_runtime_composition import create_local_runtime_composition
from home_ai_cluster.main import create_app
from home_ai_cluster.openai_compatibility import (
    COMPATIBILITY_HOST,
    COMPATIBILITY_PORT,
    create_openai_compatibility_app,
    create_static_cluster_openai_compatibility_app,
    main,
    parse_args,
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


def test_parse_args_accepts_only_the_optional_declaration() -> None:
    assert parse_args([]).declaration is None
    assert parse_args(["--declaration", "cluster.toml"]).declaration == Path(
        "cluster.toml"
    )


def test_main_keeps_no_argument_compatibility_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import openai_compatibility

    app = FastAPI()
    calls: list[str] = []

    monkeypatch.setattr(
        openai_compatibility,
        "create_openai_compatibility_app",
        lambda: calls.append("local") or app,
    )
    monkeypatch.setattr(
        openai_compatibility,
        "load_static_cluster_declarations",
        lambda _: pytest.fail("local mode must not load a declaration"),
    )
    monkeypatch.setattr(
        openai_compatibility.uvicorn,
        "run",
        lambda actual_app, *, host, port: calls.extend(
            ["server", str(actual_app is app), host, str(port)]
        ),
    )

    main([])

    assert calls == [
        "local",
        "server",
        "True",
        COMPATIBILITY_HOST,
        str(COMPATIBILITY_PORT),
    ]


def test_main_loads_declaration_before_static_compatibility_startup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import openai_compatibility

    declaration_path = tmp_path / "cluster.toml"
    declaration_path.write_text(
        '[[remote_nodes]]\nnode_id = "remote-a"\n'
        'base_url = "https://remote-a.example:8000/"\n'
        '[[remote_nodes]]\nnode_id = "remote-b"\n'
        'base_url = "https://remote-b.example:8000"\n',
        encoding="utf-8",
    )
    app = FastAPI()
    recorded: dict[str, object] = {}
    composition = create_local_runtime_composition(runtime="ollama")

    def fail_network(*_: object, **__: object) -> None:
        pytest.fail("declaration loading must not use the network")

    monkeypatch.setattr(socket, "getaddrinfo", fail_network)
    monkeypatch.setattr(socket, "create_connection", fail_network)

    def create_local_composition(*, runtime: str) -> object:
        recorded["runtime"] = runtime
        return composition

    monkeypatch.setattr(
        openai_compatibility,
        "create_local_runtime_composition",
        create_local_composition,
    )
    monkeypatch.setattr(
        openai_compatibility,
        "create_static_cluster_openai_compatibility_app",
        lambda remote_nodes, *, local_app_composition: (
            recorded.update(
                remote_nodes=remote_nodes,
                local_app_composition=local_app_composition,
            )
            or app
        ),
    )
    monkeypatch.setattr(
        openai_compatibility.uvicorn,
        "run",
        lambda actual_app, *, host, port: recorded.update(
            app=actual_app,
            host=host,
            port=port,
        ),
    )

    main(["--declaration", str(declaration_path)])

    assert recorded["runtime"] == "ollama"
    remote_nodes = recorded["remote_nodes"]
    assert [(remote.node_id, remote.base_url) for remote in remote_nodes] == [
        ("remote-a", "https://remote-a.example:8000"),
        ("remote-b", "https://remote-b.example:8000"),
    ]
    assert recorded["local_app_composition"] is composition
    assert recorded["app"] is app
    assert recorded["host"] == COMPATIBILITY_HOST
    assert recorded["port"] == COMPATIBILITY_PORT


def test_invalid_declaration_stops_before_listener_startup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster import openai_compatibility

    declaration_path = tmp_path / "cluster.toml"
    private_host = "private.example:9443"
    declaration_path.write_text(
        f'remote_node_id = "remote"\nremote_base_url = "{private_host}"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        openai_compatibility.uvicorn,
        "run",
        lambda *_args, **_kwargs: pytest.fail("listener must not start"),
    )

    with pytest.raises(SystemExit):
        main(["--declaration", str(declaration_path)])

    captured = capsys.readouterr().err
    assert "invalid remote base URL declaration" in captured
    assert private_host not in captured


def test_static_compatibility_route_uses_existing_collection_wiring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import openai_compatibility
    from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration

    app = create_static_cluster_openai_compatibility_app(
        [
            RemoteNodeDeclaration(
                node_id="remote",
                base_url="https://remote.example:8000",
            )
        ],
        local_app_composition=create_local_runtime_composition(runtime="ollama"),
    )
    collections: list[object] = []

    async def handle(
        request: ClusterRequest,
        _,
        *,
        static_remote_wiring: object,
        static_remote_collection_wiring: object,
        local_app_composition: object,
    ) -> ClusterResult:
        assert request.capability == Capability(name="chat")
        assert static_remote_wiring is None
        assert local_app_composition is None
        collections.append(static_remote_collection_wiring)
        return ClusterResult(
            content="Cluster response",
            adapter="test-adapter",
            model="actual-model",
            node_id="remote",
        )

    monkeypatch.setattr(openai_compatibility, "handle_chat_cluster_request", handle)

    response = post(app, payload=compatibility_payload())

    assert response.status_code == 200
    assert collections == [app.state.static_remote_collection_wiring]
    remote_registry = app.state.static_remote_collection_wiring.remote_registry
    assert remote_registry.list_declarations()[0].node.id == "remote"
    asyncio.run(app.state.static_cluster_http_client.aclose())


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

    openai_compatibility.main([])

    assert calls[0]["host"] == COMPATIBILITY_HOST
    assert calls[0]["host"] == "127.0.0.1"
