"""Loopback-only process for RFC-0031 compatibility access."""

import argparse
from collections.abc import Sequence
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from home_ai_cluster.api.openai_compatibility import (
    ProofObservationState,
    compatibility_router,
)
from home_ai_cluster.api.wiring import LocalAppComposition
from home_ai_cluster.local_runtime_composition import create_local_runtime_composition
from home_ai_cluster.main import create_app
from home_ai_cluster.static_cluster import create_static_cluster_collection_app
from home_ai_cluster.static_cluster_declaration import (
    RemoteNodeDeclaration,
    StaticClusterDeclarationError,
    load_static_cluster_declarations,
)

COMPATIBILITY_HOST = "127.0.0.1"
COMPATIBILITY_PORT = 8001


def create_openai_compatibility_app() -> FastAPI:
    """Create the dedicated app without changing the ordinary application."""
    app = create_app()
    app.include_router(compatibility_router)
    return app


def create_static_cluster_openai_compatibility_app(
    remote_nodes: Sequence[RemoteNodeDeclaration],
    *,
    local_app_composition: LocalAppComposition,
    proof_observation: bool = False,
) -> FastAPI:
    """Add RFC-0031 access to one ordinary static-cluster application."""
    app = create_static_cluster_collection_app(
        remote_nodes,
        local_app_composition=local_app_composition,
    )
    if proof_observation:
        app.state.proof_observation_state = ProofObservationState()
    app.include_router(compatibility_router)
    return app


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="home-ai-cluster-openai-compatibility")
    parser.add_argument("--declaration", type=Path)
    parser.add_argument("--proof-observation", action="store_true")
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the local-only default or one explicit static declaration."""
    parser = _create_argument_parser()
    args = parser.parse_args(argv)
    if args.proof_observation and args.declaration is None:
        parser.error("--proof-observation requires --declaration")
    return args


def main(argv: Sequence[str] | None = None) -> None:
    """Run the RFC-0031 compatibility process on loopback only."""
    args = parse_args(argv)

    if args.declaration is None:
        app = create_openai_compatibility_app()
    else:
        try:
            declarations = load_static_cluster_declarations(args.declaration)
        except StaticClusterDeclarationError as exc:
            _create_argument_parser().error(str(exc))
        if args.proof_observation:
            app = create_static_cluster_openai_compatibility_app(
                declarations.remote_nodes,
                local_app_composition=create_local_runtime_composition(
                    runtime="ollama"
                ),
                proof_observation=True,
            )
        else:
            app = create_static_cluster_openai_compatibility_app(
                declarations.remote_nodes,
                local_app_composition=create_local_runtime_composition(
                    runtime="ollama"
                ),
            )

    uvicorn.run(
        app,
        host=COMPATIBILITY_HOST,
        port=COMPATIBILITY_PORT,
    )
