"""Explicit RFC-0033 local node and adapter health snapshot command."""

import json
import sys
from typing import Any

from home_ai_cluster.api.wiring import (
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.models import NodeDescription
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry

MISSING_ADAPTER_REASON = "declared adapter is not present in the inspected registry"
PROBE_FAILED_REASON = "adapter health observation failed"
SNAPSHOT_FAILURE_MESSAGE = "error: unable to construct local health snapshot"


def project_health_snapshot(
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
) -> dict[str, Any]:
    """Project static node declarations and direct adapter health observations."""
    return {
        "nodes": [
            _project_node(node, adapter_registry)
            for node in node_registry.list_nodes()
        ]
    }


def _project_node(
    node: NodeDescription,
    adapter_registry: AdapterRegistry,
) -> dict[str, Any]:
    return {
        "node_id": node.id,
        "name": node.name,
        "declared": {
            "availability": node.availability,
            "healthy": node.health.healthy,
            "reason": node.health.reason,
            "capabilities": [capability.name for capability in node.capabilities],
            "adapters": list(node.adapters),
        },
        "adapter_observations": [
            _observe_adapter(adapter_name, adapter_registry)
            for adapter_name in node.adapters
        ],
    }


def _observe_adapter(
    adapter_name: str,
    adapter_registry: AdapterRegistry,
) -> dict[str, str | None]:
    adapter = adapter_registry.adapter_named(adapter_name)
    if adapter is None:
        return {
            "adapter": adapter_name,
            "status": "missing",
            "reason": MISSING_ADAPTER_REASON,
        }

    try:
        health = adapter.health()
    except Exception:
        return {
            "adapter": adapter_name,
            "status": "probe-failed",
            "reason": PROBE_FAILED_REASON,
        }

    return {
        "adapter": adapter_name,
        "status": "available" if health.available else "unavailable",
        "reason": health.reason,
    }


def evaluate_health_snapshot(
    *,
    node_registry: NodeRegistry | None = None,
    adapter_registry: AdapterRegistry | None = None,
) -> dict[str, Any]:
    """Inspect the ordinary local registries for one process-scoped snapshot."""
    return project_health_snapshot(
        node_registry
        if node_registry is not None
        else create_static_local_node_registry(),
        adapter_registry
        if adapter_registry is not None
        else create_static_runtime_adapter_registry(),
    )


def main() -> None:
    """Emit one compact RFC-0033 local health snapshot JSON object."""
    try:
        snapshot = evaluate_health_snapshot()
    except Exception as error:
        print(SNAPSHOT_FAILURE_MESSAGE, file=sys.stderr)
        raise SystemExit(1) from error

    print(json.dumps(snapshot, separators=(",", ":")))
