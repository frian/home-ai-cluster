"""Explicit process entrypoint for the RFC-0022 two-machine proof."""

import argparse
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

import httpx
import uvicorn
from fastapi import FastAPI

from home_ai_cluster.api.wiring import (
    build_static_remote_proof_wiring,
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.remote_transport import HttpRemoteTransport
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.main import create_app

PROOF_HOST = "127.0.0.1"
PROOF_PORT = 8000
REMOTE_NODE_ID = "declared-remote"


def remote_address(value: str) -> str:
    """Validate one explicit HTTP transport address for the proof command."""
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
        raise argparse.ArgumentTypeError(
            "remote address must be an absolute http:// or https:// URL"
        )
    return value.rstrip("/")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the explicit proof-only process arguments."""
    parser = argparse.ArgumentParser(
        prog="home-ai-cluster-static-proof",
        description="Run the explicit RFC-0022 static two-machine proof.",
    )
    parser.add_argument(
        "remote_address",
        type=remote_address,
        help="LAN HTTP address of the manually declared remote node",
    )
    return parser.parse_args(argv)


def create_remote_declaration(address: str) -> RemoteNodeDeclaration:
    """Create the one fixed manually declared remote node for the proof."""
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id=REMOTE_NODE_ID,
            name="Declared remote node",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="chat")],
            adapters=["ollama"],
        ),
        transport_address=address,
    )


def create_static_proof_app(
    address: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> FastAPI:
    """Construct the explicit caller-owned proof application."""
    process_client = client or httpx.AsyncClient()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await process_client.aclose()

    wiring = build_static_remote_proof_wiring(
        node_registry=create_static_local_node_registry(),
        adapter_registry=create_static_runtime_adapter_registry(),
        remote_declaration=create_remote_declaration(address),
        remote_transport=HttpRemoteTransport(process_client),
        selection_mode=RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
    )
    app = create_app(static_remote_proof_wiring=wiring, lifespan=lifespan)
    app.state.static_proof_http_client = process_client
    return app


def main(argv: Sequence[str] | None = None) -> None:
    """Run the explicit LAN-only static proof process."""
    args = parse_args(argv)
    app = create_static_proof_app(args.remote_address)
    uvicorn.run(app, host=PROOF_HOST, port=PROOF_PORT)
