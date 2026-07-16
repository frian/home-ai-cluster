"""Explicit RFC-0036 static operator preflight command."""

import json
import sys
from typing import Any

from home_ai_cluster.api.wiring import (
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry

MISSING_ADAPTER_REASON = "declared adapter is not present in the inspected registry"
PREFLIGHT_FAILURE_MESSAGE = "error: unable to construct static preflight report"


def project_static_preflight(
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
) -> dict[str, Any]:
    """Project one read-only static coherence report."""
    nodes = []
    issues = []

    for node in node_registry.list_nodes():
        nodes.append(
            {
                "node_id": node.id,
                "capabilities": [capability.name for capability in node.capabilities],
                "declared_adapters": list(node.adapters),
            }
        )

        for adapter_name in node.adapters:
            if adapter_registry.adapter_named(adapter_name) is None:
                issues.append(
                    {
                        "status": "missing-adapter",
                        "node_id": node.id,
                        "adapter": adapter_name,
                        "reason": MISSING_ADAPTER_REASON,
                    }
                )

    return {
        "status": "incoherent" if issues else "coherent",
        "operating_mode": "local-only",
        "nodes": nodes,
        "registered_adapters": [
            adapter.name for adapter in adapter_registry.list_adapters()
        ],
        "issues": issues,
    }


def evaluate_static_preflight(
    *,
    node_registry: NodeRegistry | None = None,
    adapter_registry: AdapterRegistry | None = None,
) -> dict[str, Any]:
    """Inspect the ordinary static local registries without runtime operations."""
    return project_static_preflight(
        node_registry
        if node_registry is not None
        else create_static_local_node_registry(),
        adapter_registry
        if adapter_registry is not None
        else create_static_runtime_adapter_registry(),
    )


def main() -> None:
    """Emit one compact RFC-0036 preflight report and its operator exit status."""
    try:
        report = evaluate_static_preflight()
    except Exception as error:
        print(PREFLIGHT_FAILURE_MESSAGE, file=sys.stderr)
        raise SystemExit(1) from error

    print(json.dumps(report, separators=(",", ":")))

    if report["status"] == "incoherent":
        raise SystemExit(1)
