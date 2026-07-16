from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api.proof_orchestrator import orchestrate_static_remote_proof
from home_ai_cluster.api.wiring import (
    StaticRemoteProofWiring,
    StaticRemoteWiring,
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    RequestConstraints,
)
from home_ai_cluster.core.orchestrator import (
    orchestrate_request,
    orchestrate_request_with_static_remote_fallback,
)
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


async def handle_chat_cluster_request(
    cluster_request: ClusterRequest,
    static_remote_proof_wiring: StaticRemoteProofWiring | None,
    static_remote_wiring: StaticRemoteWiring | None,
) -> ClusterResult:
    """Use explicit proof, ordinary static remote, or local-only wiring."""
    if static_remote_proof_wiring is not None:
        return await orchestrate_static_remote_proof(
            cluster_request,
            static_remote_proof_wiring,
        )

    if static_remote_wiring is not None:
        return await orchestrate_request_with_static_remote_fallback(
            cluster_request,
            static_remote_wiring.node_registry,
            static_remote_wiring.adapter_registry,
            static_remote_wiring.remote_registry,
            static_remote_wiring.remote_transport,
        )

    return await handle_static_local_cluster_request(cluster_request)


@router.post("/v1/chat", response_model=ClusterResult)
async def chat(request: ChatRequest, http_request: Request) -> ClusterResult:
    automatic_proof_orchestrator = http_request.app.state.automatic_proof_orchestrator
    static_remote_wiring = http_request.app.state.static_remote_wiring
    cluster_request = ClusterRequest(
        messages=request.messages,
        capability=Capability(name=request.capability),
        constraints=(
            RequestConstraints(local_only=False)
            if automatic_proof_orchestrator or static_remote_wiring is not None
            else RequestConstraints()
        ),
    )

    if automatic_proof_orchestrator:
        return await automatic_proof_orchestrator(cluster_request)

    return await handle_chat_cluster_request(
        cluster_request,
        http_request.app.state.static_remote_proof_wiring,
        static_remote_wiring,
    )


@router.post("/internal/cluster/request", response_model=ClusterResult)
async def internal_cluster_request(request: ClusterRequest) -> ClusterResult:
    return await handle_static_local_cluster_request(request)
