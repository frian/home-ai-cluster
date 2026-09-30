"""Explicit RFC-0034 command for one actual routed request account."""

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from typing import Any

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.api.wiring import (
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.execution_intervals import ExecutionIntervalCardinality
from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    RequestConstraints,
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


def create_request(capability: str, message: str) -> ClusterRequest:
    """Construct the one cluster-owned request executed by the command."""
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
    """Execute and explain one request through ordinary ordered fallback."""
    request = create_request(capability, message)
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
        return project_failed_account(
            error.explanation, NO_SELECTABLE_CANDIDATE_FAILURE
        )
    except ExecutionPermissionDeniedError:
        assert lifecycle.selection is not None
        return project_failed_account(
            lifecycle.selection,
            EXECUTION_PERMISSION_DENIED_FAILURE,
            local_execution_permission="denied",
            candidate_consideration="ended",
        )
    except RuntimeAdapterUnavailableError:
        assert lifecycle.selection is not None
        return project_failed_account(
            lifecycle.selection,
            RUNTIME_UNAVAILABLE_FAILURE,
            local_execution_permission="granted",
            candidate_consideration="executed",
        )
    except Exception:
        assert lifecycle.selection is not None
        return project_failed_account(
            lifecycle.selection,
            EXECUTION_FAILED_FAILURE,
            local_execution_permission="granted",
            candidate_consideration="executed",
        )
    assert lifecycle.selection is not None
    account = project_succeeded_account(
        lifecycle.selection,
        node_id=result.node_id,
        adapter=result.adapter,
        model=result.model,
        content=result.content,
    )
    account["lifecycle"] = {
        "candidates": lifecycle.candidates,
        "continuations": lifecycle.continuation_reasons,
        "final_node_id": lifecycle.final_node_id,
    }
    return account


def main(argv: Sequence[str] | None = None) -> None:
    """Run the explicit local actual-request explanation command."""
    args = parse_args(argv)
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
