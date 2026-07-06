"""Static remote node declaration model."""

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
