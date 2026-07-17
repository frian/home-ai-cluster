"""Explicit RFC-0036 static operator preflight command."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
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
from home_ai_cluster.static_cluster_declaration import (
    StaticClusterDeclarationError,
    StaticClusterDeclarations,
    load_static_cluster_declarations,
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
    adapter_resolution_node_ids: set[str] | None = None,
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

        resolves_locally = (
            adapter_resolution_node_ids is None
            or node.id in adapter_resolution_node_ids
        )
        if resolves_locally:
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
    declarations = StaticClusterDeclarations(
        remote_nodes=(
            load_inline_remote_declaration(
                remote_node_id_value,
                remote_base_url_value,
            ),
        )
    )
    return evaluate_static_declarations_preflight(
        declarations,
        node_registry=node_registry,
        adapter_registry=adapter_registry,
    )


def load_inline_remote_declaration(
    remote_node_id_value: str,
    remote_base_url_value: str,
):
    """Convert the accepted inline pair into one declaration value."""
    from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration

    return RemoteNodeDeclaration(
        node_id=remote_node_id_value,
        base_url=remote_base_url_value,
    )


def evaluate_static_declarations_preflight(
    declarations: StaticClusterDeclarations,
    *,
    node_registry: NodeRegistry | None = None,
    adapter_registry: AdapterRegistry | None = None,
) -> dict[str, Any]:
    """Inspect local plus ordered remote declarations without transport use."""
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
    remote_nodes = [
        create_remote_declaration(remote.node_id, remote.base_url).node
        for remote in declarations.remote_nodes
    ]
    return project_static_preflight_nodes(
        [*local_nodes.list_nodes(), *remote_nodes],
        adapters,
        operating_mode="static-multi-node",
        adapter_resolution_node_ids={node.id for node in local_nodes.list_nodes()},
    )


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="home-ai-cluster-preflight")
    parser.add_argument("--declaration", type=Path)
    parser.add_argument("--remote-node-id", type=remote_node_id)
    parser.add_argument("--remote-base-url", type=remote_base_url)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse local-only, inline single-remote, or declaration preflight mode."""
    parser = _create_argument_parser()
    args = parser.parse_args(argv)

    has_declaration = args.declaration is not None
    has_remote_node_id = args.remote_node_id is not None
    has_remote_base_url = args.remote_base_url is not None

    if has_declaration and (has_remote_node_id or has_remote_base_url):
        parser.error("--declaration cannot be combined with inline remote arguments")

    if has_remote_node_id != has_remote_base_url:
        parser.error("--remote-node-id and --remote-base-url must be supplied together")

    return args


def main(argv: Sequence[str] | None = None) -> None:
    """Emit one compact RFC-0036 preflight report and its operator exit status."""
    args = parse_args(argv)

    try:
        if args.declaration is not None:
            report = evaluate_static_declarations_preflight(
                load_static_cluster_declarations(args.declaration)
            )
        elif args.remote_node_id is not None:
            report = evaluate_static_multi_node_preflight(
                args.remote_node_id,
                args.remote_base_url,
            )
        else:
            report = evaluate_static_preflight()
    except StaticClusterDeclarationError as error:
        _create_argument_parser().error(str(error))
    except Exception as error:
        print(PREFLIGHT_FAILURE_MESSAGE, file=sys.stderr)
        raise SystemExit(1) from error

    print(json.dumps(report, separators=(",", ":")))

    if report["status"] == "incoherent":
        raise SystemExit(1)
