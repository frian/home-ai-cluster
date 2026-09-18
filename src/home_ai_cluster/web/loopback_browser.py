"""Fixed browser assets for the RFC-0062 loopback application composition."""

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from home_ai_cluster.api.client_disconnect import (
    cancellation_has_won,
    run_routable_execution,
)
from home_ai_cluster.api.routes import handle_chat_cluster_request
from home_ai_cluster.commands import external_information_command
from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    RequestConstraints,
    SourceGroundedChatRequest,
)
from home_ai_cluster.core.workspace_authority import WorkspaceAuthorityError
from home_ai_cluster.retained_configuration import (
    RetainedConfigurationError,
    RetainedImageGenerationConfiguration,
    RetainedLocalConfiguration,
    browser_retained_image_generation_shape_is_supported,
    browser_retained_local_shape_is_supported,
    build_retained_image_generation_configuration,
    build_retained_local_configuration,
    build_retained_remote_node_declaration,
    load_retained_configuration,
    remove_retained_remote_node,
    replace_retained_external_information_plugin,
    replace_retained_image_generation_configuration,
    replace_retained_local_configuration,
    replace_retained_remote_node,
    reset_retained_image_generation_configuration,
    reset_retained_local_configuration,
    set_retained_chat_external_information_fallback,
    validate_external_information_plugin_name,
)
from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration
from home_ai_cluster.workspace_aware_code import (
    WorkspaceAwareCodeStatus,
    run_workspace_aware_code_async,
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
    "temperature",
    "local_capabilities",
    "execution_limit",
)
_REMOTE_NODE_DOCUMENT_KEYS = ("base_url", "capabilities")
_IMAGE_GENERATION_DOCUMENT_KEYS = ("base_url",)
_EXTERNAL_INFORMATION_DOCUMENT_KEYS = ("plugin",)
_CHAT_EXTERNAL_INFORMATION_DOCUMENT_KEYS = ("authorized",)
_WORKSPACE_CODE_KEYS = ("root", "grants", "history", "instruction")
_WORKSPACE_GRANTS = frozenset({"list", "read", "write", "create"})
_EXTERNAL_INFORMATION_OPERATION_KEYS = ("plugin", "query", "question")


def _workspace_code_document(
    value: Any,
) -> tuple[str, set[str], list[ChatMessage], str]:
    if not isinstance(value, dict) or set(value) != set(_WORKSPACE_CODE_KEYS):
        raise ValueError("invalid workspace Code request")
    root, grants, history, instruction = (
        value["root"],
        value["grants"],
        value["history"],
        value["instruction"],
    )
    if not isinstance(root, str) or not root or not isinstance(grants, list):
        raise ValueError("invalid workspace Code request")
    if not grants or any(not isinstance(item, str) for item in grants):
        raise ValueError("invalid workspace Code request")
    grant_set = set(grants)
    if len(grant_set) != len(grants) or not grant_set <= _WORKSPACE_GRANTS:
        raise ValueError("invalid workspace Code request")
    if (
        not isinstance(history, list)
        or not isinstance(instruction, str)
        or not instruction.strip()
    ):
        raise ValueError("invalid workspace Code request")
    try:
        messages = [ChatMessage.model_validate(item) for item in history]
        ClusterRequest(
            messages=[*messages, ChatMessage(role="user", content=instruction)],
            capability=Capability(name="code"),
        )
    except (TypeError, ValueError):
        raise ValueError("invalid workspace Code request") from None
    if len(messages) % 2 or any(
        message.role != ("user" if index % 2 == 0 else "assistant")
        for index, message in enumerate(messages)
    ):
        raise ValueError("invalid workspace Code request")
    return root, grant_set, messages, instruction


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
        "temperature": runtime.temperature,
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
        temperature=document["temperature"],
        local_capabilities=document["local_capabilities"],
        execution_limit=document["execution_limit"],
    )


def _browser_image_generation_document(
    image_generation: RetainedImageGenerationConfiguration,
) -> dict[str, object]:
    if not browser_retained_image_generation_shape_is_supported(image_generation):
        raise ValueError("unsupported retained Image Generation configuration shape")
    return {"runtime": "stable-diffusion-cpp", "base_url": image_generation.base_url}


def _image_generation_from_browser_document(
    document: Any,
) -> RetainedImageGenerationConfiguration:
    if not isinstance(document, dict) or set(document) != set(
        _IMAGE_GENERATION_DOCUMENT_KEYS
    ):
        raise ValueError("invalid retained Image Generation configuration")
    return build_retained_image_generation_configuration(base_url=document["base_url"])


def _external_information_plugin_from_browser_document(document: Any) -> str:
    if not isinstance(document, dict) or set(document) != set(
        _EXTERNAL_INFORMATION_DOCUMENT_KEYS
    ):
        raise ValueError("invalid retained external-information configuration")
    return validate_external_information_plugin_name(document["plugin"])


def _chat_external_information_fallback_from_browser_document(document: Any) -> bool:
    if not isinstance(document, dict) or set(document) != set(
        _CHAT_EXTERNAL_INFORMATION_DOCUMENT_KEYS
    ):
        raise ValueError("invalid retained Chat configuration")
    authorized = document["authorized"]
    if not isinstance(authorized, bool):
        raise ValueError("invalid retained Chat configuration")
    return authorized


def _browser_remote_node_document(node: RemoteNodeDeclaration) -> dict[str, object]:
    return {
        "node_id": node.node_id,
        "base_url": node.base_url,
        "capabilities": list(node.capabilities),
    }


def _remote_node_from_browser_document(
    node_id: str, document: Any
) -> RemoteNodeDeclaration:
    if not isinstance(document, dict) or set(document) != set(
        _REMOTE_NODE_DOCUMENT_KEYS
    ):
        raise ValueError("invalid retained remote node")
    if not isinstance(document["base_url"], str) or not isinstance(
        document["capabilities"], list
    ):
        raise ValueError("invalid retained remote node")
    return build_retained_remote_node_declaration(
        node_id=node_id,
        base_url=document["base_url"],
        capabilities=document["capabilities"],
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


def _external_information_operation_document(value: Any) -> tuple[str, str, str]:
    """Validate the browser edge without moving RFC-0077 validation earlier."""
    if not isinstance(value, dict) or set(value) != set(
        _EXTERNAL_INFORMATION_OPERATION_KEYS
    ):
        raise ValueError("invalid External Information request")
    plugin, query, question = value["plugin"], value["query"], value["question"]
    if (
        not isinstance(plugin, str)
        or not isinstance(query, str)
        or not isinstance(question, str)
    ):
        raise ValueError("invalid External Information request")
    try:
        selected_plugin = validate_external_information_plugin_name(
            plugin
            if plugin.strip()
            else load_retained_configuration().external_information_plugin
        )
        if selected_plugin is None:
            raise ValueError("missing plugin selection")
        return (
            selected_plugin,
            external_information_command._validate_query(query),
            question,
        )
    except (
        RetainedConfigurationError,
        ValueError,
        external_information_command._InvalidRequestInput,
    ):
        raise ValueError("invalid External Information request") from None


def add_loopback_browser_routes(app: FastAPI) -> FastAPI:
    """Attach only the fixed RFC-0062 browser page and assets to one API app."""

    @app.get("/", include_in_schema=False)
    def page() -> FileResponse:
        return FileResponse(
            _WEB_DIRECTORY / "index.html",
            media_type="text/html",
            headers={
                **_CACHE_HEADERS,
                "Content-Security-Policy": "frame-ancestors 'self'",
            },
        )

    @app.post("/external-information", include_in_schema=False)
    async def external_information(request: Request) -> JSONResponse:
        authority = _native_authority(request)
        if not _has_native_host_authority(request, authority):
            raise HTTPException(status_code=400, detail="invalid native authority")
        if request.headers.get("origin") != f"http://{authority}":
            raise HTTPException(status_code=403, detail="invalid native origin")
        content_type = request.headers.get("content-type", "").split(";", 1)[0]
        if content_type.strip().lower() != "application/json":
            raise HTTPException(status_code=415, detail="JSON required")
        try:
            plugin_name, query, question = _external_information_operation_document(
                await request.json()
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            raise HTTPException(
                status_code=400, detail="invalid External Information request"
            ) from None

        async def execute() -> SourceGroundedChatRequest | object:
            try:
                source_request = await (
                    external_information_command._acquire_source_grounded_request_async(
                        plugin_name, query, question
                    )
                )
            except external_information_command._AcquisitionFailure:
                raise HTTPException(
                    status_code=502,
                    detail="external-information-acquisition-failed",
                ) from None
            if cancellation_has_won():
                raise asyncio.CancelledError
            source_request = source_request.model_copy(
                update={
                    "constraints": RequestConstraints(
                        local_only=(
                            request.app.state.static_remote_wiring is None
                            and request.app.state.static_remote_collection_wiring
                            is None
                        )
                    )
                }
            )
            return await handle_chat_cluster_request(
                source_request,
                request.app.state.static_remote_wiring,
                request.app.state.static_remote_collection_wiring,
                request.app.state.local_app_composition,
            )

        result = await run_routable_execution(request, execute)
        return JSONResponse(result.model_dump())

    @app.post("/workspace-code", include_in_schema=False)
    async def workspace_code(request: Request) -> JSONResponse:
        authority = _native_authority(request)
        if not _has_native_host_authority(request, authority):
            raise HTTPException(status_code=400, detail="invalid native authority")
        if request.headers.get("origin") != f"http://{authority}":
            raise HTTPException(status_code=403, detail="invalid native origin")
        content_type = request.headers.get("content-type", "").split(";", 1)[0]
        if content_type.strip().lower() != "application/json":
            raise HTTPException(status_code=415, detail="JSON required")
        try:
            root, grants, history, instruction = _workspace_code_document(
                await request.json()
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            raise HTTPException(
                status_code=400, detail="invalid workspace Code request"
            ) from None
        activity: list[dict[str, str]] = []
        final_node_id: str | None = None

        async def infer(messages: tuple[ChatMessage, ...]):
            nonlocal final_node_id
            result = await handle_chat_cluster_request(
                ClusterRequest(
                    messages=list(messages), capability=Capability(name="code")
                ),
                request.app.state.static_remote_wiring,
                request.app.state.static_remote_collection_wiring,
                request.app.state.local_app_composition,
            )
            final_node_id = result.node_id
            return result

        try:
            outcome = await run_routable_execution(
                request,
                lambda: run_workspace_aware_code_async(
                    instruction,
                    root=root,
                    operations=grants,
                    prior_messages=history,
                    infer=infer,
                    on_completed_action=lambda operation, path, status: activity.append(
                        {"operation": operation, "path": path, "outcome": status}
                    ),
                ),
            )
        except WorkspaceAuthorityError:
            raise HTTPException(
                status_code=400, detail="invalid workspace root"
            ) from None
        if outcome.status == WorkspaceAwareCodeStatus.FINAL and outcome.content:
            return JSONResponse(
                {
                    "content": outcome.content,
                    "node_id": final_node_id,
                    "activity": activity,
                }
            )
        return JSONResponse({"status": outcome.status, "activity": activity})

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

    @app.delete("/retained-local-configuration", include_in_schema=False)
    def reset_retained_local_configuration_route(request: Request) -> JSONResponse:
        authority = _native_authority(request)
        if not _has_native_host_authority(request, authority):
            raise HTTPException(status_code=400, detail="invalid native authority")
        if request.headers.get("origin") != f"http://{authority}":
            raise HTTPException(status_code=403, detail="invalid native origin")
        try:
            local = load_retained_configuration().local
            if local is not None and not browser_retained_local_shape_is_supported(
                local
            ):
                raise ValueError("unsupported retained local configuration shape")
            reset_retained_local_configuration()
        except (RetainedConfigurationError, ValueError):
            raise HTTPException(
                status_code=400, detail="unable to reset retained local configuration"
            ) from None
        return JSONResponse({"local": None})

    @app.get("/retained-image-generation-configuration", include_in_schema=False)
    def retained_image_generation_configuration(request: Request) -> JSONResponse:
        if not _has_native_host_authority(request, _native_authority(request)):
            raise HTTPException(status_code=400, detail="invalid native authority")
        try:
            image_generation = load_retained_configuration().image_generation
            if image_generation is None:
                return JSONResponse({"image_generation": None})
            return JSONResponse(
                {
                    "image_generation": _browser_image_generation_document(
                        image_generation
                    )
                }
            )
        except (RetainedConfigurationError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="retained Image Generation configuration unavailable",
            ) from None

    @app.put("/retained-image-generation-configuration", include_in_schema=False)
    async def replace_retained_image_generation_configuration_route(
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
            image_generation = _image_generation_from_browser_document(
                await request.json()
            )
            if not browser_retained_image_generation_shape_is_supported(
                image_generation
            ):
                raise ValueError(
                    "unsupported retained Image Generation configuration shape"
                )
            replace_retained_image_generation_configuration(image_generation)
        except (
            json.JSONDecodeError,
            RetainedConfigurationError,
            TypeError,
            ValueError,
        ):
            raise HTTPException(
                status_code=400,
                detail="invalid retained Image Generation configuration",
            ) from None
        return JSONResponse(
            {"image_generation": _browser_image_generation_document(image_generation)}
        )

    @app.delete("/retained-image-generation-configuration", include_in_schema=False)
    def reset_retained_image_generation_configuration_route(
        request: Request,
    ) -> JSONResponse:
        authority = _native_authority(request)
        if not _has_native_host_authority(request, authority):
            raise HTTPException(status_code=400, detail="invalid native authority")
        if request.headers.get("origin") != f"http://{authority}":
            raise HTTPException(status_code=403, detail="invalid native origin")
        try:
            image_generation = load_retained_configuration().image_generation
            if image_generation is not None and not (
                browser_retained_image_generation_shape_is_supported(image_generation)
            ):
                raise ValueError(
                    "unsupported retained Image Generation configuration shape"
                )
            reset_retained_image_generation_configuration()
        except (RetainedConfigurationError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="unable to reset retained Image Generation configuration",
            ) from None
        return JSONResponse({"image_generation": None})

    @app.get("/retained-external-information-configuration", include_in_schema=False)
    def retained_external_information_configuration(request: Request) -> JSONResponse:
        if not _has_native_host_authority(request, _native_authority(request)):
            raise HTTPException(status_code=400, detail="invalid native authority")
        try:
            plugin = load_retained_configuration().external_information_plugin
        except RetainedConfigurationError:
            raise HTTPException(
                status_code=400,
                detail="retained external-information configuration unavailable",
            ) from None
        return JSONResponse({"plugin": plugin})

    @app.put("/retained-external-information-configuration", include_in_schema=False)
    async def replace_retained_external_information_configuration_route(
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
            plugin = _external_information_plugin_from_browser_document(
                await request.json()
            )
            replace_retained_external_information_plugin(plugin)
        except (
            json.JSONDecodeError,
            RetainedConfigurationError,
            TypeError,
            ValueError,
        ):
            raise HTTPException(
                status_code=400,
                detail="invalid retained external-information configuration",
            ) from None
        return JSONResponse({"plugin": plugin})

    @app.delete("/retained-external-information-configuration", include_in_schema=False)
    def reset_retained_external_information_configuration_route(
        request: Request,
    ) -> JSONResponse:
        authority = _native_authority(request)
        if not _has_native_host_authority(request, authority):
            raise HTTPException(status_code=400, detail="invalid native authority")
        if request.headers.get("origin") != f"http://{authority}":
            raise HTTPException(status_code=403, detail="invalid native origin")
        try:
            replace_retained_external_information_plugin(None)
        except RetainedConfigurationError:
            raise HTTPException(
                status_code=400,
                detail="unable to reset retained external-information configuration",
            ) from None
        return JSONResponse({"plugin": None})

    @app.get(
        "/retained-chat-external-information-configuration", include_in_schema=False
    )
    def retained_chat_external_information_configuration(
        request: Request,
    ) -> JSONResponse:
        if not _has_native_host_authority(request, _native_authority(request)):
            raise HTTPException(status_code=400, detail="invalid native authority")
        try:
            authorized = (
                load_retained_configuration().chat_external_information_fallback
            )
        except RetainedConfigurationError:
            raise HTTPException(
                status_code=400, detail="retained Chat configuration unavailable"
            ) from None
        return JSONResponse({"authorized": authorized})

    @app.put(
        "/retained-chat-external-information-configuration", include_in_schema=False
    )
    async def set_retained_chat_external_information_configuration_route(
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
            authorized = _chat_external_information_fallback_from_browser_document(
                await request.json()
            )
            set_retained_chat_external_information_fallback(authorized)
        except (
            json.JSONDecodeError,
            RetainedConfigurationError,
            TypeError,
            ValueError,
        ):
            raise HTTPException(
                status_code=400, detail="invalid retained Chat configuration"
            ) from None
        return JSONResponse({"authorized": authorized})

    @app.get("/retained-remote-nodes", include_in_schema=False)
    def retained_remote_nodes(request: Request) -> JSONResponse:
        if not _has_native_host_authority(request, _native_authority(request)):
            raise HTTPException(status_code=400, detail="invalid native authority")
        try:
            configuration = load_retained_configuration()
        except RetainedConfigurationError:
            raise HTTPException(
                status_code=400, detail="retained remote nodes unavailable"
            ) from None
        return JSONResponse(
            {
                "remote_nodes": [
                    _browser_remote_node_document(node)
                    for node in configuration.remote_nodes
                ]
            }
        )

    @app.put("/retained-remote-nodes/{node_id:path}", include_in_schema=False)
    async def replace_retained_remote_node_route(
        node_id: str, request: Request
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
            declaration = _remote_node_from_browser_document(
                node_id, await request.json()
            )
            replace_retained_remote_node(declaration)
        except (
            json.JSONDecodeError,
            RetainedConfigurationError,
            TypeError,
            ValueError,
        ):
            raise HTTPException(
                status_code=400, detail="invalid retained remote node"
            ) from None
        return JSONResponse({"remote_node": _browser_remote_node_document(declaration)})

    @app.delete("/retained-remote-nodes/{node_id:path}", include_in_schema=False)
    def remove_retained_remote_node_route(
        node_id: str, request: Request
    ) -> JSONResponse:
        authority = _native_authority(request)
        if not _has_native_host_authority(request, authority):
            raise HTTPException(status_code=400, detail="invalid native authority")
        if request.headers.get("origin") != f"http://{authority}":
            raise HTTPException(status_code=403, detail="invalid native origin")
        try:
            removed = remove_retained_remote_node(node_id)
        except (RetainedConfigurationError, ValueError):
            raise HTTPException(
                status_code=400, detail="invalid retained remote node"
            ) from None
        if not removed:
            raise HTTPException(status_code=404, detail="retained node not found")
        return JSONResponse({"removed": node_id})

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
