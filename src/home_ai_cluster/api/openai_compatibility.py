"""Minimal OpenAI-compatible public-edge chat translation."""

import asyncio
import json
import re
import sys
import time
import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api.routes import handle_chat_cluster_request
from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
)
from home_ai_cluster.core.router import NoMatchingAdapterError

COMPATIBILITY_MODEL = "home-ai-cluster"
_AUTHORIZATION_PATTERN = re.compile(r"^Bearer [^\s,]+$", re.IGNORECASE)

compatibility_router = APIRouter()


class ProofObservationState:
    """Process-local accepted-request counting for RFC-0047 only."""

    def __init__(self) -> None:
        self._accepted_request_count = 0
        self._lock = asyncio.Lock()

    async def count_accepted_request(self) -> int:
        """Return the next distinct positive count without serializing execution."""
        async with self._lock:
            self._accepted_request_count += 1
            return self._accepted_request_count


class CompatibilityMessage(BaseModel):
    """One supported plain-text compatibility message."""

    model_config = ConfigDict(extra="forbid", strict=True)

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class CompatibilityRequest(BaseModel):
    """The intentionally small RFC-0031 request subset."""

    model_config = ConfigDict(extra="forbid", strict=True)

    model: str
    messages: list[CompatibilityMessage] = Field(min_length=1)
    stream: bool = False
    n: int = 1


class CompatibilityChoiceMessage(BaseModel):
    role: Literal["assistant"]
    content: str


class CompatibilityChoice(BaseModel):
    index: Literal[0]
    message: CompatibilityChoiceMessage
    finish_reason: None = None


class CompatibilityResponse(BaseModel):
    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    choices: list[CompatibilityChoice]


class CompatibilityErrorBody(BaseModel):
    message: str
    type: Literal["invalid_request_error", "server_error"]
    param: str | None = None
    code: None = None


class CompatibilityErrorResponse(BaseModel):
    error: CompatibilityErrorBody


def compatibility_error(
    status_code: int,
    message: str,
    error_type: Literal["invalid_request_error", "server_error"],
    param: str | None = None,
) -> JSONResponse:
    """Return the endpoint-local RFC-0031 error envelope."""
    body = CompatibilityErrorResponse(
        error=CompatibilityErrorBody(
            message=message,
            type=error_type,
            param=param,
        )
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def _unsupported_value(param: str | None = None) -> JSONResponse:
    return compatibility_error(
        400,
        "Unsupported chat completion request value",
        "invalid_request_error",
        param,
    )


def _invalid_request(param: str | None = None) -> JSONResponse:
    return compatibility_error(
        400,
        "Invalid chat completion request",
        "invalid_request_error",
        param,
    )


def _authorization_is_valid(value: str | None) -> bool:
    return value is None or _AUTHORIZATION_PATTERN.fullmatch(value) is not None


def _validation_error_response(error: ValidationError) -> JSONResponse:
    """Classify strict DTO failures without exposing Pydantic details."""
    first_error = error.errors()[0]
    location = first_error["loc"]
    top_level = location[0] if location else None

    if first_error["type"] == "missing":
        return _invalid_request()

    if top_level in {"stream", "n"}:
        return _unsupported_value(top_level)

    if top_level == "messages" and len(location) > 1:
        return _unsupported_value("messages")

    return _invalid_request()


def _validate_compatibility_request(
    body: object,
) -> CompatibilityRequest | JSONResponse:
    if not isinstance(body, dict):
        return _invalid_request()

    unexpected_fields = set(body) - {"model", "messages", "stream", "n"}
    if unexpected_fields:
        return _unsupported_value(sorted(unexpected_fields)[0])

    model = body.get("model")
    if isinstance(model, str) and model != COMPATIBILITY_MODEL:
        return compatibility_error(
            400,
            "Unsupported model identifier",
            "invalid_request_error",
            "model",
        )

    stream = body.get("stream", False)
    if stream is True:
        return compatibility_error(
            400,
            "Streaming is not supported",
            "invalid_request_error",
            "stream",
        )
    if stream is not False:
        return _unsupported_value("stream")

    if "n" in body and body["n"] != 1:
        return _unsupported_value("n")

    messages = body.get("messages")
    if isinstance(messages, list):
        for message in messages:
            if isinstance(message, dict):
                unexpected_message_fields = set(message) - {"role", "content"}
                if unexpected_message_fields:
                    return _unsupported_value("messages")

    try:
        return CompatibilityRequest.model_validate(body)
    except ValidationError as error:
        return _validation_error_response(error)


def _compatibility_response(result: ClusterResult) -> CompatibilityResponse:
    return CompatibilityResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        object="chat.completion",
        created=int(time.time()),
        model=result.model or COMPATIBILITY_MODEL,
        choices=[
            CompatibilityChoice(
                index=0,
                message=CompatibilityChoiceMessage(
                    role="assistant",
                    content=result.content,
                ),
            )
        ],
    )


def _write_proof_observation_line(
    accepted_request_count: int | None,
    *,
    outcome: Literal["success", "failure"],
    result_node_id: str,
) -> None:
    """Best-effort RFC-0047 process output without retaining request results."""
    if accepted_request_count is None:
        return

    try:
        sys.stderr.write(
            "proof_observation "
            f"accepted_request={accepted_request_count} "
            f"outcome={outcome} result_node_id={result_node_id}\n"
        )
    except (OSError, ValueError):
        pass


@compatibility_router.post("/v1/chat/completions", response_model=CompatibilityResponse)
async def chat_completions(request: Request) -> JSONResponse:
    """Translate the RFC-0031 subset into the existing cluster chat flow."""
    if not _authorization_is_valid(request.headers.get("authorization")):
        return _invalid_request("authorization")

    try:
        body = await request.json()
    except (json.JSONDecodeError, ValueError):
        return _invalid_request()

    compatibility_request = _validate_compatibility_request(body)
    if isinstance(compatibility_request, JSONResponse):
        return compatibility_request

    proof_observation_state = getattr(
        request.app.state,
        "proof_observation_state",
        None,
    )
    accepted_request_count = (
        await proof_observation_state.count_accepted_request()
        if proof_observation_state is not None
        else None
    )

    cluster_request = ClusterRequest(
        messages=[
            ChatMessage(role=message.role, content=message.content)
            for message in compatibility_request.messages
        ],
        capability=Capability(name="chat"),
    )

    try:
        static_remote_wiring = request.app.state.static_remote_wiring
        static_remote_collection_wiring = (
            request.app.state.static_remote_collection_wiring
        )
        local_app_composition = request.app.state.local_app_composition
        if (
            static_remote_wiring is None
            and static_remote_collection_wiring is None
            and local_app_composition is None
        ):
            result = await handle_chat_cluster_request(
                cluster_request,
                request.app.state.static_remote_proof_wiring,
            )
        else:
            result = await handle_chat_cluster_request(
                cluster_request,
                request.app.state.static_remote_proof_wiring,
                static_remote_wiring=static_remote_wiring,
                static_remote_collection_wiring=static_remote_collection_wiring,
                local_app_composition=local_app_composition,
            )
    except HTTPException as error:
        if error.status_code == 404:
            error_response = compatibility_error(
                503,
                "No available chat capability",
                "server_error",
            )
        elif error.status_code == 503:
            error_response = compatibility_error(
                503,
                "Runtime adapter unavailable",
                "server_error",
            )
        else:
            error_response = compatibility_error(
                500,
                "Internal server error",
                "server_error",
            )
    except NoMatchingAdapterError:
        error_response = compatibility_error(
            503,
            "No available chat capability",
            "server_error",
        )
    except RuntimeAdapterUnavailableError:
        error_response = compatibility_error(
            503,
            "Runtime adapter unavailable",
            "server_error",
        )
    except Exception:
        error_response = compatibility_error(
            500,
            "Internal server error",
            "server_error",
        )

    else:
        _write_proof_observation_line(
            accepted_request_count,
            outcome="success",
            result_node_id=result.node_id,
        )
        return JSONResponse(content=_compatibility_response(result).model_dump())

    _write_proof_observation_line(
        accepted_request_count,
        outcome="failure",
        result_node_id="none",
    )
    return error_response
