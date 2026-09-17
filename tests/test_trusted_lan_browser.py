import asyncio

import httpx

from home_ai_cluster.local_runtime_composition import create_local_runtime_composition
from home_ai_cluster.main import create_app
from home_ai_cluster.web.trusted_lan_browser import create_trusted_lan_browser_app


def request(app, method, path, *, headers=None, json=None):
    async def send():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as client:
            return await client.request(method, path, headers=headers, json=json)

    return asyncio.run(send())


def test_trusted_lan_browser_has_only_closed_routes_and_requires_host():
    owner = create_app(
        local_app_composition=create_local_runtime_composition(runtime="ollama")
    )
    app = create_trusted_lan_browser_app(owner, host="192.0.2.10", port=25042)
    routes = {route.path for route in app.routes}

    assert routes == {
        "/",
        "/assets/lan.css",
        "/assets/lan.js",
        "/assets/pdfjs-6.2.108/pdf.min.mjs",
        "/assets/pdfjs-6.2.108/pdf.worker.min.mjs",
        "/v1/chat",
        "/v1/summarize",
        "/v1/classify",
        "/v1/image-generation",
    }
    assert request(app, "GET", "/").status_code == 400
    headers = {"host": "192.0.2.10:25042"}
    assert request(app, "GET", "/", headers=headers).status_code == 200
    assert request(app, "GET", "/workspace-code", headers=headers).status_code == 404
    assert request(app, "GET", "/docs", headers=headers).status_code == 404


def test_trusted_lan_chat_rejects_non_chat_or_code_before_execution():
    owner = create_app(
        local_app_composition=create_local_runtime_composition(runtime="ollama")
    )
    app = create_trusted_lan_browser_app(owner, host="192.0.2.10", port=25042)
    headers = {
        "host": "192.0.2.10:25042",
        "origin": "http://192.0.2.10:25042",
        "content-type": "application/json",
    }
    response = request(
        app,
        "POST",
        "/v1/chat",
        headers=headers,
        json={
            "messages": [{"role": "user", "content": "hello"}],
            "capability": "summarize",
        },
    )
    assert response.status_code == 422
    assert (
        request(
            app, "POST", "/v1/chat", headers={"host": "192.0.2.10:25042"}, json={}
        ).status_code
        == 403
    )
