"""Explicit RFC-0032 command for one actual routed request."""

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
from home_ai_cluster.core.models import (
    Capability,
    ChatMessage,
    ClusterRequest,
    RequestConstraints,
)
from home_ai_cluster.core.orchestrator import (
    AutomaticCapabilityRoutingOutcome,
    NoSelectableRoutingCandidateError,
    orchestrate_request_with_automatic_capability_explanation,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclarationRegistry,
    build_remote_node_declaration_registry,
)


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
    return parser.parse_args(argv)


def create_request(capability: str, message: str) -> ClusterRequest:
    """Construct the one cluster-owned request executed by the command."""
    return ClusterRequest(
        messages=[ChatMessage(role="user", content=message)],
        capability=Capability(name=capability),
        constraints=RequestConstraints(),
    )


def _candidate_families(*, local: bool, declared_remote: bool) -> list[str]:
    return [
        family
        for family, present in (("local", local), ("declared-remote", declared_remote))
        if present
    ]


def project_outcome(outcome: AutomaticCapabilityRoutingOutcome) -> dict[str, Any]:
    """Project one request-scoped outcome to the accepted RFC-0032 JSON shape."""
    explanation = outcome.explanation
    outcome_rule = str(explanation.outcome_rule)
    selected_candidate_family = None
    if outcome_rule in {"local-only", "local-precedence"}:
        selected_candidate_family = "local"
    elif outcome_rule == "declared-remote-only":
        selected_candidate_family = "declared-remote"

    return {
        "routing": {
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
        },
        "result": {
            "node_id": outcome.result.node_id,
            "adapter": outcome.result.adapter,
            "model": outcome.result.model,
            "content": outcome.result.content,
        },
    }


async def evaluate_actual_request(
    capability: str,
    message: str,
    *,
    node_registry: NodeRegistry | None = None,
    adapter_registry: AdapterRegistry | None = None,
    remote_registry: RemoteNodeDeclarationRegistry | None = None,
) -> dict[str, Any]:
    """Execute exactly one automatic selection and return its successful account."""
    request = create_request(capability, message)
    outcome = await orchestrate_request_with_automatic_capability_explanation(
        request,
        node_registry or create_static_local_node_registry(),
        adapter_registry or create_static_runtime_adapter_registry(),
        remote_registry or build_remote_node_declaration_registry([]),
    )
    return project_outcome(outcome)


def main(argv: Sequence[str] | None = None) -> None:
    """Run the explicit local actual-request explanation command."""
    args = parse_args(argv)
    try:
        projection = asyncio.run(
            evaluate_actual_request(args.capability, args.message)
        )
    except NoSelectableRoutingCandidateError as error:
        print("error: no selectable routing candidate", file=sys.stderr)
        raise SystemExit(1) from error
    except RuntimeAdapterUnavailableError as error:
        print("error: runtime adapter unavailable", file=sys.stderr)
        raise SystemExit(1) from error
    except Exception as error:
        print("error: unable to execute explained request", file=sys.stderr)
        raise SystemExit(1) from error

    print(json.dumps(projection))
