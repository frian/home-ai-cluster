"""Focused RFC-0124 proof for the browser-only workspace Code facade."""

import asyncio
import json

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from starlette.requests import Request

from home_ai_cluster.core.models import ClusterResult
from home_ai_cluster.main import create_app, create_receiver_app
from home_ai_cluster.web import loopback_browser
from home_ai_cluster.web.loopback_browser import add_loopback_browser_routes


class State:
    def __init__(self, body: object) -> None:
        self.body = json.dumps(body).encode()
        self.consumed = False
        self.disconnected = False

    async def receive(self) -> dict[str, object]:
        if not self.consumed:
            self.consumed = True
            return {"type": "http.request", "body": self.body, "more_body": False}
        if self.disconnected:
            return {"type": "http.disconnect"}
        return {"type": "http.request", "body": b"", "more_body": False}


def endpoint(app):
    return next(
        route.endpoint
        for route in app.routes
        if isinstance(route, APIRoute) and route.path == "/workspace-code"
    )


def request(app, state: State, headers: dict[str, str] | None = None) -> Request:
    values = {
        "host": "127.0.0.1:25042",
        "origin": "http://127.0.0.1:25042",
        "content-type": "application/json",
        **(headers or {}),
    }
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/workspace-code",
            "headers": [
                (key.encode(), value.encode()) for key, value in values.items()
            ],
            "server": ("127.0.0.1", 25042),
            "app": app,
        },
        receive=state.receive,
    )


def payload(root: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "root": root,
        "grants": ["list", "read", "write", "create"],
        "history": [],
        "instruction": "update the workspace",
    }
    value.update(overrides)
    return value


def test_workspace_route_is_browser_only(tmp_path) -> None:
    with pytest.raises(StopIteration):
        endpoint(create_app())
    with pytest.raises(StopIteration):
        endpoint(create_receiver_app(local_app_composition=object()))
    assert endpoint(add_loopback_browser_routes(create_app()))


def test_workspace_route_executes_all_actions_with_bounded_ordered_activity(
    monkeypatch, tmp_path
) -> None:
    (tmp_path / "source.txt").write_text("before", encoding="utf-8")
    responses = iter(
        [
            '{"kind":"workspace","operation":"list","path":"."}',
            '{"kind":"workspace","operation":"read","path":"source.txt"}',
            '{"kind":"workspace","operation":"write","path":"source.txt","content":"after"}',
            '{"kind":"workspace","operation":"create","path":"new.txt"}',
            '{"kind":"final","content":"done"}',
        ]
    )
    contexts = []
    requests = []

    async def infer(cluster_request, *_):
        requests.append(cluster_request)
        contexts.append(cluster_request.messages)
        return ClusterResult(content=next(responses), adapter="test", node_id="node")

    monkeypatch.setattr(loopback_browser, "handle_chat_cluster_request", infer)
    app = add_loopback_browser_routes(create_app())

    result = asyncio.run(endpoint(app)(request(app, State(payload(str(tmp_path))))))

    assert result.body
    assert json.loads(result.body) == {
        "content": "done",
        "node_id": "node",
        "activity": [
            {"operation": "list", "path": ".", "outcome": "success"},
            {"operation": "read", "path": "source.txt", "outcome": "success"},
            {"operation": "write", "path": "source.txt", "outcome": "success"},
            {"operation": "create", "path": "new.txt", "outcome": "success"},
        ],
    }
    assert (tmp_path / "source.txt").read_text(encoding="utf-8") == "after"
    assert (tmp_path / "new.txt").exists()
    assert all(item.capability.name == "code" for item in requests)
    assert str(tmp_path) not in "\n".join(message.content for message in contexts[0])


@pytest.mark.parametrize(
    ("document", "headers"),
    [
        (lambda root: payload(root, grants=[]), {}),
        (lambda root: payload(root, grants=["read", "read"]), {}),
        (lambda root: payload(root, grants=["unknown"]), {}),
        (
            lambda root: payload(
                root, history=[{"role": "assistant", "content": "no"}]
            ),
            {},
        ),
        (lambda root: payload(root, history=[{"role": "user", "content": "one"}]), {}),
        (lambda root: {**payload(root), "extra": True}, {}),
        (lambda root: payload(root), {"host": "foreign.example"}),
        (lambda root: payload(root), {"origin": ""}),
        (lambda root: payload(root), {"origin": "null"}),
        (lambda root: payload(root), {"origin": "http://foreign.example"}),
        (lambda root: payload(root), {"content-type": "text/plain"}),
    ],
)
def test_workspace_route_rejects_invalid_requests_before_inference(
    monkeypatch, tmp_path, document, headers
) -> None:
    calls = 0

    async def infer(*_):
        nonlocal calls
        calls += 1
        raise AssertionError("inference must not run")

    monkeypatch.setattr(loopback_browser, "handle_chat_cluster_request", infer)
    app = add_loopback_browser_routes(create_app())
    with pytest.raises(HTTPException) as raised:
        asyncio.run(
            endpoint(app)(request(app, State(document(str(tmp_path))), headers))
        )
    assert raised.value.status_code in {400, 403, 415}
    assert calls == 0


def test_workspace_route_rejects_malformed_json_and_invalid_root_before_inference(
    monkeypatch, tmp_path
) -> None:
    async def infer(*_):
        raise AssertionError("inference must not run")

    monkeypatch.setattr(loopback_browser, "handle_chat_cluster_request", infer)
    app = add_loopback_browser_routes(create_app())
    malformed = State({})
    malformed.body = b"{"
    with pytest.raises(HTTPException) as malformed_error:
        asyncio.run(endpoint(app)(request(app, malformed)))
    assert malformed_error.value.status_code == 400
    with pytest.raises(HTTPException) as root_error:
        asyncio.run(
            endpoint(app)(request(app, State(payload(str(tmp_path / "missing")))))
        )
    assert root_error.value.status_code == 400


def test_empty_final_keeps_committed_write_and_returns_activity(
    monkeypatch, tmp_path
) -> None:
    target = tmp_path / "target.txt"
    target.write_text("before", encoding="utf-8")
    responses = iter(
        [
            '{"kind":"workspace","operation":"write","path":"target.txt","content":"after"}',
            '{"kind":"final","content":""}',
        ]
    )

    async def infer(*_):
        return ClusterResult(content=next(responses), adapter="test", node_id="node")

    monkeypatch.setattr(loopback_browser, "handle_chat_cluster_request", infer)
    app = add_loopback_browser_routes(create_app())
    result = asyncio.run(endpoint(app)(request(app, State(payload(str(tmp_path))))))

    assert json.loads(result.body) == {
        "status": "final",
        "activity": [
            {"operation": "write", "path": "target.txt", "outcome": "success"}
        ],
    }
    assert target.read_text(encoding="utf-8") == "after"


def test_initial_context_overflow_runs_no_inference_or_action(
    monkeypatch, tmp_path
) -> None:
    calls = 0

    async def infer(*_):
        nonlocal calls
        calls += 1
        raise AssertionError("inference must not run")

    monkeypatch.setattr(loopback_browser, "handle_chat_cluster_request", infer)
    app = add_loopback_browser_routes(create_app())
    with pytest.raises(HTTPException) as raised:
        asyncio.run(
            endpoint(app)(
                request(app, State(payload(str(tmp_path), instruction="x" * 65_537)))
            )
        )
    assert raised.value.status_code == 400
    assert calls == 0
