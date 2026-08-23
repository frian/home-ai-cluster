import asyncio
from hashlib import sha256
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
        assert get(app, "/assets/pdfjs-6.2.108/pdf.min.mjs").status_code == 404


def test_loopback_browser_routes_are_fixed_and_keep_native_routes() -> None:
    app = add_loopback_browser_routes(create_app())

    page = get(app, "/")
    stylesheet = get(app, "/assets/app.css")
    script = get(app, "/assets/app.js")
    pdfjs_main = get(app, "/assets/pdfjs-6.2.108/pdf.min.mjs")
    pdfjs_worker = get(app, "/assets/pdfjs-6.2.108/pdf.worker.min.mjs")

    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert page.headers["cache-control"] == "no-store"
    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")
    assert script.status_code == 200
    assert script.headers["content-type"].startswith("application/javascript")
    assert pdfjs_main.status_code == 200
    assert pdfjs_main.headers["content-type"].startswith("application/javascript")
    assert pdfjs_worker.status_code == 200
    assert pdfjs_worker.headers["content-type"].startswith("application/javascript")
    assert get(app, "/unknown-page").status_code == 404
    assert get(app, "/assets/").status_code == 404
    assert get(app, "/assets/unknown.css").status_code == 404
    assert get(app, "/assets/%2e%2e/main.py").status_code == 404
    assert get(app, "/v1/code").status_code == 404
    assert post_native_chat(app).status_code == 422


def test_packaged_browser_assets_reference_only_fixed_local_assets() -> None:
    web = files("home_ai_cluster").joinpath("web")
    html = web.joinpath("index.html").read_text(encoding="utf-8")
    stylesheet = web.joinpath("assets", "app.css").read_text(encoding="utf-8")
    script = web.joinpath("assets", "app.js").read_text(encoding="utf-8")
    pdfjs_assets = web.joinpath("assets", "pdfjs-6.2.108")

    assert 'href="/assets/app.css"' in html
    assert 'src="/assets/app.js"' in html
    assert "http://" not in html
    assert "https://" not in html
    assert "http://" not in script
    assert "https://" not in script
    assert '"/v1/chat"' in script
    assert 'post("/v1/summarize"' in script
    assert 'post("/v1/classify"' in script
    assert 'accept="application/pdf,.pdf" id="summarize-pdf" type="file"' in html
    assert "const pdfByteLimit = 8388608;" in script
    assert 'const pdfjsMainUrl = "/assets/pdfjs-6.2.108/pdf.min.mjs";' in script
    assert (
        'const pdfjsWorkerUrl = "/assets/pdfjs-6.2.108/pdf.worker.min.mjs";' in script
    )
    assert "PDF.js 6.2.108: matched vendored main/worker assets." in script
    assert "if (file.size > pdfByteLimit)" in script
    assert "new Uint8Array(await file.arrayBuffer())" in script
    assert "pdfjs.GlobalWorkerOptions.workerSrc = pdfjsWorkerUrl" in script
    read_pdf_text = script.split("async function readPdfText(file)", 1)[1].split(
        'document.querySelector("#summarize-pdf").addEventListener(', 1
    )[0]
    assert "let loadingTask;" in read_pdf_text
    assert "loadingTask = pdfjs.getDocument({ data: bytes });" in read_pdf_text
    assert "new pdfjs.PDFWorker" not in read_pdf_text
    assert "documentProxy.destroy" not in read_pdf_text
    assert "worker.destroy" not in read_pdf_text
    assert "await loadingTask.destroy();" in read_pdf_text
    assert (
        read_pdf_text.index("loadingTask = pdfjs.getDocument")
        < read_pdf_text.index("await loadingTask.promise")
        < read_pdf_text.index("finally {")
        < read_pdf_text.index("await loadingTask.destroy();")
    )
    assert 'post("/v1/summarize", { text }, "Summarizing…")' in script
    assert 'document.querySelector("#summarize-pdf")' in script
    assert 'document.querySelector("#classify-pdf")' not in script
    assert 'document.querySelector("#chat-pdf")' not in script
    assert "Selected PDF must be at most 8 MiB" in script
    assert "Selected PDF is password-protected" in script
    assert "Selected PDF contains no extractable text" in script
    assert "Selected PDF could not be read" in script
    assert ".name" not in script
    pdf_handler = script.split(
        'document.querySelector("#summarize-pdf").addEventListener(', 1
    )[1].split('document.querySelector("#summarize-form")', 1)[0]
    assert "post(" not in pdf_handler
    assert pdf_handler.index("if (file.size > pdfByteLimit)") < pdf_handler.index(
        "await readPdfText(file)"
    )
    assert 'document.querySelector("#summarize-text")' in pdf_handler
    summarize_file_handler = script.split(
        'document.querySelector("#summarize-file").addEventListener(', 1
    )[1].split("function extractedPdfText", 1)[0]
    assert 'new TextDecoder("utf-8", { fatal: true })' in summarize_file_handler
    assert (
        'document.querySelector("#summarize-text").value = text;'
        in summarize_file_handler
    )
    assert {asset.name for asset in pdfjs_assets.iterdir()} == {
        "pdf.min.mjs",
        "pdf.worker.min.mjs",
    }
    assert sha256(pdfjs_assets.joinpath("pdf.min.mjs").read_bytes()).hexdigest() == (
        "e0be3863c23c8af2305b16548febd58e7f8874a460253317d7771cddbc1c0f6d"
    )
    worker_hash = sha256(pdfjs_assets.joinpath("pdf.worker.min.mjs").read_bytes())
    assert worker_hash.hexdigest() == (
        "0613f41490dd6aaceed7a93fbbd38c85e6d6aa60474b6588c6e7709cfbe18cb3"
    )
    assert "`${message.role}: ${message.content}`" not in script
    assert "message message-${message.role}" in script
    assert 'message.role === "user" ? "You" : "Home AI Cluster"' in script
    assert ".message-user" in stylesheet
    assert ".message-assistant" in stylesheet
    assert "const assistantAttribution = new WeakMap()" in script
    assert "assistantAttribution.set(assistantMessage, result.node_id)" in script
    chat_view = html.split('id="chat-view"', 1)[1].split('id="summarize-view"', 1)[0]
    assert chat_view.index('id="chat-result-region"') < chat_view.index(
        'id="chat-form"'
    )
    assert (
        ".conversation { max-height: min(50vh, 32rem); overflow-y: auto; }"
        in stylesheet
    )
    render_chat = script.split("function renderChat()", 1)[1].split(
        "function rollbackPendingMessage", 1
    )[0]
    assert "container.scrollTop = container.scrollHeight;" in render_chat
    assert "focus(" not in render_chat
    assert "scrollIntoView" not in render_chat
    assert "window.scroll" not in render_chat
    assert 'post("/v1/summarize", { text }, "Summarizing…")' in script
    assert 'post("/v1/classify", { text, labels }, "Classifying…")' in script
    assert 'status.textContent = active ? message : ""' in script
    assert "finally {\n      setRequestActive(false);" in script
    assert "function rollbackPendingMessage(pendingMessage)" in script
    assert "rollbackPendingMessage(pendingMessage);" in script
    assert "messages.splice(pendingIndex, 1)" in script
    chat_handler = script.split(
        'document.querySelector("#chat-form").addEventListener('
        '"submit", async (event) => {',
        1,
    )[1].split('document.querySelector("#summarize-file")', 1)[0]
    pending_message = 'const pendingMessage = { role: "user", content: input.value };'
    assert pending_message in chat_handler
    assert "messages.push(pendingMessage);" in chat_handler
    assert (
        'renderChat();\n    input.value = "";\n    const request = post('
        in chat_handler
    )
    assert chat_handler.index(pending_message) < chat_handler.index(
        "messages.push(pendingMessage);"
    )
    assert (
        chat_handler.index("messages.push(pendingMessage);")
        < chat_handler.index('input.value = "";')
        < chat_handler.index("const request = post(")
        < chat_handler.index('status.scrollIntoView({ block: "nearest" });')
        < chat_handler.index("const result = await request;")
    )
    assert '"Generating response…"' in chat_handler
    assert 'behavior: "smooth"' not in chat_handler
    set_request_active = script.split("function setRequestActive", 1)[1].split(
        "function clearError", 1
    )[0]
    assert 'status.textContent = active ? message : "";' in set_request_active
    post_handler = script.split("async function post(", 1)[1].split(
        "function renderChat()", 1
    )[0]
    assert post_handler.index(
        "setRequestActive(true, activeMessage);"
    ) < post_handler.index("await fetch(")
    success_handler = chat_handler.split(
        'if (result && typeof result.content === "string"', 1
    )[1].split("    } else {", 1)[0]
    assert "input.value =" not in success_handler
    failure_handler = chat_handler.split("    } else {\n", 1)[1]
    assert "rollbackPendingMessage(pendingMessage);" in failure_handler
    assert (
        'if (input.value === "") input.value = pendingMessage.content;'
        in failure_handler
    )
    assert "sessionStorage" not in script
    assert "indexedDB" not in script
    assert "matchMedia" not in script
    assert "FormData" not in script
    assert "multipart/form-data" not in script
    assert ".name" not in script
    assert (
        'aria-live="polite" class="request-status" id="request-status" role="status"'
        in html
    )
    assert "@media (prefers-reduced-motion: reduce)" in stylesheet
    assert "color-scheme: light dark;" in stylesheet
    assert "@media (prefers-color-scheme: dark)" in stylesheet
    assert ":root:not([data-theme])" in stylesheet
    dark_mode = stylesheet.split("@media (prefers-color-scheme: dark)", 1)[1]
    assert "--page-background:" in dark_mode
    assert "--surface-background:" in dark_mode
    assert "--text-primary:" in dark_mode
    assert "--focus-color:" in dark_mode
    assert "--disabled-background:" in stylesheet
    assert "--disabled-text:" in stylesheet
    assert 'input[type="file"]::file-selector-button' in stylesheet
    assert "@media (max-width: 40rem)" in stylesheet
    assert 'tabindex="0"' in html
    assert html.count('tabindex="-1"') == 3
    assert "function activateTab(tab, focus = false)" in script
    assert 'event.key === "ArrowRight"' in script
    assert 'event.key === "ArrowLeft"' in script
    assert 'event.key === "Home"' in script
    assert 'event.key === "End"' in script
    assert "other.tabIndex = selected ? 0 : -1;" in script
    assert "function updateLabelAccessibleNames()" in script
    assert "Classification label ${labelNumber}" in script
    assert "Remove classification label ${labelNumber}" in script
    for heading in ("Chat", "Summarize", "Classify", "Code"):
        assert f">{heading}</h2>" in html
    for heading in ("Response", "Summary", "Classification", "Generated code"):
        assert f">{heading}</h3>" in html
    assert ".conversation:empty { display: none; }" in stylesheet
    assert "[hidden] { display: none !important; }" in stylesheet
    assert 'class="result-section" hidden id="chat-result-region"' in html
    assert '<output class="result" hidden id="summarize-result"></output>' in html
    assert '<output class="result" hidden id="classify-result"></output>' in html
    render_result = script.split("function renderResult", 1)[1].split(
        'document.querySelector("#chat-form")', 1
    )[0]
    assert "container.hidden = false;" in render_result
    assert "container.replaceChildren();" in render_result
    assert render_result.index("container.hidden = false;") < render_result.index(
        "container.append(value, attribution);"
    )
    classify_section = html.split('id="classify-view"', 1)[1].split("</section>", 1)[0]
    assert 'for="classify-file"' in classify_section
    assert 'accept="text/plain,.txt" id="classify-file" type="file"' in classify_section
    assert classify_section.count('type="file"') == 1
    assert "multiple" not in classify_section

    classify_file_handler = script.split(
        'document.querySelector("#classify-file").addEventListener('
        '"change", async (event) => {',
        1,
    )[1].split('document.querySelector("#classify-form")', 1)[0]
    assert "const [file] = event.target.files;" in classify_file_handler
    assert "if (!file) return;" in classify_file_handler
    assert 'new TextDecoder("utf-8", { fatal: true })' in classify_file_handler
    assert (
        'document.querySelector("#classify-text").value = text;'
        in classify_file_handler
    )
    assert 'showError("Selected file is not valid UTF-8 text")' in classify_file_handler
    assert 'const text = document.querySelector("#classify-text").value;' in script
    assert 'post("/v1/classify", { text, labels }, "Classifying…")' in script
    assert (
        'Array.from(document.querySelectorAll(".classify-label"), '
        "(input) => input.value)" in script
    )


def test_code_view_is_fixed_text_only_and_uses_native_code_request() -> None:
    web = files("home_ai_cluster").joinpath("web")
    html = web.joinpath("index.html").read_text(encoding="utf-8")
    stylesheet = web.joinpath("assets", "app.css").read_text(encoding="utf-8")
    script = web.joinpath("assets", "app.js").read_text(encoding="utf-8")

    assert html.count('role="tab"') == 4
    assert html.count('role="tabpanel"') == 4
    assert 'aria-controls="code-view"' in html
    assert 'id="code-tab"' in html
    assert 'id="code-view" role="tabpanel"' in html
    code_view = html.split('id="code-view"', 1)[1].split('id="request-error"', 1)[0]
    code_section = code_view
    assert code_view.index('id="code-result-region"') < code_view.index(
        'id="code-form"'
    )
    assert 'id="code-form"' in code_section
    assert 'for="code-text"' in code_section
    assert 'id="code-text"' in code_section
    assert code_section.count("<textarea") == 1
    assert 'data-submit type="submit"' in code_section
    assert 'aria-live="polite" class="conversation" id="code-conversation"' in code_view
    assert 'type="file"' not in code_section
    assert (
        ".conversation { max-height: min(50vh, 32rem); overflow-y: auto; }"
        in stylesheet
    )

    code_handler = script.split(
        'document.querySelector("#code-form").addEventListener('
        '"submit", async (event) => {',
        1,
    )[1].split('document.querySelector("#summarize-file")', 1)[0]
    assert "const codeMessages = [];" in script
    assert 'const input = document.querySelector("#code-text");' in code_handler
    assert (
        'const pendingMessage = { role: "user", content: input.value };' in code_handler
    )
    assert (
        "const candidateMessages = [...codeMessages, pendingMessage];" in code_handler
    )
    assert "new TextEncoder().encode(message.content).length" in code_handler
    assert "!input.value.trim() || candidateBytes > byteLimit" in code_handler
    assert (
        'showError("Code conversation must be non-blank and within the accepted limit")'
        in code_handler
    )
    assert '"/v1/chat"' in code_handler
    assert '{ capability: "code", messages: codeMessages }' in code_handler
    assert "codeMessages.push(pendingMessage);" in code_handler
    assert "codeMessages.push(assistantMessage);" in code_handler
    assert "messages.push" not in code_handler
    assert "const messages" not in code_handler
    assert "assistantAttribution.set(assistantMessage, result.node_id);" in code_handler
    assert '"Generating code…"' in code_handler
    assert 'status.scrollIntoView({ block: "nearest" });' in code_handler
    assert 'behavior: "smooth"' not in code_handler
    assert code_handler.index(
        "codeMessages.push(pendingMessage);"
    ) < code_handler.index("const request = post(")
    assert code_handler.index(
        'status.scrollIntoView({ block: "nearest" });'
    ) < code_handler.index("const result = await request;")
    assert 'typeof result.content === "string"' in code_handler
    assert 'typeof result.node_id === "string"' in code_handler
    assert "function rollbackPendingCodeMessage(pendingMessage)" in script
    assert "rollbackPendingCodeMessage(pendingMessage);" in code_handler
    assert (
        'if (input.value === "") input.value = pendingMessage.content;' in code_handler
    )
    render_code = script.split("function renderCode()", 1)[1].split(
        "function rollbackPendingCodeMessage", 1
    )[0]
    assert "container.scrollTop = container.scrollHeight;" in render_code
    assert "focus(" not in render_code
    assert "scrollIntoView" not in render_code
    assert "textContent = message.content;" in render_code
    assert '"/v1/code"' not in script
    assert "sessionStorage" not in script
    assert "indexedDB" not in script
    assert "innerHTML" not in script


def test_loopback_theme_preference_is_the_only_persistent_browser_state() -> None:
    web = files("home_ai_cluster").joinpath("web")
    html = web.joinpath("index.html").read_text(encoding="utf-8")
    stylesheet = web.joinpath("assets", "app.css").read_text(encoding="utf-8")
    script = web.joinpath("assets", "app.js").read_text(encoding="utf-8")

    assert '<label for="theme-select">Theme</label>' in html
    assert '<select id="theme-select">' in html
    theme_select = html.split('<select id="theme-select">', 1)[1].split("</select>", 1)[
        0
    ]
    assert theme_select == (
        '<option value="system">System</option><option value="light">Light</option>'
        '<option value="dark">Dark</option>'
    )
    bootstrap = html.split("<script>", 1)[1].split("</script>", 1)[0]
    assert 'localStorage.getItem("home-ai-cluster.theme")' in bootstrap
    assert 'document.documentElement.setAttribute("data-theme", theme);' in bootstrap
    assert 'theme === "light" || theme === "dark"' in bootstrap
    assert "catch (_)" in bootstrap

    assert 'const themeKey = "home-ai-cluster.theme";' in script
    assert 'themeSelect.value = "system";' in script
    assert "localStorage.setItem(themeKey, theme);" in script
    assert "localStorage.removeItem(themeKey);" in script
    assert 'localStorage.setItem(themeKey, "system")' not in script
    assert 'root.setAttribute("data-theme", theme);' in script
    assert 'root.removeAttribute("data-theme");' in script
    assert 'theme === "light" || theme === "dark"' in script
    assert "function initializeThemePreference()" in script
    assert "function useSystemTheme()" in script
    assert script.count("catch (_)") >= 3
    assert "sessionStorage" not in script
    assert "indexedDB" not in script
    assert "document.cookie" not in script
    assert "matchMedia" not in script
    assert 'addEventListener("storage"' not in script

    assert "color-scheme: light dark;" in stylesheet
    assert "@media (prefers-color-scheme: dark)" in stylesheet
    assert ":root:not([data-theme])" in stylesheet
    assert ':root[data-theme="light"] { color-scheme: light; }' in stylesheet
    assert ':root[data-theme="dark"] { color-scheme: dark;' in stylesheet
    assert (
        "--page-background: #0b1525;"
        in stylesheet.split(':root[data-theme="dark"]', 1)[1]
    )
    assert "select:focus-visible" in stylesheet
    assert ".header-tools" in stylesheet
    assert "@media (max-width: 40rem)" in stylesheet
