"""Static API wiring for local and explicitly declared remote nodes."""

from collections.abc import Sequence
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
from home_ai_cluster.static_capabilities import DEFAULT_STATIC_CAPABILITY_NAMES


class StaticRemoteWiringError(Exception):
    """Raised when explicit static remote wiring is incomplete."""


class LocalAppCompositionError(Exception):
    """Raised when ordinary local application composition is incomplete."""


@dataclass(frozen=True)
class LocalAppComposition:
    """Explicit local registries for ordinary application construction."""

    node_registry: NodeRegistry
    adapter_registry: AdapterRegistry

    def __post_init__(self) -> None:
        if self.node_registry is None:
            raise LocalAppCompositionError(
                "Local application composition requires a local node registry"
            )
        if self.adapter_registry is None:
            raise LocalAppCompositionError(
                "Local application composition requires a local adapter registry"
            )


def _validate_static_remote_wiring_dependencies(
    *,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry,
    remote_transport: RemoteTransport,
    selection_mode: RoutingCandidateSelectionMode,
) -> list[RemoteNodeDeclaration]:
    if node_registry is None:
        raise StaticRemoteWiringError(
            "Static remote wiring requires a local node registry"
        )
    if adapter_registry is None:
        raise StaticRemoteWiringError(
            "Static remote wiring requires a local adapter registry"
        )
    if remote_registry is None:
        raise StaticRemoteWiringError(
            "Static remote wiring requires a remote declaration registry"
        )
    if remote_transport is None:
        raise StaticRemoteWiringError(
            "Static remote wiring requires an explicit remote transport"
        )
    if selection_mode is None:
        raise StaticRemoteWiringError(
            "Static remote wiring requires an explicit selection mode"
        )
    return remote_registry.list_declarations()


@dataclass(frozen=True)
class StaticRemoteWiring:
    """Caller-owned in-memory wiring for one explicit static remote node."""

    node_registry: NodeRegistry
    adapter_registry: AdapterRegistry
    remote_registry: RemoteNodeDeclarationRegistry
    remote_transport: RemoteTransport
    selection_mode: RoutingCandidateSelectionMode

    def __post_init__(self) -> None:
        declarations = _validate_static_remote_wiring_dependencies(
            node_registry=self.node_registry,
            adapter_registry=self.adapter_registry,
            remote_registry=self.remote_registry,
            remote_transport=self.remote_transport,
            selection_mode=self.selection_mode,
        )
        if len(declarations) != 1:
            raise StaticRemoteWiringError(
                "Static remote wiring requires exactly one declared remote node"
            )


@dataclass(frozen=True)
class StaticRemoteCollectionWiring:
    """Caller-owned wiring for one ordered non-empty remote collection."""

    node_registry: NodeRegistry
    adapter_registry: AdapterRegistry
    remote_registry: RemoteNodeDeclarationRegistry
    remote_transport: RemoteTransport
    selection_mode: RoutingCandidateSelectionMode

    def __post_init__(self) -> None:
        declarations = _validate_static_remote_wiring_dependencies(
            node_registry=self.node_registry,
            adapter_registry=self.adapter_registry,
            remote_registry=self.remote_registry,
            remote_transport=self.remote_transport,
            selection_mode=self.selection_mode,
        )
        if not declarations:
            raise StaticRemoteWiringError(
                "Static remote collection wiring requires at least one "
                "declared remote node"
            )


def build_static_remote_collection_wiring(
    *,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_declarations: Sequence[RemoteNodeDeclaration],
    remote_transport: RemoteTransport,
    selection_mode: RoutingCandidateSelectionMode,
) -> StaticRemoteCollectionWiring:
    """Build caller-owned wiring for one ordered static remote collection."""
    return StaticRemoteCollectionWiring(
        node_registry=node_registry,
        adapter_registry=adapter_registry,
        remote_registry=build_remote_node_declaration_registry(remote_declarations),
        remote_transport=remote_transport,
        selection_mode=selection_mode,
    )


def build_static_remote_wiring(
    *,
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_declaration: RemoteNodeDeclaration,
    remote_transport: RemoteTransport,
    selection_mode: RoutingCandidateSelectionMode,
) -> StaticRemoteWiring:
    """Preserve the accepted single-remote wiring seam."""
    return StaticRemoteWiring(
        node_registry=node_registry,
        adapter_registry=adapter_registry,
        remote_registry=build_remote_node_declaration_registry([remote_declaration]),
        remote_transport=remote_transport,
        selection_mode=selection_mode,
    )


def create_static_local_node_announcement(
    capabilities: Sequence[str] = DEFAULT_STATIC_CAPABILITY_NAMES,
) -> NodeDescription:
    """Create the explicit static local node announcement for Phase 2."""
    return NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name=name) for name in capabilities],
        adapters=["ollama"],
    )


def create_static_local_node_registry(
    capabilities: Sequence[str] = DEFAULT_STATIC_CAPABILITY_NAMES,
) -> NodeRegistry:
    """Create the temporary static local node registry."""
    return NodeRegistry([create_static_local_node_announcement(capabilities)])


def create_static_runtime_adapter_registry() -> AdapterRegistry:
    """Create the temporary static runtime adapter registry."""
    return AdapterRegistry([OllamaAdapter()])
