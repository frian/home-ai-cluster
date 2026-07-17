"""Explicit ordinary local runtime application startup."""

import argparse
from collections.abc import Sequence

import uvicorn
from fastapi import FastAPI

from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.api.wiring import LocalAppComposition
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.local_http import local_http_url
from home_ai_cluster.main import create_app

LOCAL_RUNTIME_HOST = "127.0.0.1"
LOCAL_RUNTIME_PORT = 8000


def non_empty_value(value: str) -> str:
    """Require one explicit non-empty operator-supplied value."""
    if not value:
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="home-ai-cluster-local")
    parser.add_argument(
        "--runtime",
        choices=["ollama", "llama-server"],
        default="ollama",
    )
    parser.add_argument("--llama-server-base-url", type=local_http_url)
    parser.add_argument("--llama-server-model", type=non_empty_value)
    parser.add_argument("--host", default=LOCAL_RUNTIME_HOST)
    parser.add_argument("--port", type=int, default=LOCAL_RUNTIME_PORT)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse one explicit ordinary local runtime composition."""
    parser = _create_argument_parser()
    args = parser.parse_args(argv)

    if args.runtime == "ollama":
        if (
            args.llama_server_base_url is not None
            or args.llama_server_model is not None
        ):
            parser.error("llama-server arguments require --runtime llama-server")
        return args

    if args.llama_server_base_url is None:
        parser.error("--llama-server-base-url is required for llama-server")
    if args.llama_server_model is None:
        parser.error("--llama-server-model is required for llama-server")
    return args


def _create_local_node(adapter_name: str) -> NodeDescription:
    return NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=[adapter_name],
    )


def create_ollama_local_app_composition() -> LocalAppComposition:
    """Construct the ordinary local Ollama composition with existing defaults."""
    adapter = OllamaAdapter()
    return LocalAppComposition(
        node_registry=NodeRegistry([_create_local_node(adapter.name)]),
        adapter_registry=AdapterRegistry([adapter]),
    )


def create_llama_server_local_app_composition(
    *,
    base_url: str,
    model: str,
) -> LocalAppComposition:
    """Construct one ordinary local llama-server composition."""
    adapter = LlamaServerAdapter(base_url=base_url, model=model)
    return LocalAppComposition(
        node_registry=NodeRegistry([_create_local_node(adapter.name)]),
        adapter_registry=AdapterRegistry([adapter]),
    )


def create_local_runtime_app(args: argparse.Namespace) -> FastAPI:
    """Construct the ordinary app for the explicitly selected local runtime."""
    if args.runtime == "ollama":
        composition = create_ollama_local_app_composition()
    else:
        composition = create_llama_server_local_app_composition(
            base_url=args.llama_server_base_url,
            model=args.llama_server_model,
        )
    return create_app(local_app_composition=composition)


def main(argv: Sequence[str] | None = None) -> None:
    """Run one ordinary local runtime composition on the selected address."""
    args = parse_args(argv)
    uvicorn.run(
        create_local_runtime_app(args),
        host=args.host,
        port=args.port,
    )
