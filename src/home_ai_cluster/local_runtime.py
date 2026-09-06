"""Explicit ordinary local runtime application startup."""

import argparse
from collections.abc import Sequence

import uvicorn
from fastapi import FastAPI

from home_ai_cluster.local_runtime_composition import (
    MultiBindingRuntimeCompositionValues,
    add_local_runtime_arguments,
    create_local_runtime_composition,
    create_multi_binding_local_app_composition,
    resolve_local_runtime_composition_values,
    validate_local_runtime_arguments,
)
from home_ai_cluster.main import create_app
from home_ai_cluster.retained_configuration import (
    RetainedConfigurationError,
    load_retained_configuration,
    retained_configuration_file,
)
from home_ai_cluster.web.loopback_browser import add_loopback_browser_routes

LOCAL_RUNTIME_HOST = "127.0.0.1"
LOCAL_RUNTIME_PORT = 25042


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="home-ai-cluster-local",
        description=(
            "Run one foreground local HAC process with an operator-managed runtime."
        ),
    )
    add_local_runtime_arguments(parser)
    parser.add_argument(
        "--host", default=LOCAL_RUNTIME_HOST, help="Address on which to serve HAC."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=LOCAL_RUNTIME_PORT,
        help="Port on which to serve HAC.",
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse one explicit ordinary local runtime composition."""
    parser = _create_argument_parser()
    if argv in (["-h"], ["--help"]):
        parser.prog = "home-ai-cluster local"
    args = parser.parse_args(argv)
    retained_values = None
    needs_retained_runtime = args.runtime_config is None
    if needs_retained_runtime or retained_configuration_file().exists():
        try:
            retained = load_retained_configuration()
        except RetainedConfigurationError as error:
            parser.error(str(error))
        if retained.local is not None:
            if needs_retained_runtime:
                retained_values = retained.local.runtime
            args.retained_execution_limit = retained.local.execution_limit
    validate_local_runtime_arguments(parser, args, retained_values)
    return args


def create_local_runtime_app(args: argparse.Namespace) -> FastAPI:
    """Construct the ordinary app for the explicitly selected local runtime."""
    values = resolve_local_runtime_composition_values(_create_argument_parser(), args)
    execution_limit = getattr(args, "retained_execution_limit", 1) or 1
    if isinstance(values, MultiBindingRuntimeCompositionValues):
        composition = create_multi_binding_local_app_composition(
            values, execution_limit=execution_limit
        )
        app = create_app(local_app_composition=composition)
        if args.host == LOCAL_RUNTIME_HOST:
            return add_loopback_browser_routes(app)
        return app
    composition_arguments = dict(
        runtime=values.runtime,
        ollama_model=values.ollama_model,
        ollama_disable_thinking=values.ollama_disable_thinking,
        llama_server_base_url=values.llama_server_base_url,
        llama_server_model=values.llama_server_model,
        vllm_base_url=values.vllm_base_url,
        vllm_model=values.vllm_model,
    )
    if getattr(args, "retained_execution_limit", None) is not None:
        composition_arguments["execution_limit"] = args.retained_execution_limit
    composition = create_local_runtime_composition(**composition_arguments)
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
