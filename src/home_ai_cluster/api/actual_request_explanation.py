"""Effectful, request-scoped explanation on the ordinary loopback authority."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api.client_disconnect import (
    ConfirmedClientDisconnect,
    run_routable_execution,
)
from home_ai_cluster.core.execution_intervals import ExecutionPermissionDeniedError
from home_ai_cluster.core.models import (
    Capability,
    ClassifyRequest,
    ClassifyResult,
    ClusterRequest,
    ClusterResult,
    RequestConstraints,
    SummarizeRequest,
)
from home_ai_cluster.core.orchestrator import (
    NoSelectableRoutingCandidateError,
    orchestrate_composed_request,
    orchestrate_request_with_static_remote_fallback,
)
from home_ai_cluster.core.ordered_remote_fallback import (
    orchestrate_request_with_ordered_static_remote_fallback,
)
from home_ai_cluster.core.ordinary_request_lifecycle import OrdinaryRequestLifecycle
from home_ai_cluster.core.router import NoMatchingAdapterError
from home_ai_cluster.core.routing_candidates import (
    AutomaticCapabilitySelectionOutcomeRule,
)

router = APIRouter()


class _ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Message(_ClosedModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class _Messages(_ClosedModel):
    messages: list[_Message] = Field(min_length=1)
    capability: Literal["chat", "code"]


class _Summarize(_ClosedModel):
    text: str


class _Classify(_ClosedModel):
    text: str
    labels: list[str]


class _Carrier(_ClosedModel):
    kind: Literal["chat", "summarize", "classify", "code"]
    local_only: StrictBool
    request: dict[str, object]


def _normalized_request(
    body: _Carrier,
) -> ClusterRequest | SummarizeRequest | ClassifyRequest:
    constraints = RequestConstraints(local_only=body.local_only)
    if body.kind in {"chat", "code"}:
        supplied = _Messages.model_validate(body.request)
        if supplied.capability != body.kind:
            raise ValueError("capability does not match kind")
        return ClusterRequest(
            messages=[message.model_dump() for message in supplied.messages],
            capability=Capability(name=body.kind),
            constraints=constraints,
        )
    if body.kind == "summarize":
        supplied = _Summarize.model_validate(body.request)
        return SummarizeRequest(text=supplied.text, constraints=constraints)
    supplied = _Classify.model_validate(body.request)
    return ClassifyRequest(
        text=supplied.text, labels=supplied.labels, constraints=constraints
    )


_FACTS = {
    "local": {
        "execution-permission-granted",
        "execution-permission-denied",
        "adapter-invoked",
    },
    "declared-remote": {"transport-invoked", "execution-permission-refused"},
}
_REASONS = {
    "local-execution-permission-denied": ("local", "execution-permission-denied"),
    "local-runtime-connection-unavailable-before-request": ("local", "adapter-invoked"),
    "remote-runtime-connection-unavailable-before-request": (
        "declared-remote",
        "transport-invoked",
    ),
    "remote-execution-permission-refused": (
        "declared-remote",
        "execution-permission-refused",
    ),
}


def _explanation(
    request: ClusterRequest | SummarizeRequest | ClassifyRequest,
    lifecycle: OrdinaryRequestLifecycle,
    *,
    succeeded: bool,
) -> dict[str, object]:
    initial: dict[str, str] | None = None
    if lifecycle.local_initial_selection:
        if lifecycle.selection is not None:
            raise ValueError("contradictory selection")
        initial = {"kind": "local"}
    elif lifecycle.selection is not None:
        selection = lifecycle.selection
        if selection.requested_capability_name != request.capability.name:
            raise ValueError("wrong selected capability")
        if selection.outcome_rule in {
            AutomaticCapabilitySelectionOutcomeRule.LOCAL_ONLY,
            AutomaticCapabilitySelectionOutcomeRule.LOCAL_PRECEDENCE,
        }:
            if not selection.selected_node_id:
                raise ValueError("missing local selection")
            initial = {"kind": "local"}
        elif (
            selection.outcome_rule
            == AutomaticCapabilitySelectionOutcomeRule.DECLARED_REMOTE_ONLY
        ):
            if not selection.selected_node_id:
                raise ValueError("missing remote selection")
            initial = {"kind": "declared_remote", "node_id": selection.selected_node_id}
        elif (
            selection.outcome_rule
            != AutomaticCapabilitySelectionOutcomeRule.NO_SELECTABLE_CANDIDATE
        ):
            raise ValueError("unsupported selection")
        elif selection.selected_node_id is not None:
            raise ValueError("contradictory no-selection")

    facts: set[tuple[str, str, str]] = set()
    fact_positions: dict[tuple[str, str, str], int] = {}
    completed_candidates: set[tuple[str, str]] = set()
    current_candidate: tuple[str, str] | None = None
    for index, item in enumerate(lifecycle.candidates):
        if set(item) != {"family", "node_id", "fact"}:
            raise ValueError("invalid fact shape")
        family, node_id, fact = item["family"], item["node_id"], item["fact"]
        if not node_id or fact not in _FACTS.get(family, set()):
            raise ValueError("invalid fact")
        candidate = (family, node_id)
        if candidate != current_candidate:
            if candidate in completed_candidates:
                raise ValueError("candidate resumed after progression")
            if current_candidate is not None:
                completed_candidates.add(current_candidate)
            current_candidate = candidate
        key = (family, node_id, fact)
        if key in facts:
            raise ValueError("duplicate fact")
        facts.add(key)
        fact_positions[key] = index

    for family, node_id, _ in facts:
        if family == "local":
            if (family, node_id, "execution-permission-denied") in facts and (
                family,
                node_id,
                "execution-permission-granted",
            ) in facts:
                raise ValueError("contradictory local permission")
            if (family, node_id, "execution-permission-denied") in facts and (
                family,
                node_id,
                "adapter-invoked",
            ) in facts:
                raise ValueError("denied local adapter invocation")
            if (
                (family, node_id, "adapter-invoked") in facts
                and (family, node_id, "execution-permission-granted") in facts
                and fact_positions[(family, node_id, "execution-permission-granted")]
                > fact_positions[(family, node_id, "adapter-invoked")]
            ):
                raise ValueError("local fact order")
        elif (family, node_id, "execution-permission-refused") in facts and (
            (family, node_id, "transport-invoked") not in facts
            or fact_positions[(family, node_id, "transport-invoked")]
            > fact_positions[(family, node_id, "execution-permission-refused")]
        ):
            raise ValueError("remote fact order")

    if len(lifecycle.continuation_reasons) != len(lifecycle.continuation_fact_counts):
        raise ValueError("unpaired continuation")
    seen_continuations: set[tuple[str, str]] = set()
    previous_count = 0
    for item, count in zip(
        lifecycle.continuation_reasons, lifecycle.continuation_fact_counts, strict=True
    ):
        if set(item) != {"node_id", "reason"}:
            raise ValueError("invalid continuation shape")
        node_id, reason = item["node_id"], item["reason"]
        if (
            not node_id
            or reason not in _REASONS
            or (node_id, reason) in seen_continuations
        ):
            raise ValueError("invalid continuation")
        seen_continuations.add((node_id, reason))
        family, required = _REASONS[reason]
        position = fact_positions.get((family, node_id, required))
        if position is None or position >= count:
            raise ValueError("continuation without establishing fact")
        if count <= previous_count or count >= len(lifecycle.candidates):
            raise ValueError("continuation without later candidate")
        next_fact = lifecycle.candidates[count]
        if (next_fact["family"], next_fact["node_id"]) == (family, node_id):
            raise ValueError("continuation did not advance")
        previous_count = count
        if (
            reason == "remote-execution-permission-refused"
            and (family, node_id, "transport-invoked") not in facts
        ):
            raise ValueError("refusal without transport")

    if succeeded != (lifecycle.final_node_id is not None):
        raise ValueError("invalid final attribution")
    if lifecycle.final_node_id == "":
        raise ValueError("empty final attribution")
    if initial is None and lifecycle.candidates:
        raise ValueError("facts without selected candidate")
    if initial is not None and lifecycle.candidates:
        first = lifecycle.candidates[0]
        expected_family = "local" if initial["kind"] == "local" else "declared-remote"
        if first["family"] != expected_family or (
            initial["kind"] == "declared_remote"
            and first["node_id"] != initial["node_id"]
        ):
            raise ValueError("facts do not match selection")
    if lifecycle.final_node_id is not None and not any(
        item["node_id"] == lifecycle.final_node_id
        and item["fact"] in {"adapter-invoked", "transport-invoked"}
        for item in lifecycle.candidates
    ):
        raise ValueError("final node was not invoked")
    return {
        "requested_capability": request.capability.name,
        "local_only": request.constraints.local_only,
        "initial_selection": initial,
        "candidate_facts": lifecycle.candidates,
        "continuations": lifecycle.continuation_reasons,
        "final_node_id": lifecycle.final_node_id,
    }


def _failure_status(exc: Exception) -> str:
    if isinstance(exc, (NoSelectableRoutingCandidateError, NoMatchingAdapterError)):
        return "no-selectable-candidate"
    if isinstance(exc, ExecutionPermissionDeniedError):
        return "execution-permission-denied"
    if isinstance(exc, RuntimeAdapterUnavailableError):
        return "runtime-unavailable"
    return "execution-failed"


@router.post("/diagnostics/actual-request-explanation")
async def actual_request_explanation(http_request: Request) -> dict[str, object]:
    try:
        body = _Carrier.model_validate(await http_request.json())
        ordinary_request = _normalized_request(body)
    except (ValueError, ValidationError):
        raise HTTPException(
            status_code=422, detail="Invalid diagnostic input"
        ) from None

    state = http_request.app.state
    single = getattr(state, "static_remote_wiring", None)
    ordered = getattr(state, "static_remote_collection_wiring", None)
    local = getattr(state, "local_app_composition", None)
    if (single is not None and ordered is not None) or (
        single is None and ordered is None and local is None
    ):
        raise HTTPException(
            status_code=503, detail="Active request explanation unavailable"
        )
    active = single or ordered or local
    if any(
        getattr(active, name, None) is None
        for name in ("node_registry", "adapter_registry", "execution_intervals")
    ) or (
        (single is not None or ordered is not None)
        and any(
            getattr(active, name, None) is None
            for name in ("remote_registry", "remote_transport")
        )
    ):
        raise HTTPException(
            status_code=503, detail="Active request explanation unavailable"
        )

    lifecycle = OrdinaryRequestLifecycle()

    async def execute():
        if single is not None:
            return await orchestrate_request_with_static_remote_fallback(
                ordinary_request,
                single.node_registry,
                single.adapter_registry,
                single.remote_registry,
                single.remote_transport,
                single.execution_intervals,
                lifecycle,
            )
        if ordered is not None:
            return await orchestrate_request_with_ordered_static_remote_fallback(
                ordinary_request,
                ordered.node_registry,
                ordered.adapter_registry,
                ordered.remote_registry,
                ordered.remote_transport,
                ordered.execution_intervals,
                lifecycle,
            )
        return await orchestrate_composed_request(
            ordinary_request,
            local.node_registry,
            local.adapter_registry,
            local.execution_intervals,
            lifecycle,
        )

    result: ClusterResult | ClassifyResult | None = None
    failure: dict[str, str] | None = None
    try:
        result = await run_routable_execution(http_request, execute)
    except ConfirmedClientDisconnect:
        raise
    except Exception as exc:
        # Cancellation is a BaseException-owned HTTP boundary and is not caught here.
        failure = {"status": _failure_status(exc)}

    try:
        if result is not None and not isinstance(
            result, (ClusterResult, ClassifyResult)
        ):
            raise ValueError("unexpected result family")
        if result is None and failure is None:
            raise ValueError("missing completed outcome")
        if result is not None and result.node_id != lifecycle.final_node_id:
            raise ValueError("incorrect final attribution")
        explanation = _explanation(
            ordinary_request, lifecycle, succeeded=result is not None
        )
        return {
            "status": "succeeded" if result is not None else "failed",
            "result": result.model_dump() if result is not None else None,
            "failure": failure,
            "explanation": explanation,
        }
    except Exception:
        raise HTTPException(
            status_code=500, detail="Request explanation failed"
        ) from None
