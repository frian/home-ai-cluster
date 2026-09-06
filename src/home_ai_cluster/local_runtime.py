"""Explicit ordinary local runtime application startup."""

import argparse
import asyncio
import ipaddress
from collections.abc import Sequence
from contextlib import contextmanager

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
from home_ai_cluster.main import create_app, create_receiver_app
from home_ai_cluster.retained_configuration import (
    RetainedConfigurationError,
    load_retained_configuration,
    retained_configuration_file,
)
from home_ai_cluster.web.loopback_browser import add_loopback_browser_routes

LOCAL_RUNTIME_HOST = "127.0.0.1"
LOCAL_RUNTIME_PORT = 25042


class _ReceiverServer(uvicorn.Server):
    """Receiver server that leaves foreground process signals to native HAC."""

    @contextmanager
    def capture_signals(self):
        yield


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
    parser.add_argument(
        "--receiver-host",
        help="Concrete non-loopback IP address on which to serve the HAC receiver.",
    )
    parser.add_argument(
        "--receiver-port",
        type=int,
        help="Port on which to serve the HAC receiver.",
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
    if args.host != LOCAL_RUNTIME_HOST:
        parser.error("--host must be exactly 127.0.0.1")
    if args.receiver_port is not None and args.receiver_host is None:
        parser.error("--receiver-port requires --receiver-host")
    if args.receiver_host is not None:
        try:
            receiver_address = ipaddress.ip_address(args.receiver_host)
        except ValueError:
            parser.error("--receiver-host must be a concrete non-loopback IP address")
        if receiver_address.is_loopback or receiver_address.is_unspecified:
            parser.error("--receiver-host must be a concrete non-loopback IP address")
        if args.receiver_port is None:
            args.receiver_port = LOCAL_RUNTIME_PORT
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
        return add_loopback_browser_routes(app)
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
    return add_loopback_browser_routes(app)


async def _serve_until_sibling_stops(
    server: uvicorn.Server, sibling: uvicorn.Server
) -> None:
    """Keep both receiver-enabled authorities in one foreground lifecycle."""
    try:
        await server.serve()
    finally:
        sibling.should_exit = True


async def _run_receiver_enabled_servers(
    native_app: FastAPI, receiver_app: FastAPI, args: argparse.Namespace
) -> None:
    """Run the two explicit authorities over one shared composition."""
    native_server = uvicorn.Server(
        uvicorn.Config(native_app, host=LOCAL_RUNTIME_HOST, port=args.port)
    )
    receiver_server = _ReceiverServer(
        uvicorn.Config(receiver_app, host=args.receiver_host, port=args.receiver_port)
    )
    async with asyncio.TaskGroup() as task_group:
        task_group.create_task(
            _serve_until_sibling_stops(native_server, receiver_server)
        )
        task_group.create_task(
            _serve_until_sibling_stops(receiver_server, native_server)
        )


def main(argv: Sequence[str] | None = None) -> None:
    """Run one ordinary local runtime composition on the selected address."""
    args = parse_args(argv)
    if args.receiver_host is not None:
        native_app = create_local_runtime_app(args)
        receiver_app = create_receiver_app(
            local_app_composition=native_app.state.local_app_composition
        )
        asyncio.run(_run_receiver_enabled_servers(native_app, receiver_app, args))
        return
    uvicorn.run(
        create_local_runtime_app(args),
        host=args.host,
        port=args.port,
    )
