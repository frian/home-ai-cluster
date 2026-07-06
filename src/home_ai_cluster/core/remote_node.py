"""Static remote node declaration model."""

from collections.abc import Iterable

from pydantic import BaseModel, Field

from home_ai_cluster.core.models import NodeDescription


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
