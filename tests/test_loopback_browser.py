import asyncio
from importlib.resources import files

import httpx
from fastapi import FastAPI

from home_ai_cluster.local_runtime_composition import create_local_runtime_composition
from home_ai_cluster.loopback_browser import add_loopback_browser_routes
from home_ai_cluster.main import app as module_level_app
from home_ai_cluster.main import create_app
from home_ai_cluster.openai_compatibility import (
    create_openai_compatibility_app,
    create_static_cluster_openai_compatibility_app,
)
from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration


def get(app: FastAPI, path: str) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as client:
            return await client.get(path)

    return asyncio.run(send())


def post_native_chat(app: FastAPI) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as client:
            return await client.post("/v1/chat", json={})

    return asyncio.run(send())


def test_api_only_applications_remain_page_free() -> None:
    static_compatibility_app = create_static_cluster_openai_compatibility_app(
        [RemoteNodeDeclaration(node_id="remote", base_url="http://remote.example")],
        local_app_composition=create_local_runtime_composition(runtime="ollama"),
    )
    for app in (
        create_app(),
        module_level_app,
        create_openai_compatibility_app(),
        static_compatibility_app,
    ):
        assert get(app, "/").status_code == 404
        assert get(app, "/assets/app.css").status_code == 404


def test_loopback_browser_routes_are_fixed_and_keep_native_routes() -> None:
    app = add_loopback_browser_routes(create_app())

    page = get(app, "/")
    stylesheet = get(app, "/assets/app.css")
    script = get(app, "/assets/app.js")

    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert page.headers["cache-control"] == "no-store"
    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")
    assert script.status_code == 200
    assert script.headers["content-type"].startswith("application/javascript")
    assert get(app, "/unknown-page").status_code == 404
    assert get(app, "/assets/").status_code == 404
    assert get(app, "/assets/unknown.css").status_code == 404
    assert get(app, "/assets/%2e%2e/main.py").status_code == 404
    assert post_native_chat(app).status_code == 422


def test_packaged_browser_assets_reference_only_fixed_local_assets() -> None:
    web = files("home_ai_cluster").joinpath("web")
    html = web.joinpath("index.html").read_text(encoding="utf-8")
    script = web.joinpath("assets", "app.js").read_text(encoding="utf-8")

    assert 'href="/assets/app.css"' in html
    assert 'src="/assets/app.js"' in html
    assert "http://" not in html
    assert "https://" not in html
    assert 'post("/v1/chat"' in script
    assert 'post("/v1/summarize"' in script
    assert 'post("/v1/classify"' in script
    assert "`${message.role}: ${message.content}`" not in script
    assert "message message-${message.role}" in script
    assert 'message.role === "user" ? "You" : "Home AI Cluster"' in script
    assert ".message-user" in web.joinpath("assets", "app.css").read_text(
        encoding="utf-8"
    )
    assert ".message-assistant" in web.joinpath("assets", "app.css").read_text(
        encoding="utf-8"
    )
    assert "const assistantAttribution = new WeakMap()" in script
    assert "assistantAttribution.set(assistantMessage, result.node_id)" in script
    assert 'post("/v1/chat", { capability: "chat", messages }, "Sending…")' in script
    assert 'post("/v1/summarize", { text }, "Summarizing…")' in script
    assert 'post("/v1/classify", { text, labels }, "Classifying…")' in script
    assert 'status.textContent = active ? message : ""' in script
    assert "finally {\n      setRequestActive(false);" in script
    assert "function rollbackPendingMessage(pendingMessage)" in script
    assert "rollbackPendingMessage(pendingMessage);" in script
    assert "messages.splice(pendingIndex, 1)" in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "indexedDB" not in script
    assert (
        'aria-live="polite" class="request-status" id="request-status" role="status"'
        in html
    )
    assert "@media (prefers-reduced-motion: reduce)" in web.joinpath(
        "assets", "app.css"
    ).read_text(encoding="utf-8")
    assert ".conversation:empty { display: none; }" in web.joinpath(
        "assets", "app.css"
    ).read_text(encoding="utf-8")
    classify_section = html.split('id="classify-view"', 1)[1].split("</section>", 1)[0]
    assert 'type="file"' not in classify_section
