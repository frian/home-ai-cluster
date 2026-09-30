"""Explicit RFC-0034 command for one actual routed request account."""

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from typing import Any

from home_ai_cluster import local_runtime, static_cluster
from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api.wiring import (
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.execution_intervals import ExecutionIntervalCardinality
from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClassifyResult,
    ClusterRequest,
    ClusterResult,
    ImageGenerationRequest,
    ImageGenerationResult,
    RemoteTransportRequest,
    RemoteTransportResult,
    RequestConstraints,
    SummarizeRequest,
)
from home_ai_cluster.core.orchestrator import (
    ExecutionPermissionDeniedError,
    NoSelectableRoutingCandidateError,
)
from home_ai_cluster.core.ordered_remote_fallback import (
    orchestrate_request_with_ordered_static_remote_fallback,
)
from home_ai_cluster.core.ordinary_request_lifecycle import OrdinaryRequestLifecycle
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclarationRegistry,
    build_remote_node_declaration_registry,
)
from home_ai_cluster.core.remote_transport import RemoteTransport
from home_ai_cluster.core.routing_candidates import (
    AutomaticCapabilitySelectionExplanation,
)
from home_ai_cluster.request_history import record_account
from home_ai_cluster.retained_configuration import load_retained_configuration

NO_SELECTABLE_CANDIDATE_FAILURE = {
    "status": "no-selectable-candidate",
    "reason": "no selectable routing candidate",
}
RUNTIME_UNAVAILABLE_FAILURE = {
    "status": "runtime-unavailable",
    "reason": "selected runtime adapter unavailable",
}
EXECUTION_FAILED_FAILURE = {
    "status": "execution-failed",
    "reason": "selected candidate execution failed",
}
EXECUTION_PERMISSION_DENIED_FAILURE = {
    "status": "execution-permission-denied",
    "reason": "execution permission denied",
}
INTERNAL_FAILURE_MESSAGE = "error: unable to construct actual request account"
HISTORY_RECORDING_WARNING = "warning: unable to record request history"


def non_empty_value(value: str) -> str:
    """Validate one non-empty command value without changing its content."""
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse one explicit actual-request explanation invocation."""
    parser = argparse.ArgumentParser(prog="home-ai-cluster-explain-request")
    parser.add_argument("--capability", required=True, type=non_empty_value)
    parser.add_argument("--message", required=True, type=non_empty_value)
    parser.add_argument("--record-history", action="store_true")
    return parser.parse_args(argv)


def create_request(capability: str, message: str) -> RemoteTransportRequest:
    """Construct only request shapes determined by the existing message input."""
    if capability == "classify":
        raise ValueError("classification requires operator-supplied labels")
    if capability == "summarize":
        return SummarizeRequest(
            text=message, constraints=RequestConstraints(local_only=False)
        )
    if capability == "image-generation":
        return ImageGenerationRequest(
            instruction=message, constraints=RequestConstraints(local_only=False)
        )
    return ClusterRequest(
        messages=[ChatMessage(role="user", content=message)],
        capability=Capability(name=capability),
        constraints=RequestConstraints(local_only=False),
    )


def _candidate_families(*, local: bool, declared_remote: bool) -> list[str]:
    return [
        family
        for family, present in (("local", local), ("declared-remote", declared_remote))
        if present
    ]


def project_routing(
    explanation: AutomaticCapabilitySelectionExplanation,
    *,
    local_execution_permission: str = "not-applicable",
    candidate_consideration: str = "not-started",
) -> dict[str, Any]:
    """Project the existing eight-field automatic selection explanation."""
    outcome_rule = str(explanation.outcome_rule)
    selected_candidate_family = None
    if outcome_rule in {"local-only", "local-precedence"}:
        selected_candidate_family = "local"
    elif outcome_rule == "declared-remote-only":
        selected_candidate_family = "declared-remote"

    return {
        "requested_capability": explanation.requested_capability_name,
        "matched_candidate_families": _candidate_families(
            local=explanation.local_matched,
            declared_remote=explanation.declared_remote_matched,
        ),
        "selectable_candidate_families": _candidate_families(
            local=explanation.local_selectable,
            declared_remote=explanation.declared_remote_selectable,
        ),
        "excluded_candidate_families": _candidate_families(
            local=False,
            declared_remote=explanation.local_only_excluded_declared_remote,
        ),
        "selected_candidate_family": selected_candidate_family,
        "selected_node_id": explanation.selected_node_id,
        "outcome_rule": outcome_rule,
        "failure_reason": (
            str(explanation.no_selectable_candidate_reason)
            if explanation.no_selectable_candidate_reason is not None
            else None
        ),
        "local_execution_permission": local_execution_permission,
        "candidate_consideration": candidate_consideration,
    }


def project_succeeded_account(
    explanation: AutomaticCapabilitySelectionExplanation,
    *,
    node_id: str,
    adapter: str,
    model: str | None,
    content: str,
    local_execution_permission: str = "granted",
    candidate_consideration: str = "executed",
) -> dict[str, Any]:
    """Project one successful RFC-0034 account."""
    return {
        "status": "succeeded",
        "routing": project_routing(
            explanation,
            local_execution_permission=local_execution_permission,
            candidate_consideration=candidate_consideration,
        ),
        "result": {
            "node_id": node_id,
            "adapter": adapter,
            "model": model,
            "content": content,
        },
        "failure": None,
    }


def project_failed_account(
    explanation: AutomaticCapabilitySelectionExplanation,
    failure: dict[str, str],
    *,
    local_execution_permission: str = "not-applicable",
    candidate_consideration: str = "ended",
) -> dict[str, Any]:
    """Project one safely classified RFC-0034 failed account."""
    return {
        "status": "failed",
        "routing": project_routing(
            explanation,
            local_execution_permission=local_execution_permission,
            candidate_consideration=candidate_consideration,
        ),
        "result": None,
        "failure": failure,
    }


def _with_lifecycle(
    account: dict[str, Any], lifecycle: OrdinaryRequestLifecycle
) -> dict[str, Any]:
    account["lifecycle"] = {
        "candidates": lifecycle.candidates,
        "continuations": lifecycle.continuation_reasons,
        "final_node_id": lifecycle.final_node_id,
    }
    return account


def _lifecycle_routing_values(lifecycle: OrdinaryRequestLifecycle) -> dict[str, str]:
    """Project existing RFC-0034 fields from same-request lifecycle facts."""
    facts = lifecycle.candidates
    permission = (
        "denied"
        if any(f["fact"] == "execution-permission-denied" for f in facts)
        else "granted"
        if any(f["fact"] == "execution-permission-granted" for f in facts)
        else "not-applicable"
    )
    local_candidate_reached_adapter = any(
        fact["family"] == "local" and fact["fact"] == "adapter-invoked"
        for fact in facts
    )
    remote_candidate_reached_transport = any(
        fact["family"] == "declared-remote" and fact["fact"] == "transport-invoked"
        for fact in facts
    )
    consideration = (
        "executed"
        if local_candidate_reached_adapter
        or (
            not any(fact["family"] == "local" for fact in facts)
            and remote_candidate_reached_transport
        )
        else "ended"
    )
    return {
        "local_execution_permission": permission,
        "candidate_consideration": consideration,
    }


def _project_result(result: RemoteTransportResult) -> dict[str, Any]:
    """Project only bounded fields owned by each existing result shape."""
    if isinstance(result, ClusterResult):
        return {
            "node_id": result.node_id,
            "adapter": result.adapter,
            "model": result.model,
            "content": result.content,
        }
    if isinstance(result, (ClassifyResult, ImageGenerationResult)):
        return {"node_id": result.node_id}
    raise TypeError("unsupported explained result")


async def _evaluate_actual_request(
    request: RemoteTransportRequest,
    *,
    node_registry: NodeRegistry | None = None,
    adapter_registry: AdapterRegistry | None = None,
    remote_registry: RemoteNodeDeclarationRegistry | None = None,
    remote_transport: RemoteTransport | None = None,
    execution_intervals: ExecutionIntervalCardinality | None = None,
) -> dict[str, Any]:
    """Execute and explain one request through ordinary ordered fallback."""
    nodes = (
        node_registry
        if node_registry is not None
        else create_static_local_node_registry()
    )
    adapters = (
        adapter_registry
        if adapter_registry is not None
        else create_static_runtime_adapter_registry()
    )
    remotes = (
        remote_registry
        if remote_registry is not None
        else build_remote_node_declaration_registry([])
    )
    intervals = execution_intervals or ExecutionIntervalCardinality()
    lifecycle = OrdinaryRequestLifecycle()
    if remote_transport is None:

        class NoRemoteTransport:
            async def send(self, request: object, declaration: object) -> object:
                raise RuntimeAdapterUnavailableError("remote transport unavailable")

        remote_transport = NoRemoteTransport()  # type: ignore[assignment]
    try:
        result = await orchestrate_request_with_ordered_static_remote_fallback(
            request, nodes, adapters, remotes, remote_transport, intervals, lifecycle
        )
    except NoSelectableRoutingCandidateError as error:
        return _with_lifecycle(
            project_failed_account(error.explanation, NO_SELECTABLE_CANDIDATE_FAILURE),
            lifecycle,
        )
    except ExecutionPermissionDeniedError:
        assert lifecycle.selection is not None
        return _with_lifecycle(
            project_failed_account(
                lifecycle.selection,
                EXECUTION_PERMISSION_DENIED_FAILURE,
                **_lifecycle_routing_values(lifecycle),
            ),
            lifecycle,
        )
    except RuntimeAdapterUnavailableError:
        assert lifecycle.selection is not None
        return _with_lifecycle(
            project_failed_account(
                lifecycle.selection,
                RUNTIME_UNAVAILABLE_FAILURE,
                **_lifecycle_routing_values(lifecycle),
            ),
            lifecycle,
        )
    except Exception:
        assert lifecycle.selection is not None
        return _with_lifecycle(
            project_failed_account(
                lifecycle.selection,
                EXECUTION_FAILED_FAILURE,
                **_lifecycle_routing_values(lifecycle),
            ),
            lifecycle,
        )
    assert lifecycle.selection is not None
    return _with_lifecycle(
        {
            "status": "succeeded",
            "routing": project_routing(
                lifecycle.selection, **_lifecycle_routing_values(lifecycle)
            ),
            "result": _project_result(result),
            "failure": None,
        },
        lifecycle,
    )


async def _evaluate_ordinary_request(
    request: RemoteTransportRequest,
    *,
    node_registry: NodeRegistry | None = None,
    adapter_registry: AdapterRegistry | None = None,
    remote_registry: RemoteNodeDeclarationRegistry | None = None,
    remote_transport: RemoteTransport | None = None,
    execution_intervals: ExecutionIntervalCardinality | None = None,
) -> dict[str, Any]:
    """Execute one explained request through its own ordinary composition."""
    injected_dependencies = any(
        dependency is not None
        for dependency in (
            node_registry,
            adapter_registry,
            remote_registry,
            remote_transport,
            execution_intervals,
        )
    )
    if injected_dependencies:
        return await _evaluate_actual_request(
            request,
            node_registry=node_registry,
            adapter_registry=adapter_registry,
            remote_registry=remote_registry,
            remote_transport=remote_transport,
            execution_intervals=execution_intervals,
        )

    retained = load_retained_configuration()
    local_app = local_runtime.create_local_runtime_app(local_runtime.parse_args([]))
    process_client = static_cluster.create_static_cluster_http_client()
    try:
        effective = static_cluster._compose_effective_ordinary_request_wiring(
            local_app_composition=local_app.state.local_app_composition,
            remote_nodes=retained.remote_nodes,
            caller_local_capabilities=(
                retained.local.local_capabilities
                if retained.local is not None
                and retained.local.local_capabilities is not None
                else static_cluster.DEFAULT_STATIC_CAPABILITY_NAMES
            ),
            client=process_client,
        )
        return await _evaluate_actual_request(
            request,
            node_registry=effective.node_registry,
            adapter_registry=effective.adapter_registry,
            remote_registry=effective.remote_registry,
            remote_transport=effective.remote_transport,
            execution_intervals=effective.execution_intervals,
        )
    finally:
        await process_client.aclose()


async def evaluate_actual_request(
    capability: str,
    message: str,
    *,
    node_registry: NodeRegistry | None = None,
    adapter_registry: AdapterRegistry | None = None,
    remote_registry: RemoteNodeDeclarationRegistry | None = None,
    remote_transport: RemoteTransport | None = None,
    execution_intervals: ExecutionIntervalCardinality | None = None,
) -> dict[str, Any]:
    """Explain one request expressible by the existing public message input."""
    return await _evaluate_ordinary_request(
        create_request(capability, message),
        node_registry=node_registry,
        adapter_registry=adapter_registry,
        remote_registry=remote_registry,
        remote_transport=remote_transport,
        execution_intervals=execution_intervals,
    )


def main(argv: Sequence[str] | None = None) -> None:
    """Run the explicit local actual-request explanation command."""
    args = parse_args(argv)
    if args.capability == "classify":
        print("error: classify explanation requires labels", file=sys.stderr)
        raise SystemExit(2)
    try:
        account = asyncio.run(evaluate_actual_request(args.capability, args.message))
    except Exception as error:
        print(INTERNAL_FAILURE_MESSAGE, file=sys.stderr)
        raise SystemExit(1) from error

    if args.record_history:
        try:
            record_account(account)
        except Exception:
            print(HISTORY_RECORDING_WARNING, file=sys.stderr)

    print(json.dumps(account, separators=(",", ":")))
    if account["status"] == "failed":
        raise SystemExit(1)
