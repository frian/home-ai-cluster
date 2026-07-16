"""Explicit RFC-0036 static operator preflight command."""

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from home_ai_cluster.api.wiring import (
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.models import NodeDescription
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.static_cluster import (
    create_remote_declaration,
    remote_base_url,
    remote_node_id,
)

MISSING_ADAPTER_REASON = "declared adapter is not present in the inspected registry"
PREFLIGHT_FAILURE_MESSAGE = "error: unable to construct static preflight report"


def project_static_preflight(
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
) -> dict[str, Any]:
    """Project one read-only static coherence report."""
    return project_static_preflight_nodes(
        node_registry.list_nodes(),
        adapter_registry,
        operating_mode="local-only",
    )


def project_static_preflight_nodes(
    nodes: Sequence[NodeDescription],
    adapter_registry: AdapterRegistry,
    *,
    operating_mode: str,
) -> dict[str, Any]:
    """Project one read-only static coherence report for ordered declarations."""
    projected_nodes = []
    issues = []

    for node in nodes:
        projected_nodes.append(
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
        "operating_mode": operating_mode,
        "nodes": projected_nodes,
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


def evaluate_static_multi_node_preflight(
    remote_node_id_value: str,
    remote_base_url_value: str,
    *,
    node_registry: NodeRegistry | None = None,
    adapter_registry: AdapterRegistry | None = None,
) -> dict[str, Any]:
    """Inspect one local and one explicit remote declaration without transport use."""
    local_nodes = (
        node_registry
        if node_registry is not None
        else create_static_local_node_registry()
    )
    adapters = (
        adapter_registry
        if adapter_registry is not None
        else create_static_runtime_adapter_registry()
    )
    remote_declaration = create_remote_declaration(
        remote_node_id_value,
        remote_base_url_value,
    )
    return project_static_preflight_nodes(
        [*local_nodes.list_nodes(), remote_declaration.node],
        adapters,
        operating_mode="static-multi-node",
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse either local-only or one explicit static multi-node declaration."""
    parser = argparse.ArgumentParser(prog="home-ai-cluster-preflight")
    parser.add_argument("--remote-node-id", type=remote_node_id)
    parser.add_argument("--remote-base-url", type=remote_base_url)
    args = parser.parse_args(argv)

    if (args.remote_node_id is None) != (args.remote_base_url is None):
        parser.error("--remote-node-id and --remote-base-url must be supplied together")

    return args


def main(argv: Sequence[str] | None = None) -> None:
    """Emit one compact RFC-0036 preflight report and its operator exit status."""
    args = parse_args(argv)

    try:
        report = (
            evaluate_static_preflight()
            if args.remote_node_id is None
            else evaluate_static_multi_node_preflight(
                args.remote_node_id,
                args.remote_base_url,
            )
        )
    except Exception as error:
        print(PREFLIGHT_FAILURE_MESSAGE, file=sys.stderr)
        raise SystemExit(1) from error

    print(json.dumps(report, separators=(",", ":")))

    if report["status"] == "incoherent":
        raise SystemExit(1)
