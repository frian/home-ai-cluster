"""Explicit ordinary local runtime application startup."""

import argparse
from collections.abc import Sequence

import uvicorn
from fastapi import FastAPI

from home_ai_cluster.local_runtime_composition import (
    add_local_runtime_arguments,
    create_local_runtime_composition,
    validate_local_runtime_arguments,
)
from home_ai_cluster.loopback_browser import add_loopback_browser_routes
from home_ai_cluster.main import create_app

LOCAL_RUNTIME_HOST = "127.0.0.1"
LOCAL_RUNTIME_PORT = 8000


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="home-ai-cluster-local")
    add_local_runtime_arguments(parser)
    parser.add_argument("--host", default=LOCAL_RUNTIME_HOST)
    parser.add_argument("--port", type=int, default=LOCAL_RUNTIME_PORT)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse one explicit ordinary local runtime composition."""
    parser = _create_argument_parser()
    args = parser.parse_args(argv)
    validate_local_runtime_arguments(parser, args)
    return args


def create_local_runtime_app(args: argparse.Namespace) -> FastAPI:
    """Construct the ordinary app for the explicitly selected local runtime."""
    composition = create_local_runtime_composition(
        runtime=args.runtime,
        ollama_model=args.ollama_model,
        llama_server_base_url=args.llama_server_base_url,
        llama_server_model=args.llama_server_model,
    )
    app = create_app(local_app_composition=composition)
    if args.host == LOCAL_RUNTIME_HOST:
        return add_loopback_browser_routes(app)
    return app


def main(argv: Sequence[str] | None = None) -> None:
    """Run one ordinary local runtime composition on the selected address."""
    args = parse_args(argv)
    uvicorn.run(
        create_local_runtime_app(args),
        host=args.host,
        port=args.port,
    )
