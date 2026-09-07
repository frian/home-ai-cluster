"""Fixed browser assets for the RFC-0062 loopback application composition."""

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from home_ai_cluster.retained_configuration import (
    RetainedConfigurationError,
    RetainedLocalConfiguration,
    browser_retained_local_shape_is_supported,
    build_retained_local_configuration,
    load_retained_configuration,
    replace_retained_local_configuration,
)

_WEB_DIRECTORY = Path(__file__).parent
_CACHE_HEADERS = {"Cache-Control": "no-store"}


_LOCAL_DOCUMENT_KEYS = (
    "runtime",
    "ollama_model",
    "ollama_disable_thinking",
    "llama_server_base_url",
    "llama_server_model",
    "vllm_base_url",
    "vllm_model",
    "local_capabilities",
    "execution_limit",
)


def _browser_local_document(local: RetainedLocalConfiguration) -> dict[str, object]:
    if not browser_retained_local_shape_is_supported(local):
        raise ValueError("unsupported retained local configuration shape")
    runtime = local.runtime
    return {
        "runtime": runtime.runtime,
        "ollama_model": runtime.ollama_model,
        "ollama_disable_thinking": runtime.ollama_disable_thinking,
        "llama_server_base_url": runtime.llama_server_base_url,
        "llama_server_model": runtime.llama_server_model,
        "vllm_base_url": runtime.vllm_base_url,
        "vllm_model": runtime.vllm_model,
        "local_capabilities": (
            None if local.local_capabilities is None else list(local.local_capabilities)
        ),
        "execution_limit": local.execution_limit,
    }


def _local_from_browser_document(document: Any) -> RetainedLocalConfiguration:
    if not isinstance(document, dict) or set(document) != set(_LOCAL_DOCUMENT_KEYS):
        raise ValueError("invalid retained local configuration")
    return build_retained_local_configuration(
        runtime=document["runtime"],
        ollama_model=document["ollama_model"],
        ollama_disable_thinking=document["ollama_disable_thinking"],
        llama_server_base_url=document["llama_server_base_url"],
        llama_server_model=document["llama_server_model"],
        vllm_base_url=document["vllm_base_url"],
        vllm_model=document["vllm_model"],
        local_capabilities=document["local_capabilities"],
        execution_limit=document["execution_limit"],
    )


def _native_authority(request: Request) -> str | None:
    """Return the exact native authority from Uvicorn's local socket scope."""
    server = request.scope.get("server")
    if (
        not isinstance(server, (tuple, list))
        or len(server) != 2
        or server[0] != "127.0.0.1"
        or isinstance(server[1], bool)
        or not isinstance(server[1], int)
        or not 1 <= server[1] <= 65535
    ):
        return None
    return f"127.0.0.1:{server[1]}"


def _has_native_host_authority(request: Request, authority: str | None) -> bool:
    return authority is not None and request.headers.get("host") == authority


def add_loopback_browser_routes(app: FastAPI) -> FastAPI:
    """Attach only the fixed RFC-0062 browser page and assets to one API app."""

    @app.get("/", include_in_schema=False)
    def page() -> FileResponse:
        return FileResponse(
            _WEB_DIRECTORY / "index.html",
            media_type="text/html",
            headers=_CACHE_HEADERS,
        )

    @app.get("/assets/app.css", include_in_schema=False)
    def stylesheet() -> FileResponse:
        return FileResponse(
            _WEB_DIRECTORY / "assets" / "app.css",
            media_type="text/css",
            headers=_CACHE_HEADERS,
        )

    @app.get("/assets/app.js", include_in_schema=False)
    def script() -> FileResponse:
        return FileResponse(
            _WEB_DIRECTORY / "assets" / "app.js",
            media_type="application/javascript",
            headers=_CACHE_HEADERS,
        )

    @app.get("/retained-local-configuration", include_in_schema=False)
    def retained_local_configuration(request: Request) -> JSONResponse:
        if not _has_native_host_authority(request, _native_authority(request)):
            raise HTTPException(status_code=400, detail="invalid native authority")
        try:
            local = load_retained_configuration().local
            if local is None:
                return JSONResponse({"local": None})
            return JSONResponse({"local": _browser_local_document(local)})
        except (RetainedConfigurationError, ValueError):
            raise HTTPException(
                status_code=400, detail="retained local configuration unavailable"
            ) from None

    @app.put("/retained-local-configuration", include_in_schema=False)
    async def replace_retained_local_configuration_route(
        request: Request,
    ) -> JSONResponse:
        authority = _native_authority(request)
        if not _has_native_host_authority(request, authority):
            raise HTTPException(status_code=400, detail="invalid native authority")
        if request.headers.get("origin") != f"http://{authority}":
            raise HTTPException(status_code=403, detail="invalid native origin")
        content_type = request.headers.get("content-type", "").split(";", 1)[0]
        if content_type.strip().lower() != "application/json":
            raise HTTPException(status_code=415, detail="JSON required")
        try:
            local = _local_from_browser_document(await request.json())
        except (
            json.JSONDecodeError,
            RetainedConfigurationError,
            TypeError,
            ValueError,
        ):
            raise HTTPException(
                status_code=400, detail="invalid retained local configuration"
            ) from None
        if not browser_retained_local_shape_is_supported(local):
            raise HTTPException(
                status_code=400, detail="unsupported retained local configuration shape"
            )
        try:
            replace_retained_local_configuration(local)
        except RetainedConfigurationError:
            raise HTTPException(
                status_code=400, detail="unable to retain local configuration"
            ) from None
        return JSONResponse({"local": _browser_local_document(local)})

    @app.get("/assets/pdfjs-6.2.108/pdf.min.mjs", include_in_schema=False)
    def pdfjs_main() -> FileResponse:
        return FileResponse(
            _WEB_DIRECTORY / "assets" / "pdfjs-6.2.108" / "pdf.min.mjs",
            media_type="application/javascript",
            headers=_CACHE_HEADERS,
        )

    @app.get("/assets/pdfjs-6.2.108/pdf.worker.min.mjs", include_in_schema=False)
    def pdfjs_worker() -> FileResponse:
        return FileResponse(
            _WEB_DIRECTORY / "assets" / "pdfjs-6.2.108" / "pdf.worker.min.mjs",
            media_type="application/javascript",
            headers=_CACHE_HEADERS,
        )

    return app
