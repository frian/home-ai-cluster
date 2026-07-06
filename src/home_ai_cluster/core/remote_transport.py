"""Remote transport boundary for normalized cluster objects."""

from typing import Protocol

from home_ai_cluster.core.models import ClusterRequest, ClusterResult, NodeDescription


class RemoteTransportError(Exception):
    """Raised when a remote transport cannot carry a cluster request."""


class RemoteTransport(Protocol):
    """Boundary for carrying a normalized request to a selected remote node."""

    async def send(
        self,
        request: ClusterRequest,
        node: NodeDescription,
    ) -> ClusterResult:
        """Send a normalized cluster request to a selected node."""
        ...
