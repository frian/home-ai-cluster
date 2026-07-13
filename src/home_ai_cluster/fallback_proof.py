"""Explicit process entrypoint for the RFC-0028 fallback proof."""

import argparse
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

import httpx
import uvicorn
from fastapi import FastAPI

from home_ai_cluster.adapters.base import RuntimeAdapter
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.orchestrator import (
    orchestrate_request_with_automatic_capability_fallback,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    build_remote_node_declaration_registry,
)
from home_ai_cluster.core.remote_transport import HttpRemoteTransport
from home_ai_cluster.main import create_app

PROOF_HOST = "127.0.0.1"
PROOF_PORT = 8000
REMOTE_NODE_ID = "declared-remote"


def remote_address(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "http" or parsed.hostname is None:
        raise argparse.ArgumentTypeError(
            "remote address must be an absolute http:// URL"
        )
    return value.rstrip("/")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="home-ai-cluster-fallback-proof")
    parser.add_argument("remote_address", type=remote_address)
    return parser.parse_args(argv)


def create_remote_declaration(address: str) -> RemoteNodeDeclaration:
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


def create_unavailable_local_adapter() -> OllamaAdapter:
    return OllamaAdapter(base_url="http://127.0.0.1:1")


def create_fallback_proof_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=None)


def create_fallback_proof_app(
    address: str,
    *,
    client: httpx.AsyncClient | None = None,
    local_adapter: RuntimeAdapter | None = None,
) -> FastAPI:
    process_client = client or create_fallback_proof_http_client()
    adapter = local_adapter or create_unavailable_local_adapter()
    node_registry = NodeRegistry(
        [
            NodeDescription(
                id="local",
                name="Local node",
                availability="available",
                health=NodeHealth(healthy=True),
                capabilities=[Capability(name="chat")],
                adapters=[adapter.name],
            )
        ]
    )
    adapter_registry = AdapterRegistry([adapter])
    remote_registry = build_remote_node_declaration_registry(
        [create_remote_declaration(address)]
    )
    transport = HttpRemoteTransport(process_client)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await process_client.aclose()

    app = create_app(lifespan=lifespan)

    async def fallback_proof_orchestrator(request):
        return await orchestrate_request_with_automatic_capability_fallback(
            request,
            node_registry,
            adapter_registry,
            remote_registry,
            transport,
        )

    app.state.automatic_proof_orchestrator = fallback_proof_orchestrator
    app.state.fallback_proof_http_client = process_client
    app.state.fallback_proof_remote_registry = remote_registry
    return app


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    uvicorn.run(
        create_fallback_proof_app(args.remote_address),
        host=PROOF_HOST,
        port=PROOF_PORT,
    )
