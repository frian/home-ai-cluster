from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api.proof_orchestrator import orchestrate_static_remote_proof
from home_ai_cluster.api.wiring import (
    LocalAppComposition,
    ProofReceivingAppWiring,
    StaticRemoteCollectionWiring,
    StaticRemoteProofWiring,
    StaticRemoteWiring,
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.models import (
    INTERNAL_CLUSTER_REQUEST_ADAPTER,
    Capability,
    ChatInternalRequest,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    InternalClusterStatusResponse,
    RequestConstraints,
    SummarizeRequest,
)
from home_ai_cluster.core.orchestrator import (
    orchestrate_request,
    orchestrate_request_with_static_remote_fallback,
)
from home_ai_cluster.core.ordered_remote_fallback import (
    orchestrate_request_with_ordered_static_remote_fallback,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.router import NoMatchingAdapterError
from home_ai_cluster.local_health_snapshot import (
    project_health_snapshot,
    project_local_cluster_status,
)

router = APIRouter()


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    capability: str = Field(min_length=1)


class SummarizePublicRequest(BaseModel):
    """The deliberately narrow public body for one text summarization."""

    text: str


def _resolve_local_registries(
    local_app_composition: LocalAppComposition | None,
) -> tuple[NodeRegistry, AdapterRegistry]:
    if local_app_composition is not None:
        return (
            local_app_composition.node_registry,
            local_app_composition.adapter_registry,
        )

    return (
        create_static_local_node_registry(),
        create_static_runtime_adapter_registry(),
    )


async def handle_static_local_cluster_request(
    cluster_request: ClusterRequest | SummarizeRequest,
    proof_receiving_app_wiring: ProofReceivingAppWiring | None = None,
    local_app_composition: LocalAppComposition | None = None,
) -> ClusterResult:
    if proof_receiving_app_wiring is not None:
        node_registry = proof_receiving_app_wiring.node_registry
        adapter_registry = proof_receiving_app_wiring.adapter_registry
    else:
        node_registry, adapter_registry = _resolve_local_registries(
            local_app_composition
        )

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
    static_remote_wiring: StaticRemoteWiring | None = None,
    static_remote_collection_wiring: StaticRemoteCollectionWiring | None = None,
    local_app_composition: LocalAppComposition | None = None,
) -> ClusterResult:
    """Use proof, ordinary static remote, collection, or local-only wiring."""
    if static_remote_proof_wiring is not None:
        return await orchestrate_static_remote_proof(
            cluster_request,
            static_remote_proof_wiring,
        )

    if static_remote_wiring is not None:
        try:
            return await orchestrate_request_with_static_remote_fallback(
                cluster_request,
                static_remote_wiring.node_registry,
                static_remote_wiring.adapter_registry,
                static_remote_wiring.remote_registry,
                static_remote_wiring.remote_transport,
            )
        except RuntimeAdapterUnavailableError as exc:
            raise HTTPException(
                status_code=503,
                detail="Runtime adapter unavailable",
            ) from exc

    if static_remote_collection_wiring is not None:
        try:
            return await orchestrate_request_with_ordered_static_remote_fallback(
                cluster_request,
                static_remote_collection_wiring.node_registry,
                static_remote_collection_wiring.adapter_registry,
                static_remote_collection_wiring.remote_registry,
                static_remote_collection_wiring.remote_transport,
            )
        except RuntimeAdapterUnavailableError as exc:
            raise HTTPException(
                status_code=503,
                detail="Runtime adapter unavailable",
            ) from exc

    if local_app_composition is None:
        return await handle_static_local_cluster_request(cluster_request)

    return await handle_static_local_cluster_request(
        cluster_request,
        local_app_composition=local_app_composition,
    )


@router.post("/v1/chat", response_model=ClusterResult)
async def chat(request: ChatRequest, http_request: Request) -> ClusterResult:
    automatic_proof_orchestrator = http_request.app.state.automatic_proof_orchestrator
    static_remote_wiring = http_request.app.state.static_remote_wiring
    static_remote_collection_wiring = (
        http_request.app.state.static_remote_collection_wiring
    )
    cluster_request = ClusterRequest(
        messages=request.messages,
        capability=Capability(name=request.capability),
        constraints=(
            RequestConstraints(local_only=False)
            if (
                automatic_proof_orchestrator
                or static_remote_wiring is not None
                or static_remote_collection_wiring is not None
            )
            else RequestConstraints()
        ),
    )

    if automatic_proof_orchestrator:
        return await automatic_proof_orchestrator(cluster_request)

    return await handle_chat_cluster_request(
        cluster_request,
        http_request.app.state.static_remote_proof_wiring,
        static_remote_wiring,
        static_remote_collection_wiring,
        http_request.app.state.local_app_composition,
    )


@router.post("/v1/summarize", response_model=ClusterResult)
async def summarize(http_request: Request) -> ClusterResult:
    """Execute one locally normalized text summarization request."""
    try:
        body = await http_request.json()
        public_request = SummarizePublicRequest.model_validate(body)
        cluster_request = SummarizeRequest(
            text=public_request.text,
            constraints=(
                RequestConstraints(local_only=False)
                if (
                    http_request.app.state.automatic_proof_orchestrator
                    or http_request.app.state.static_remote_wiring is not None
                    or (
                        http_request.app.state.static_remote_collection_wiring
                        is not None
                    )
                )
                else RequestConstraints()
            ),
        )
    except (ValueError, ValidationError):
        raise HTTPException(
            status_code=422,
            detail="Invalid summarize request",
        ) from None

    return await handle_static_local_cluster_request(
        cluster_request,
        local_app_composition=http_request.app.state.local_app_composition,
    )


@router.post("/internal/cluster/request", response_model=ClusterResult)
async def internal_cluster_request(
    http_request: Request,
) -> ClusterResult:
    try:
        envelope = INTERNAL_CLUSTER_REQUEST_ADAPTER.validate_python(
            await http_request.json()
        )
    except (ValueError, ValidationError):
        raise HTTPException(
            status_code=422,
            detail="Invalid internal cluster request",
        ) from None

    request = (
        envelope.request
        if isinstance(envelope, ChatInternalRequest)
        else envelope.request.normalized_request()
    )
    proof_receiving_app_wiring = http_request.app.state.proof_receiving_app_wiring
    if proof_receiving_app_wiring is not None:
        return await handle_static_local_cluster_request(
            request,
            proof_receiving_app_wiring,
        )

    local_app_composition = http_request.app.state.local_app_composition
    if local_app_composition is None:
        return await handle_static_local_cluster_request(request)

    return await handle_static_local_cluster_request(
        request,
        local_app_composition=local_app_composition,
    )


@router.get(
    "/internal/cluster/status",
    response_model=InternalClusterStatusResponse,
)
async def internal_cluster_status(
    http_request: Request,
) -> InternalClusterStatusResponse:
    """Return one completed local runtime observation without cluster collection."""
    try:
        proof_receiving_app_wiring = http_request.app.state.proof_receiving_app_wiring
        if proof_receiving_app_wiring is not None:
            node_registry = proof_receiving_app_wiring.node_registry
            adapter_registry = proof_receiving_app_wiring.adapter_registry
        else:
            node_registry, adapter_registry = _resolve_local_registries(
                http_request.app.state.local_app_composition
            )
        snapshot = project_health_snapshot(node_registry, adapter_registry)
        local_status = project_local_cluster_status(snapshot)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to inspect local runtime status",
        ) from error

    return InternalClusterStatusResponse(runtime_status=local_status.runtime_status)
