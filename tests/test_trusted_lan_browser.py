import asyncio
from importlib.resources import files

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
    routes = {route.path: set(route.methods or ()) for route in app.routes}

    assert routes == {
        "/": {"GET"},
        "/assets/lan.css": {"GET"},
        "/assets/lan.js": {"GET"},
        "/v1/chat": {"POST"},
        "/v1/summarize": {"POST"},
        "/v1/classify": {"POST"},
        "/v1/image-generation": {"POST"},
    }
    assert request(app, "GET", "/").status_code == 400
    headers = {"host": "192.0.2.10:25042"}
    assert request(app, "GET", "/", headers=headers).status_code == 200
    for path in (
        "/workspace-code",
        "/retained-local-configuration",
        "/retained-remote-nodes",
        "/retained-image-generation-configuration",
        "/retained-external-information-configuration",
        "/retained-chat-external-information-configuration",
        "/v1/chat/sources",
        "/internal/chat/external-information-decision",
        "/internal/cluster/request",
        "/internal/cluster/status",
        "/docs",
        "/redoc",
        "/openapi.json",
    ):
        assert request(app, "GET", path, headers=headers).status_code == 404
    assert request(app, "GET", "/assets/lan.css", headers=headers).status_code == 200
    assert request(app, "GET", "/assets/lan.js", headers=headers).status_code == 200
    assert request(app, "GET", "/assets/lan.css").status_code == 400


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


def test_lan_browser_assets_keep_current_page_state_and_full_request_gate():
    web = files("home_ai_cluster").joinpath("web")
    html = web.joinpath("lan.html").read_text(encoding="utf-8")
    css = web.joinpath("assets", "lan.css").read_text(encoding="utf-8")
    script = web.joinpath("assets", "lan.js").read_text(encoding="utf-8")

    assert "const conversations = { chat: [], code: [] };" in script
    assert "let capabilityRequestActive = false;" in script
    assert "capabilityRequestActive = true;" in script
    assert 'document.querySelectorAll("[data-submit]")' in script
    assert "ArrowRight" in script
    assert "ArrowLeft" in script
    assert 'event.key === "Home"' in script
    assert 'event.key === "End"' in script
    assert script.index("currentImageUrl = URL.createObjectURL") < script.index(
        "finally { setActive(context, false); }"
    )
    assert "URL.revokeObjectURL(currentImageUrl)" in script
    assert 'const themeKey = "home-ai-cluster.theme";' in script
    assert 'id="theme-select"' in html
    assert '<option value="system">System</option>' in html
    assert '<option value="light">Light</option>' in html
    assert '<option value="dark">Dark</option>' in html
    assert "localStorage.getItem(themeKey)" in script
    assert "localStorage.setItem(themeKey, theme)" in script
    assert "sessionStorage" not in script
    assert "IndexedDB" not in script
    assert "Configuration" not in html
    assert "workspace" not in html.lower()
    assert "External Information" not in html
    assert html.count('role="tab"') == 5
    assert html.count('role="tabpanel"') == 5
    assert [
        button.split("</button>", 1)[0].rsplit(">", 1)[1]
        for button in html.split('role="tab"')[1:]
    ] == ["Chat", "Code", "Image", "Summarize", "Classify"]
    assert 'aria-selected="true" id="chat-tab"' in html
    assert 'id="result"' not in html
    assert 'id="chat-conversation"' in html
    assert 'id="code-conversation"' in html
    assert 'hidden id="chat-result-region"' in html
    assert 'hidden id="code-result-region"' in html
    assert "result-region`).hidden = conversations[capability].length === 0" in script
    assert 'id="chat-status"' in html
    assert 'id="code-status"' in html
    chat_conversation = html.split('id="chat-conversation"', 1)[1].split("</div>", 1)[0]
    code_conversation = html.split('id="code-conversation"', 1)[1].split("</div>", 1)[0]
    assert 'id="chat-status"' in chat_conversation
    assert 'id="code-status"' in code_conversation
    assert html.count('id="chat-status"') == 1
    assert html.count('id="code-status"') == 1
    assert "max-height: min(50vh, 32rem);" not in css
    assert ".conversation { overflow-y: auto;" not in css
    assert ".conversation:empty" not in css
    assert css.count("\n") > 50
    assert ".conversation, .result {" in css
    render_conversation = script.split("function renderConversation(capability)", 1)[
        1
    ].split('document.querySelectorAll("form")', 1)[0]
    assert (
        "const status = document.querySelector(`#${capability}-status`);"
        in render_conversation
    )
    assert "container.replaceChildren();" in render_conversation
    assert "container.append(status);" in render_conversation
    assert render_conversation.index(
        "container.replaceChildren();"
    ) < render_conversation.index("container.append(status);")
    assert "Local AI, simply connected" in html
    assert "header-tools" in html
    assert "Capability-only · Trusted network required" in html
    assert "radial-gradient(circle at 94% 0" in css
    assert ".tabs { display: flex; flex-wrap: wrap;" in css
    assert "justify-content: flex-end" in css
    assert "prefers-color-scheme: dark" in css
    assert "prefers-reduced-motion: reduce" in css
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in css
    assert "selected_label" in script
    assert 'id="image-generation-width"' in html
    assert 'id="image-generation-height"' in html
    assert '(width === "") !== (height === "")' in script
    assert "body.width = numericWidth; body.height = numericHeight;" in script
    assert (
        'Array.from(document.querySelectorAll(".classify-label"), '
        "(input) => input.value)" in script
    )
    assert ".split(" not in script
    assert ".trim(" not in script
    assert ".filter(" not in script
    assert 'href="/assets/lan.css"' in html
    assert 'src="/assets/lan.js"' in html
    assert "app.css" not in html
    assert "app.js" not in html


def test_trusted_lan_authority_canonicalizes_ipv6_and_http_default_port():
    owner = create_app(
        local_app_composition=create_local_runtime_composition(runtime="ollama")
    )
    app = create_trusted_lan_browser_app(owner, host="2001:db8::10", port=80)
    headers = {"host": "[2001:db8::10]", "origin": "http://[2001:db8::10]"}

    assert app.state.trusted_lan_authority == "[2001:db8::10]"
    assert request(app, "GET", "/", headers=headers).status_code == 200
    assert (
        request(app, "GET", "/", headers={"host": "[2001:db8::10]:80"}).status_code
        == 400
    )
