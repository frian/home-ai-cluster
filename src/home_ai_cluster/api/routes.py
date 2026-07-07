from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api.wiring import (
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
)
from home_ai_cluster.core.orchestrator import orchestrate_request
from home_ai_cluster.core.router import NoMatchingAdapterError

router = APIRouter()


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    capability: str = Field(min_length=1)


async def handle_static_local_cluster_request(
    cluster_request: ClusterRequest,
) -> ClusterResult:
    node_registry = create_static_local_node_registry()
    adapter_registry = create_static_runtime_adapter_registry()

    try:
        return await orchestrate_request(
            cluster_request,
            node_registry,
            adapter_registry,
        )
    except RuntimeAdapterUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Runtime adapter unavailable",
        ) from exc
    except NoMatchingAdapterError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"No adapter provides capability: {cluster_request.capability.name}",
        ) from exc


@router.post("/v1/chat", response_model=ClusterResult)
async def chat(request: ChatRequest) -> ClusterResult:
    cluster_request = ClusterRequest(
        messages=request.messages,
        capability=Capability(name=request.capability),
    )

    return await handle_static_local_cluster_request(cluster_request)


@router.post("/internal/cluster/request", response_model=ClusterResult)
async def internal_cluster_request(request: ClusterRequest) -> ClusterResult:
    return await handle_static_local_cluster_request(request)
