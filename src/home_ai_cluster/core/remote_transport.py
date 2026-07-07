"""Remote transport boundary for normalized cluster objects."""

from typing import Protocol

import httpx
from pydantic import ValidationError

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


class HttpRemoteTransport:
    """HTTP transport for manually declared remote nodes."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        endpoint = internal_cluster_request_url(declaration)

        try:
            response = await self._client.post(
                endpoint,
                json=request.model_dump(mode="json"),
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RemoteTransportError("HTTP remote transport could not send request") from exc

        try:
            return ClusterResult.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise RemoteTransportError("HTTP remote transport returned invalid result") from exc


def internal_cluster_request_url(declaration: RemoteNodeDeclaration) -> str:
    """Return the RFC-0014 internal request endpoint for a declaration."""
    return f"{declaration.transport_address.rstrip('/')}/internal/cluster/request"
