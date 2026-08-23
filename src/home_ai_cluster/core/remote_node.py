"""Static remote node declaration model."""

from collections.abc import Iterable
from dataclasses import dataclass

from pydantic import BaseModel, Field

from home_ai_cluster.core.models import (
    Capability,
    NodeDescription,
    RoutableRequest,
)
from home_ai_cluster.core.node import node_supports_capability

DECLARED_REMOTE_ROUTING_REASON = (
    "Selected declared remote routing eligibility candidate."
)


class RemoteNodeDeclaration(BaseModel):
    """A manually and statically declared remote node.

    The node description is the cluster-visible node metadata. The transport
    address is transport metadata for a declared node; it is not node identity,
    proof of trust, discovery, or registration.
    """

    node: NodeDescription
    transport_address: str = Field(min_length=1)


class RemoteNodeDeclarationRegistry:
    """In-memory registry for manually declared remote nodes."""

    def __init__(
        self,
        declarations: Iterable[RemoteNodeDeclaration] | None = None,
    ) -> None:
        self._declarations: list[RemoteNodeDeclaration] = list(declarations or ())

    def list_declarations(self) -> list[RemoteNodeDeclaration]:
        """Return declared remote nodes in declaration order."""
        return list(self._declarations)

    def declaration_for_node_id(
        self,
        node_id: str,
    ) -> RemoteNodeDeclaration | None:
        """Return the first declaration for the requested cluster node id."""
        for declaration in self._declarations:
            if declaration.node.id == node_id:
                return declaration

        return None


@dataclass(frozen=True)
class DeclaredRemoteRoutingCandidate:
    """A declared remote routing candidate selected without local adapters."""

    node: NodeDescription
    declaration: RemoteNodeDeclaration
    capability: Capability
    reason: str


def build_remote_node_declaration_registry(
    declarations: Iterable[RemoteNodeDeclaration],
) -> RemoteNodeDeclarationRegistry:
    """Build an in-memory registry from explicit caller-owned declarations."""
    return RemoteNodeDeclarationRegistry(declarations)


def declared_remote_declarations_for_request(
    request: RoutableRequest,
    remote_registry: RemoteNodeDeclarationRegistry,
) -> list[RemoteNodeDeclaration]:
    """Return declared remote declarations eligible for the requested capability."""
    return [
        declaration
        for declaration in remote_registry.list_declarations()
        if node_supports_capability(declaration.node, request.capability)
    ]


def declared_remote_routing_candidates_for_request(
    request: RoutableRequest,
    remote_registry: RemoteNodeDeclarationRegistry,
) -> list[DeclaredRemoteRoutingCandidate]:
    """Return eligible remotes in operator-owned declaration priority order.

    RFC-0040 forbids sorting, health-ranking, inferred preference, or other
    automatic reordering.
    """
    return [
        DeclaredRemoteRoutingCandidate(
            node=declaration.node,
            declaration=declaration,
            capability=request.capability,
            reason=DECLARED_REMOTE_ROUTING_REASON,
        )
        for declaration in declared_remote_declarations_for_request(
            request,
            remote_registry,
        )
    ]


def declared_remote_routing_candidate_for_request(
    request: RoutableRequest,
    remote_registry: RemoteNodeDeclarationRegistry,
) -> DeclaredRemoteRoutingCandidate | None:
    """Preserve the first eligible declared remote candidate compatibility seam."""
    candidates = declared_remote_routing_candidates_for_request(
        request,
        remote_registry,
    )
    return candidates[0] if candidates else None
