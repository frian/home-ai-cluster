"""Remote transport boundary for normalized cluster objects."""

from typing import Protocol

from home_ai_cluster.core.models import ClusterRequest, ClusterResult
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration


class RemoteTransportError(Exception):
    """Raised when a remote transport cannot carry a cluster request."""


class RemoteTransport(Protocol):
    """Boundary for carrying a normalized request to a declared remote node."""

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        """Send a normalized request to a manually declared remote node."""
        ...
