"""Helpers for resolving execution targets after routing."""

from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.router import RoutingDecision


def remote_declaration_for_routing_decision(
    decision: RoutingDecision,
    remote_registry: RemoteNodeDeclarationRegistry,
) -> RemoteNodeDeclaration | None:
    """Return the remote declaration matching the selected node id."""
    return remote_registry.declaration_for_node_id(decision.node.id)
