"""Explicit RFC-0041 finite status command for one static declaration."""

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import httpx

from home_ai_cluster.api.wiring import (
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.cluster_status import collect_static_cluster_status
from home_ai_cluster.core.remote_node import RemoteNodeDeclarationRegistry
from home_ai_cluster.core.remote_transport import HttpRemoteStatusTransport
from home_ai_cluster.static_cluster import create_remote_declaration
from home_ai_cluster.static_cluster_declaration import (
    StaticClusterDeclarationError,
    StaticClusterDeclarations,
    load_static_cluster_declarations,
)

STATUS_FAILURE_MESSAGE = "error: unable to construct cluster status result"


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="home-ai-cluster-status")
    parser.add_argument("--declaration", type=Path, required=True)
    return parser


async def evaluate_static_cluster_status(
    declarations: StaticClusterDeclarations,
):
    """Collect one validated static cluster status result with one HTTP client."""
    node_registry = create_static_local_node_registry()
    adapter_registry = create_static_runtime_adapter_registry()
    remote_registry = RemoteNodeDeclarationRegistry(
        [
            create_remote_declaration(remote.node_id, remote.base_url)
            for remote in declarations.remote_nodes
        ]
    )

    async with httpx.AsyncClient() as client:
        return await collect_static_cluster_status(
            node_registry,
            adapter_registry,
            remote_registry,
            HttpRemoteStatusTransport(client),
        )


def main(argv: Sequence[str] | None = None) -> None:
    """Validate one declaration, collect one status result, and print compact JSON."""
    parser = _create_argument_parser()
    args = parser.parse_args(argv)

    try:
        declarations = load_static_cluster_declarations(args.declaration)
    except StaticClusterDeclarationError as error:
        parser.error(str(error))

    try:
        result = asyncio.run(evaluate_static_cluster_status(declarations))
        print(json.dumps(result.model_dump(mode="json"), separators=(",", ":")))
    except Exception as error:
        print(STATUS_FAILURE_MESSAGE, file=sys.stderr)
        raise SystemExit(1) from error
