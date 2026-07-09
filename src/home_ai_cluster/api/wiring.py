"""Temporary static API wiring for the current Phase 2 prototype."""

from dataclasses import dataclass

from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
    build_remote_node_declaration_registry,
)
from home_ai_cluster.core.remote_transport import RemoteTransport
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode


class StaticRemoteProofWiringError(Exception):
    """Raised when explicit static remote proof wiring is incomplete."""


@dataclass(frozen=True)
class StaticRemoteProofWiring:
    """Caller-owned in-memory wiring for the explicit static remote proof."""

    node_registry: NodeRegistry
    adapter_registry: AdapterRegistry
    remote_registry: RemoteNodeDeclarationRegistry
    remote_transport: RemoteTransport
    selection_mode: RoutingCandidateSelectionMode

    def __post_init__(self) -> None:
        if self.node_registry is None:
            raise StaticRemoteProofWiringError(
                "Static remote proof wiring requires a local node registry"
            )

        if self.adapter_registry is None:
            raise StaticRemoteProofWiringError(
                "Static remote proof wiring requires a local adapter registry"
            )

        if self.remote_registry is None:
            raise StaticRemoteProofWiringError(
                "Static remote proof wiring requires a remote declaration registry"
            )

        if self.remote_transport is None:
            raise StaticRemoteProofWiringError(
                "Static remote proof wiring requires an explicit remote transport"
            )

        if self.selection_mode is None:
            raise StaticRemoteProofWiringError(
                "Static remote proof wiring requires an explicit selection mode"
            )

        declarations = self.remote_registry.list_declarations()
        if len(declarations) != 1:
            raise StaticRemoteProofWiringError(
                "Static remote proof wiring requires exactly one declared remote node"
            )


def build_static_remote_proof_wiring(
    *,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_declaration: RemoteNodeDeclaration,
    remote_transport: RemoteTransport,
    selection_mode: RoutingCandidateSelectionMode,
) -> StaticRemoteProofWiring:
    """Build caller-owned in-memory wiring for the explicit static proof."""
    return StaticRemoteProofWiring(
        node_registry=node_registry,
        adapter_registry=adapter_registry,
        remote_registry=build_remote_node_declaration_registry([remote_declaration]),
        remote_transport=remote_transport,
        selection_mode=selection_mode,
    )


def create_static_local_node_announcement() -> NodeDescription:
    """Create the explicit static local node announcement for Phase 2."""
    return NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["ollama"],
    )


def create_static_local_node_registry() -> NodeRegistry:
    """Create the temporary static local node registry."""
    return NodeRegistry([create_static_local_node_announcement()])


def create_static_runtime_adapter_registry() -> AdapterRegistry:
    """Create the temporary static runtime adapter registry."""
    return AdapterRegistry([OllamaAdapter()])
