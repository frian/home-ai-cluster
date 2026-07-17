"""Remote transport boundary for normalized cluster objects."""

from typing import Protocol

import httpx
from pydantic import ValidationError

from home_ai_cluster.adapters.base import (
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.core.models import (
    ApplicationStatus,
    ClusterRequest,
    ClusterResult,
    ClusterStatusNode,
    InternalClusterStatusResponse,
    RuntimeStatus,
)
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration

REMOTE_STATUS_TIMEOUT_SECONDS = 5.0
"""Fixed per-remote bound for one trusted home-LAN status observation."""


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
        except httpx.ConnectError as exc:
            message = "Remote connection unavailable before request transmission"
            raise RuntimeConnectionUnavailableBeforeRequestError(message) from exc
        except httpx.HTTPError as exc:
            message = "HTTP remote transport could not send request"
            raise RemoteTransportError(message) from exc

        try:
            return ClusterResult.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            message = "HTTP remote transport returned invalid result"
            raise RemoteTransportError(message) from exc


class HttpRemoteStatusTransport:
    """Bounded HTTP observation transport for one declared remote node."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def observe(
        self,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterStatusNode:
        """Observe one remote once and return its normalized status result."""
        try:
            response = await self._client.get(
                internal_cluster_status_url(declaration),
                timeout=REMOTE_STATUS_TIMEOUT_SECONDS,
            )
        except (httpx.ConnectError, httpx.ConnectTimeout):
            return _remote_status_node(
                declaration,
                ApplicationStatus.UNREACHABLE,
                RuntimeStatus.UNKNOWN,
            )
        except httpx.HTTPError:
            return _remote_status_node(
                declaration,
                ApplicationStatus.REQUEST_FAILED,
                RuntimeStatus.UNKNOWN,
            )

        if response.status_code != 200:
            return _remote_status_node(
                declaration,
                ApplicationStatus.INVALID_RESPONSE,
                RuntimeStatus.UNKNOWN,
            )

        try:
            remote_status = InternalClusterStatusResponse.model_validate(
                response.json()
            )
        except (ValueError, ValidationError):
            return _remote_status_node(
                declaration,
                ApplicationStatus.INVALID_RESPONSE,
                RuntimeStatus.UNKNOWN,
            )

        return _remote_status_node(
            declaration,
            ApplicationStatus.REACHABLE,
            remote_status.runtime_status,
        )


def internal_cluster_request_url(declaration: RemoteNodeDeclaration) -> str:
    """Return the RFC-0014 internal request endpoint for a declaration."""
    address = declaration.transport_address.rstrip("/")
    return f"{address}/internal/cluster/request"


def internal_cluster_status_url(declaration: RemoteNodeDeclaration) -> str:
    """Return the RFC-0041 internal status endpoint for a declaration."""
    address = declaration.transport_address.rstrip("/")
    return f"{address}/internal/cluster/status"


def _remote_status_node(
    declaration: RemoteNodeDeclaration,
    application_status: ApplicationStatus,
    runtime_status: RuntimeStatus,
) -> ClusterStatusNode:
    return ClusterStatusNode(
        node_id=declaration.node.id,
        application_status=application_status,
        runtime_status=runtime_status,
    )
