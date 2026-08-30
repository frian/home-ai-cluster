"""Explicit RFC-0041 and RFC-0044 finite static-cluster status command."""

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import httpx

from home_ai_cluster.api.wiring import LocalAppComposition
from home_ai_cluster.cluster_status import collect_static_cluster_status
from home_ai_cluster.core.models import ClusterStatusResult
from home_ai_cluster.core.remote_node import RemoteNodeDeclarationRegistry
from home_ai_cluster.core.remote_transport import HttpRemoteStatusTransport
from home_ai_cluster.local_runtime_composition import (
    add_local_runtime_arguments,
    create_local_runtime_composition,
    resolve_local_runtime_composition_values,
    validate_local_runtime_arguments,
)
from home_ai_cluster.static_cluster import create_remote_declaration
from home_ai_cluster.static_cluster_declaration import (
    StaticClusterDeclarationError,
    StaticClusterDeclarations,
    load_static_cluster_declarations,
)

STATUS_FAILURE_MESSAGE = "error: unable to construct cluster status result"


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="home-ai-cluster-status")
    parser.add_argument("-d", "--declaration", type=Path, required=True)
    add_local_runtime_arguments(parser)
    parser.add_argument("-j", "--json", action="store_true")
    return parser


def parse_args(
    argv: Sequence[str] | None = None,
) -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    """Parse status arguments while preserving parser-mediated validation errors."""
    parser = _create_argument_parser()
    return parser, parser.parse_args(argv)


def format_cluster_status(result: ClusterStatusResult) -> str:
    """Format one completed status result for ordinary terminal use."""
    lines = [
        "Cluster status",
        f"Declaration: {result.declaration_status}",
        "",
    ]

    if not result.nodes:
        lines.append("Nodes: none")
        return "\n".join(lines)

    lines.append("Nodes:")
    for node in result.nodes:
        lines.extend(
            [
                f"- {node.node_id}",
                f"  Application status: {node.application_status}",
                f"  Runtime status: {node.runtime_status}",
            ]
        )

    return "\n".join(lines)


async def evaluate_static_cluster_status(
    declarations: StaticClusterDeclarations,
    local_app_composition: LocalAppComposition,
):
    """Collect one validated static cluster status result with one HTTP client."""
    remote_registry = RemoteNodeDeclarationRegistry(
        [
            create_remote_declaration(remote.node_id, remote.base_url)
            for remote in declarations.remote_nodes
        ]
    )

    async with httpx.AsyncClient(trust_env=False) as client:
        return await collect_static_cluster_status(
            local_app_composition.node_registry,
            local_app_composition.adapter_registry,
            remote_registry,
            HttpRemoteStatusTransport(client),
        )


def main(argv: Sequence[str] | None = None) -> None:
    """Validate inputs, collect one status result, and print it once."""
    parser, args = parse_args(argv)

    try:
        declarations = load_static_cluster_declarations(args.declaration)
    except StaticClusterDeclarationError as error:
        parser.error(str(error))

    validate_local_runtime_arguments(parser, args)
    values = resolve_local_runtime_composition_values(parser, args)
    local_app_composition = create_local_runtime_composition(
        runtime=values.runtime,
        ollama_model=values.ollama_model,
        ollama_disable_thinking=values.ollama_disable_thinking,
        llama_server_base_url=values.llama_server_base_url,
        llama_server_model=values.llama_server_model,
    )

    try:
        result = asyncio.run(
            evaluate_static_cluster_status(declarations, local_app_composition)
        )
        if args.json:
            print(json.dumps(result.model_dump(mode="json"), separators=(",", ":")))
        else:
            print(format_cluster_status(result))
    except Exception as error:
        print(STATUS_FAILURE_MESSAGE, file=sys.stderr)
        raise SystemExit(1) from error
