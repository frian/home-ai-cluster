"""Explicit RFC-0027 routing explanation command without execution."""

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from home_ai_cluster.adapters.base import RuntimeAdapter
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    NodeDescription,
    NodeHealth,
    RequestConstraints,
    RuntimeResult,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    build_remote_node_declaration_registry,
)
from home_ai_cluster.core.routing_candidates import (
    AutomaticCapabilitySelection,
    RoutingCandidates,
    routing_candidates_for_request,
    select_automatic_capability_routing_candidate,
)

LOCAL_NODE_ID = "local"
DECLARED_REMOTE_NODE_ID = "declared-remote"
LOCAL_ADAPTER_NAME = "routing-explanation"
EXPLANATION_MESSAGE_CONTENT = "Routing explanation"
# ClusterRequest currently requires one ChatMessage. This placeholder is not
# operator input, is not used for selection, and is never returned in output.


class ExplanationOnlyAdapter(RuntimeAdapter):
    """Static adapter metadata used only to discover a local candidate."""

    def __init__(self, capability: Capability) -> None:
        self._capability = capability

    @property
    def name(self) -> str:
        return LOCAL_ADAPTER_NAME

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [self._capability]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        raise RuntimeError("routing explanation adapter is not executable")


def capability_name(value: str) -> str:
    """Validate one non-empty capability name for the explanation request."""
    if not value.strip():
        raise argparse.ArgumentTypeError("capability must not be empty")
    return value


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse one explicit routing-explanation request."""
    parser = argparse.ArgumentParser(prog="home-ai-cluster-explain-routing")
    parser.add_argument("--capability", required=True, type=capability_name)
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--declared-remote", action="store_true")
    return parser.parse_args(argv)


def create_request(capability: str, *, local_only: bool) -> ClusterRequest:
    """Construct the one request evaluated by the explicit command."""
    return ClusterRequest(
        messages=[ChatMessage(role="user", content=EXPLANATION_MESSAGE_CONTENT)],
        capability=Capability(name=capability),
        constraints=RequestConstraints(local_only=local_only),
    )


def create_local_node(capability: Capability) -> NodeDescription:
    """Create one static local candidate declaration for this invocation."""
    return NodeDescription(
        id=LOCAL_NODE_ID,
        name="Local explanation node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[capability],
        adapters=[LOCAL_ADAPTER_NAME],
    )


def create_declared_remote(capability: Capability) -> RemoteNodeDeclaration:
    """Create one static declaration without a usable execution address."""
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id=DECLARED_REMOTE_NODE_ID,
            name="Declared remote explanation node",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[capability],
            adapters=["declared-remote"],
        ),
        transport_address="not-used-for-routing-explanation",
    )


def discover_and_select(
    request: ClusterRequest,
    *,
    include_local: bool,
    include_declared_remote: bool,
    local_adapter: RuntimeAdapter | None = None,
) -> AutomaticCapabilitySelection:
    """Reuse RFC-0025 discovery and selection without entering execution."""
    adapter = local_adapter or ExplanationOnlyAdapter(request.capability)
    node_registry = NodeRegistry(
        [create_local_node(request.capability)] if include_local else []
    )
    adapter_registry = AdapterRegistry([adapter] if include_local else [])
    remote_registry = build_remote_node_declaration_registry(
        [create_declared_remote(request.capability)] if include_declared_remote else []
    )
    candidates: RoutingCandidates = routing_candidates_for_request(
        request,
        node_registry,
        adapter_registry,
        remote_registry,
    )
    return select_automatic_capability_routing_candidate(request, candidates)


def project_explanation(selection: AutomaticCapabilitySelection) -> dict[str, Any]:
    """Project RFC-0025 facts to the stable RFC-0027 JSON object."""
    explanation = selection.explanation
    matched_candidate_families = _candidate_families(
        local=explanation.local_matched,
        declared_remote=explanation.declared_remote_matched,
    )
    selectable_candidate_families = _candidate_families(
        local=explanation.local_selectable,
        declared_remote=explanation.declared_remote_selectable,
    )
    excluded_candidate_families = _candidate_families(
        local=False,
        declared_remote=explanation.local_only_excluded_declared_remote,
    )
    selected_candidate_family = None
    if selection.selected is not None:
        selected_candidate_family = (
            "local" if selection.selected.local is not None else "declared-remote"
        )

    return {
        "requested_capability": explanation.requested_capability_name,
        "matched_candidate_families": matched_candidate_families,
        "selectable_candidate_families": selectable_candidate_families,
        "excluded_candidate_families": excluded_candidate_families,
        "selected_candidate_family": selected_candidate_family,
        "selected_node_id": explanation.selected_node_id,
        "outcome_rule": str(explanation.outcome_rule),
        "failure_reason": (
            str(explanation.no_selectable_candidate_reason)
            if explanation.no_selectable_candidate_reason is not None
            else None
        ),
    }


def _candidate_families(*, local: bool, declared_remote: bool) -> list[str]:
    """Return candidate families in the RFC-0027 deterministic order."""
    return [
        family
        for family, present in (("local", local), ("declared-remote", declared_remote))
        if present
    ]


def evaluate_explanation(
    capability: str,
    *,
    local_only: bool,
    include_local: bool,
    include_declared_remote: bool,
) -> dict[str, Any]:
    """Evaluate one explanation-only request and return its JSON projection."""
    request = create_request(capability, local_only=local_only)
    selection = discover_and_select(
        request,
        include_local=include_local,
        include_declared_remote=include_declared_remote,
    )
    return project_explanation(selection)


def main(argv: Sequence[str] | None = None) -> None:
    """Run the explicit local routing-explanation command."""
    args = parse_args(argv)
    try:
        explanation = evaluate_explanation(
            args.capability,
            local_only=args.local_only,
            include_local=args.local,
            include_declared_remote=args.declared_remote,
        )
    except Exception as error:
        print(
            f"error: unable to evaluate routing explanation: {error}", file=sys.stderr
        )
        raise SystemExit(1) from error

    print(json.dumps(explanation))
