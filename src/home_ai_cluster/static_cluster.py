"""Ordinary RFC-0038 static local-plus-one-remote application process."""

import argparse
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI

from home_ai_cluster.api.wiring import (
    build_static_remote_wiring,
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.remote_transport import HttpRemoteTransport
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.main import create_app
from home_ai_cluster.static_cluster_declaration import (
    StaticClusterDeclarationError,
    load_static_cluster_declaration,
)
from home_ai_cluster.static_cluster_validation import (
    LOCAL_NODE_ID,  # noqa: F401
    remote_base_url,
    remote_node_id,
)

STATIC_CLUSTER_HOST = "127.0.0.1"
STATIC_CLUSTER_PORT = 8000


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="home-ai-cluster-static-cluster")
    parser.add_argument("--declaration", type=Path)
    parser.add_argument("--remote-node-id", type=remote_node_id)
    parser.add_argument("--remote-base-url", type=remote_base_url)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse exactly one complete RFC-0039 static topology input mode."""
    parser = _create_argument_parser()
    args = parser.parse_args(argv)

    has_declaration = args.declaration is not None
    has_remote_node_id = args.remote_node_id is not None
    has_remote_base_url = args.remote_base_url is not None

    if has_declaration and (has_remote_node_id or has_remote_base_url):
        parser.error("--declaration cannot be combined with inline remote arguments")

    if has_remote_node_id != has_remote_base_url:
        parser.error(
            "--remote-node-id and --remote-base-url must be provided together"
        )

    if not has_declaration and not has_remote_node_id:
        parser.error("provide either --declaration or both inline remote arguments")

    return args


def create_remote_declaration(
    node_id: str,
    base_url: str,
) -> RemoteNodeDeclaration:
    """Create the one static remote declaration for this process only."""
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id=node_id,
            name=f"Declared remote node {node_id}",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="chat")],
            adapters=["ollama"],
        ),
        transport_address=base_url,
    )


def create_static_cluster_http_client() -> httpx.AsyncClient:
    """Create the process-owned remote client without a model read timeout."""
    return httpx.AsyncClient(timeout=None)


def create_static_cluster_app(
    node_id: str,
    base_url: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> FastAPI:
    """Construct the ordinary static local-plus-one-remote application."""
    process_client = client or create_static_cluster_http_client()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await process_client.aclose()

    wiring = build_static_remote_wiring(
        node_registry=create_static_local_node_registry(),
        adapter_registry=create_static_runtime_adapter_registry(),
        remote_declaration=create_remote_declaration(node_id, base_url),
        remote_transport=HttpRemoteTransport(process_client),
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )
    app = create_app(static_remote_wiring=wiring, lifespan=lifespan)
    app.state.static_cluster_http_client = process_client
    return app


def main(argv: Sequence[str] | None = None) -> None:
    """Run one ordinary loopback-only static multi-node application process."""
    args = parse_args(argv)

    if args.declaration is not None:
        try:
            declaration = load_static_cluster_declaration(args.declaration)
        except StaticClusterDeclarationError as exc:
            _create_argument_parser().error(str(exc))
        node_id = declaration.remote_node_id
        base_url = declaration.remote_base_url
    else:
        node_id = args.remote_node_id
        base_url = args.remote_base_url

    uvicorn.run(
        create_static_cluster_app(node_id, base_url),
        host=STATIC_CLUSTER_HOST,
        port=STATIC_CLUSTER_PORT,
    )
