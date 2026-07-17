"""Proof-scoped receiving application for the Phase 12 heterogeneous proof."""

import argparse
from collections.abc import Sequence

import uvicorn
from fastapi import FastAPI

from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.main import create_proof_receiving_app
from home_ai_cluster.phase_5_runtime_adapter_proof import local_http_url

PROOF_RECEIVER_HOST = "0.0.0.0"
PROOF_RECEIVER_PORT = 8000
PROOF_RECEIVER_NODE_ID = "phase-12-receiver"


def non_empty_value(value: str) -> str:
    """Require an explicit non-empty operator-owned proof value."""
    if not value:
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the small explicit receiver configuration for this proof only."""
    parser = argparse.ArgumentParser(
        prog="home-ai-cluster-phase-12-heterogeneous-receiver",
        description="Run the Phase 12 proof-scoped llama-server receiving app.",
    )
    parser.add_argument("--host", default=PROOF_RECEIVER_HOST)
    parser.add_argument("--port", type=int, default=PROOF_RECEIVER_PORT)
    parser.add_argument("--llama-server-base-url", type=local_http_url, required=True)
    parser.add_argument("--llama-server-model", type=non_empty_value, required=True)
    return parser.parse_args(argv)


def create_phase_12_receiver_app(
    *,
    llama_server_base_url: str,
    llama_server_model: str,
) -> FastAPI:
    """Compose the one explicit llama-server receiving application for Phase 12."""
    adapter = LlamaServerAdapter(
        base_url=llama_server_base_url,
        model=llama_server_model,
    )
    node_registry = NodeRegistry(
        [
            NodeDescription(
                id=PROOF_RECEIVER_NODE_ID,
                name="Phase 12 proof receiver",
                availability="available",
                health=NodeHealth(healthy=True),
                capabilities=[Capability(name="chat")],
                adapters=[adapter.name],
            )
        ]
    )
    adapter_registry = AdapterRegistry([adapter])
    return create_proof_receiving_app(
        node_registry=node_registry,
        adapter_registry=adapter_registry,
    )


def main(argv: Sequence[str] | None = None) -> None:
    """Run the explicit operator-managed receiver for the Phase 12 proof."""
    args = parse_args(argv)
    uvicorn.run(
        create_phase_12_receiver_app(
            llama_server_base_url=args.llama_server_base_url,
            llama_server_model=args.llama_server_model,
        ),
        host=args.host,
        port=args.port,
    )
