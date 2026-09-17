"""Closed RFC-0130 trusted-LAN browser authority."""

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response

from home_ai_cluster.api.routes import ChatRequest
from home_ai_cluster.api.routes import (
    chat as native_chat,
)
from home_ai_cluster.api.routes import (
    classify as native_classify,
)
from home_ai_cluster.api.routes import (
    image_generation as native_image_generation,
)
from home_ai_cluster.api.routes import (
    summarize as native_summarize,
)
from home_ai_cluster.main import install_common_exception_handlers

_WEB_DIRECTORY = Path(__file__).parent
_CACHE_HEADERS = {"Cache-Control": "no-store"}
_ASSETS = {
    "/assets/lan.css": ("assets/lan.css", "text/css"),
    "/assets/lan.js": ("assets/lan.js", "application/javascript"),
}


def _authority(host: str, port: int) -> str:
    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"


def _require_post_authority(request: Request) -> None:
    authority = request.app.state.trusted_lan_authority
    if request.headers.get("origin") != f"http://{authority}":
        raise HTTPException(status_code=403, detail="invalid trusted-LAN origin")
    content_type = request.headers.get("content-type", "").split(";", 1)[0]
    if content_type.strip().lower() != "application/json":
        raise HTTPException(status_code=415, detail="JSON required")


def create_trusted_lan_browser_app(owner: FastAPI, *, host: str, port: int) -> FastAPI:
    """Create the closed capability-only RFC-0130 application for one owner."""
    app = FastAPI(
        title="Home AI Cluster trusted-LAN browser",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    install_common_exception_handlers(app)
    app.state.trusted_lan_authority = _authority(host, port)
    app.state.local_app_composition = owner.state.local_app_composition
    app.state.static_remote_wiring = owner.state.static_remote_wiring
    app.state.static_remote_collection_wiring = (
        owner.state.static_remote_collection_wiring
    )

    @app.middleware("http")
    async def exact_host(request: Request, call_next):
        if request.headers.get("host") != app.state.trusted_lan_authority:
            return Response(status_code=400)
        return await call_next(request)

    @app.get("/", include_in_schema=False)
    def page() -> FileResponse:
        return FileResponse(
            _WEB_DIRECTORY / "lan.html",
            media_type="text/html",
            headers={
                **_CACHE_HEADERS,
                "Content-Security-Policy": "frame-ancestors 'self'",
            },
        )

    for route, (path, media_type) in _ASSETS.items():
        app.add_api_route(
            route,
            lambda path=path, media_type=media_type: FileResponse(
                _WEB_DIRECTORY / path, media_type=media_type, headers=_CACHE_HEADERS
            ),
            methods=["GET"],
            include_in_schema=False,
        )

    @app.post("/v1/chat", dependencies=[Depends(_require_post_authority)])
    async def chat(request: ChatRequest, http_request: Request):
        if request.capability not in {"chat", "code"}:
            raise HTTPException(
                status_code=422, detail="invalid trusted-LAN capability"
            )
        return await native_chat(request, http_request)

    @app.post("/v1/summarize", dependencies=[Depends(_require_post_authority)])
    async def summarize(http_request: Request):
        return await native_summarize(http_request)

    @app.post("/v1/classify", dependencies=[Depends(_require_post_authority)])
    async def classify(http_request: Request):
        return await native_classify(http_request)

    @app.post("/v1/image-generation", dependencies=[Depends(_require_post_authority)])
    async def image_generation(http_request: Request):
        return await native_image_generation(http_request)

    return app
