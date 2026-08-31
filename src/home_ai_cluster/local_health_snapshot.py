"""Explicit RFC-0033 local node and adapter health snapshot command."""

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from typing import Any

from home_ai_cluster.api.wiring import (
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.models import (
    ApplicationStatus,
    ClusterStatusNode,
    NodeDescription,
    RuntimeStatus,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.local_runtime_composition import LOCAL_RUNTIME_CAPABILITY_NAMES

MISSING_ADAPTER_REASON = "declared adapter is not present in the inspected registry"
PROBE_FAILED_REASON = "adapter health observation failed"
SNAPSHOT_FAILURE_MESSAGE = "error: unable to construct local health snapshot"

_LOCAL_RUNTIME_STATUSES = {
    "available": RuntimeStatus.AVAILABLE,
    "unavailable": RuntimeStatus.UNAVAILABLE,
    "probe-failed": RuntimeStatus.OBSERVATION_FAILED,
}


def project_health_snapshot(
    node_registry: NodeRegistry,
    adapter_registry: AdapterRegistry,
) -> dict[str, Any]:
    """Project static node declarations and direct adapter health observations."""
    return {
        "nodes": [
            _project_node(node, adapter_registry) for node in node_registry.list_nodes()
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
        else create_static_local_node_registry(LOCAL_RUNTIME_CAPABILITY_NAMES),
        adapter_registry
        if adapter_registry is not None
        else create_static_runtime_adapter_registry(),
    )


def project_local_cluster_status(
    snapshot: Mapping[str, Any],
) -> ClusterStatusNode:
    """Normalize one completed local health snapshot without observing health again."""
    try:
        nodes = snapshot["nodes"]
        if not isinstance(nodes, list) or len(nodes) != 1:
            raise ValueError("local health snapshot must contain exactly one node")

        observations = nodes[0]["adapter_observations"]
        if not isinstance(observations, list) or len(observations) != 1:
            raise ValueError(
                "local health snapshot must contain exactly one adapter observation"
            )
        observation_status = observations[0]["status"]
    except (KeyError, TypeError) as error:
        raise ValueError(
            "local health snapshot is not a local runtime observation"
        ) from error

    try:
        runtime_status = _LOCAL_RUNTIME_STATUSES[observation_status]
    except KeyError as error:
        raise ValueError(
            "local health snapshot has an unsupported observation status"
        ) from error

    return ClusterStatusNode(
        node_id="local",
        application_status=ApplicationStatus.LOCAL,
        runtime_status=runtime_status,
    )


def format_health_snapshot(snapshot: Mapping[str, Any]) -> str:
    """Format one completed local health snapshot for ordinary terminal use."""
    lines = ["Local health", ""]
    nodes = snapshot["nodes"]

    if not nodes:
        lines.append("Nodes: none")
        return "\n".join(lines)

    lines.append("Nodes:")
    for node_index, node in enumerate(nodes):
        if node_index:
            lines.append("")

        declared = node["declared"]
        lines.extend(
            [
                f"- {_format_value(node['node_id'])}",
                f"  Name: {_format_value(node['name'])}",
                "",
                "  Declared state:",
                f"    Availability: {_format_value(declared['availability'])}",
                f"    Healthy: {_format_value(declared['healthy'])}",
                f"    Reason: {_format_value(declared['reason'])}",
                f"    Capabilities: {_format_values(declared['capabilities'])}",
                f"    Adapters: {_format_values(declared['adapters'])}",
                "",
            ]
        )

        observations = node["adapter_observations"]
        if observations:
            lines.append("  Adapter observations:")
            for observation in observations:
                lines.extend(
                    [
                        f"  - Adapter: {_format_value(observation['adapter'])}",
                        f"    Status: {_format_value(observation['status'])}",
                        f"    Reason: {_format_value(observation['reason'])}",
                    ]
                )
        else:
            lines.append("  Adapter observations: none")

    return "\n".join(lines)


def _format_values(values: Sequence[Any]) -> str:
    if not values:
        return "none"
    return ", ".join(_format_value(value) for value in values)


def _format_value(value: object) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="home-ai-cluster-health",
        description="Take one finite local runtime/adapter health snapshot.",
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Print the compact structured snapshot.",
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the selected local health snapshot output format."""
    parser = _create_argument_parser()
    if argv in (["-h"], ["--help"]):
        parser.prog = "home-ai-cluster health"
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Emit one RFC-0033 local health snapshot in the selected output format."""
    args = parse_args(argv)
    try:
        snapshot = evaluate_health_snapshot()
    except Exception as error:
        print(SNAPSHOT_FAILURE_MESSAGE, file=sys.stderr)
        raise SystemExit(1) from error

    if args.json:
        print(json.dumps(snapshot, separators=(",", ":")))
    else:
        print(format_health_snapshot(snapshot))
