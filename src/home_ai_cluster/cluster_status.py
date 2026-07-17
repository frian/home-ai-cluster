"""RFC-0041 sequential status collection for one validated static cluster."""

from home_ai_cluster.core.models import (
    ClusterStatusNode,
    ClusterStatusResult,
    DeclarationStatus,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclarationRegistry
from home_ai_cluster.core.remote_transport import HttpRemoteStatusTransport
from home_ai_cluster.local_health_snapshot import (
    project_health_snapshot,
    project_local_cluster_status,
)


async def collect_static_cluster_status(
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
    remote_registry: RemoteNodeDeclarationRegistry,
    remote_status_transport: HttpRemoteStatusTransport,
) -> ClusterStatusResult:
    """Collect local then declared-remote observations after declaration validation."""
    local_snapshot = project_health_snapshot(node_registry, adapter_registry)
    nodes: list[ClusterStatusNode] = [
        project_local_cluster_status(local_snapshot)
    ]

    for declaration in remote_registry.list_declarations():
        nodes.append(await remote_status_transport.observe(declaration))

    return ClusterStatusResult(
        declaration_status=DeclarationStatus.COHERENT,
        nodes=tuple(nodes),
    )
