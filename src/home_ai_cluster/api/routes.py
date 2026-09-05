from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api.chat_external_information_decision import (
    ChatExternalInformationDecisionRequest,
)
from home_ai_cluster.api.client_disconnect import run_routable_execution
from home_ai_cluster.api.wiring import (
    LocalAppComposition,
    StaticRemoteCollectionWiring,
    StaticRemoteWiring,
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.executor import InvalidClassificationLabelError
from home_ai_cluster.core.models import (
    INTERNAL_CLUSTER_REQUEST_ADAPTER,
    Capability,
    ChatInternalRequest,
    ChatMessage,
    ClassifyInternalRequest,
    ClassifyRequest,
    ClassifyResult,
    ClusterRequest,
    ClusterResult,
    InternalClusterStatusResponse,
    RequestConstraints,
    SourceEvidence,
    SourceGroundedChatInternalRequest,
    SourceGroundedChatRequest,
    SourceGroundedChatResult,
    SummarizeRequest,
)
from home_ai_cluster.core.orchestrator import (
    ExecutionPermissionDeniedError,
    NoSelectableRoutingCandidateError,
    orchestrate_composed_request,
    orchestrate_receiver_composed_request,
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


class ClassifyPublicRequest(BaseModel):
    """The deliberately narrow public body for one text classification."""

    text: str
    labels: list[str]


class SourceGroundedChatPublicRequest(BaseModel):
    """The deliberately closed public body for source-grounded Chat."""

    model_config = ConfigDict(extra="forbid")

    question: str
    sources: list[SourceEvidence]


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
    cluster_request: ClusterRequest
    | SummarizeRequest
    | ClassifyRequest
    | SourceGroundedChatRequest,
    local_app_composition: LocalAppComposition | None = None,
    *,
    originating: bool = True,
) -> ClusterResult | ClassifyResult | SourceGroundedChatResult:
    node_registry, adapter_registry = _resolve_local_registries(local_app_composition)

    try:
        if local_app_composition is not None and originating:
            return await orchestrate_composed_request(
                cluster_request,
                node_registry,
                adapter_registry,
                local_app_composition.execution_intervals,
            )
        if local_app_composition is not None:
            return await orchestrate_receiver_composed_request(
                cluster_request,
                node_registry,
                adapter_registry,
                local_app_composition.execution_intervals,
            )
        return await orchestrate_request(
            cluster_request, node_registry, adapter_registry
        )
    except RuntimeAdapterUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Runtime adapter unavailable",
        ) from exc
    except ExecutionPermissionDeniedError as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                "execution permission denied"
                if originating
                else "execution-permission-denied"
            ),
        ) from exc
    except InvalidClassificationLabelError as exc:
        raise HTTPException(status_code=500, detail="execution-failed") from exc
    except NoMatchingAdapterError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"No adapter provides capability: {cluster_request.capability.name}",
        ) from exc


async def handle_chat_cluster_request(
    cluster_request: ClusterRequest | SourceGroundedChatRequest,
    static_remote_wiring: StaticRemoteWiring | None = None,
    static_remote_collection_wiring: StaticRemoteCollectionWiring | None = None,
    local_app_composition: LocalAppComposition | None = None,
) -> ClusterResult | SourceGroundedChatResult:
    """Use ordinary static remote, collection, or local-only wiring."""
    if static_remote_wiring is not None:
        try:
            return await orchestrate_request_with_static_remote_fallback(
                cluster_request,
                static_remote_wiring.node_registry,
                static_remote_wiring.adapter_registry,
                static_remote_wiring.remote_registry,
                static_remote_wiring.remote_transport,
                static_remote_wiring.execution_intervals,
            )
        except (
            RuntimeAdapterUnavailableError,
            NoSelectableRoutingCandidateError,
            ExecutionPermissionDeniedError,
        ) as exc:
            if isinstance(exc, ExecutionPermissionDeniedError):
                raise HTTPException(
                    status_code=409, detail="execution permission denied"
                ) from exc
            if isinstance(exc, NoSelectableRoutingCandidateError):
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "No adapter provides capability: "
                        f"{cluster_request.capability.name}"
                    ),
                ) from exc
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
                static_remote_collection_wiring.execution_intervals,
            )
        except (
            RuntimeAdapterUnavailableError,
            NoSelectableRoutingCandidateError,
            ExecutionPermissionDeniedError,
        ) as exc:
            if isinstance(exc, ExecutionPermissionDeniedError):
                raise HTTPException(
                    status_code=409, detail="execution permission denied"
                ) from exc
            if isinstance(exc, NoSelectableRoutingCandidateError):
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "No adapter provides capability: "
                        f"{cluster_request.capability.name}"
                    ),
                ) from exc
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


async def handle_summarize_cluster_request(
    cluster_request: SummarizeRequest,
    static_remote_wiring: StaticRemoteWiring | None = None,
    static_remote_collection_wiring: StaticRemoteCollectionWiring | None = None,
    local_app_composition: LocalAppComposition | None = None,
) -> ClusterResult:
    """Use existing local-first static remote selection for summarize only."""
    try:
        if static_remote_wiring is not None:
            return await orchestrate_request_with_static_remote_fallback(
                cluster_request,
                static_remote_wiring.node_registry,
                static_remote_wiring.adapter_registry,
                static_remote_wiring.remote_registry,
                static_remote_wiring.remote_transport,
                static_remote_wiring.execution_intervals,
            )
        if static_remote_collection_wiring is not None:
            return await orchestrate_request_with_ordered_static_remote_fallback(
                cluster_request,
                static_remote_collection_wiring.node_registry,
                static_remote_collection_wiring.adapter_registry,
                static_remote_collection_wiring.remote_registry,
                static_remote_collection_wiring.remote_transport,
                static_remote_collection_wiring.execution_intervals,
            )
        return await handle_static_local_cluster_request(
            cluster_request,
            local_app_composition=local_app_composition,
        )
    except (
        RuntimeAdapterUnavailableError,
        NoSelectableRoutingCandidateError,
        ExecutionPermissionDeniedError,
    ) as exc:
        if isinstance(exc, ExecutionPermissionDeniedError):
            raise HTTPException(
                status_code=409, detail="execution permission denied"
            ) from exc
        if isinstance(exc, NoSelectableRoutingCandidateError):
            raise HTTPException(
                status_code=404,
                detail="No adapter provides capability: summarize",
            ) from exc
        raise HTTPException(
            status_code=503,
            detail="Runtime adapter unavailable",
        ) from exc


async def handle_classify_cluster_request(
    cluster_request: ClassifyRequest,
    static_remote_wiring: StaticRemoteWiring | None = None,
    static_remote_collection_wiring: StaticRemoteCollectionWiring | None = None,
    local_app_composition: LocalAppComposition | None = None,
) -> ClassifyResult:
    """Use existing local-first static routing for classification only."""
    try:
        if static_remote_wiring is not None:
            return await orchestrate_request_with_static_remote_fallback(
                cluster_request,
                static_remote_wiring.node_registry,
                static_remote_wiring.adapter_registry,
                static_remote_wiring.remote_registry,
                static_remote_wiring.remote_transport,
                static_remote_wiring.execution_intervals,
            )
        if static_remote_collection_wiring is not None:
            return await orchestrate_request_with_ordered_static_remote_fallback(
                cluster_request,
                static_remote_collection_wiring.node_registry,
                static_remote_collection_wiring.adapter_registry,
                static_remote_collection_wiring.remote_registry,
                static_remote_collection_wiring.remote_transport,
                static_remote_collection_wiring.execution_intervals,
            )
        return await handle_static_local_cluster_request(
            cluster_request,
            local_app_composition=local_app_composition,
        )
    except (
        RuntimeAdapterUnavailableError,
        NoSelectableRoutingCandidateError,
        ExecutionPermissionDeniedError,
    ) as exc:
        if isinstance(exc, ExecutionPermissionDeniedError):
            raise HTTPException(
                status_code=409, detail="execution permission denied"
            ) from exc
        if isinstance(exc, NoSelectableRoutingCandidateError):
            raise HTTPException(
                status_code=404,
                detail="No adapter provides capability: classify",
            ) from exc
        raise HTTPException(
            status_code=503,
            detail="Runtime adapter unavailable",
        ) from exc
    except InvalidClassificationLabelError as exc:
        raise HTTPException(status_code=500, detail="execution-failed") from exc


@router.post("/v1/chat", response_model=ClusterResult)
async def chat(request: ChatRequest, http_request: Request) -> ClusterResult:
    static_remote_wiring = http_request.app.state.static_remote_wiring
    static_remote_collection_wiring = (
        http_request.app.state.static_remote_collection_wiring
    )
    try:
        cluster_request = ClusterRequest(
            messages=request.messages,
            capability=Capability(name=request.capability),
            constraints=(
                RequestConstraints(local_only=False)
                if (
                    static_remote_wiring is not None
                    or static_remote_collection_wiring is not None
                )
                else RequestConstraints()
            ),
        )
    except ValidationError:
        raise HTTPException(status_code=422, detail="Invalid chat request") from None

    return await run_routable_execution(
        http_request,
        lambda: handle_chat_cluster_request(
            cluster_request,
            static_remote_wiring,
            static_remote_collection_wiring,
            http_request.app.state.local_app_composition,
        ),
    )


@router.post("/v1/chat/sources", response_model=SourceGroundedChatResult)
async def source_grounded_chat(
    http_request: Request,
) -> SourceGroundedChatResult:
    """Execute validated source evidence through ordinary Chat routing."""
    static_remote_wiring = http_request.app.state.static_remote_wiring
    static_remote_collection_wiring = (
        http_request.app.state.static_remote_collection_wiring
    )
    try:
        public_request = SourceGroundedChatPublicRequest.model_validate(
            await http_request.json()
        )
        cluster_request = SourceGroundedChatRequest(
            question=public_request.question,
            sources=public_request.sources,
            constraints=(
                RequestConstraints(local_only=False)
                if (
                    static_remote_wiring is not None
                    or static_remote_collection_wiring is not None
                )
                else RequestConstraints()
            ),
        )
    except (ValueError, ValidationError):
        raise HTTPException(
            status_code=422,
            detail="Invalid source-grounded chat request",
        ) from None

    return await run_routable_execution(
        http_request,
        lambda: handle_chat_cluster_request(
            cluster_request,
            static_remote_wiring,
            static_remote_collection_wiring,
            http_request.app.state.local_app_composition,
        ),
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
                    http_request.app.state.static_remote_wiring is not None
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

    return await run_routable_execution(
        http_request,
        lambda: handle_summarize_cluster_request(
            cluster_request,
            http_request.app.state.static_remote_wiring,
            http_request.app.state.static_remote_collection_wiring,
            local_app_composition=http_request.app.state.local_app_composition,
        ),
    )


@router.post("/v1/classify", response_model=ClassifyResult)
async def classify(http_request: Request) -> ClassifyResult:
    """Execute one locally normalized text classification request."""
    try:
        body = await http_request.json()
        public_request = ClassifyPublicRequest.model_validate(body)
        cluster_request = ClassifyRequest(
            text=public_request.text,
            labels=public_request.labels,
            constraints=(
                RequestConstraints(local_only=False)
                if (
                    http_request.app.state.static_remote_wiring is not None
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
            detail="Invalid classify request",
        ) from None

    return await run_routable_execution(
        http_request,
        lambda: handle_classify_cluster_request(
            cluster_request,
            http_request.app.state.static_remote_wiring,
            http_request.app.state.static_remote_collection_wiring,
            local_app_composition=http_request.app.state.local_app_composition,
        ),
    )


@router.post(
    "/internal/chat/external-information-decision",
    response_model=ClassifyResult,
)
async def chat_external_information_decision(
    http_request: Request,
) -> ClassifyResult:
    """Execute the fixed RFC-0096 decision only on caller-local Classify."""
    try:
        decision = ChatExternalInformationDecisionRequest.model_validate(
            await http_request.json()
        )
    except (ValueError, ValidationError):
        raise HTTPException(
            status_code=422,
            detail="Invalid chat external-information decision request",
        ) from None

    return await run_routable_execution(
        http_request,
        lambda: handle_static_local_cluster_request(
            decision.classify_request(),
            local_app_composition=http_request.app.state.local_app_composition,
        ),
    )


@router.post(
    "/internal/cluster/request",
    response_model=ClusterResult | ClassifyResult | SourceGroundedChatResult,
)
async def internal_cluster_request(
    http_request: Request,
) -> ClusterResult | ClassifyResult | SourceGroundedChatResult:
    try:
        envelope = INTERNAL_CLUSTER_REQUEST_ADAPTER.validate_python(
            await http_request.json()
        )
    except (ValueError, ValidationError):
        raise HTTPException(
            status_code=422,
            detail="Invalid internal cluster request",
        ) from None

    if isinstance(envelope, ChatInternalRequest):
        request = envelope.request
    elif isinstance(envelope, ClassifyInternalRequest):
        request = envelope.request.normalized_request()
    elif isinstance(envelope, SourceGroundedChatInternalRequest):
        request = envelope.request.normalized_request()
    else:
        request = envelope.request.normalized_request()
    local_app_composition = http_request.app.state.local_app_composition
    if local_app_composition is None:
        return await run_routable_execution(
            http_request,
            lambda: handle_static_local_cluster_request(request),
        )

    return await run_routable_execution(
        http_request,
        lambda: handle_static_local_cluster_request(
            request,
            local_app_composition=local_app_composition,
            originating=False,
        ),
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
