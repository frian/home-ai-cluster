"""Ordinary static local-plus-remote application process."""

import argparse
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI

from home_ai_cluster.api.wiring import (
    LocalAppComposition,
    build_static_remote_collection_wiring,
    build_static_remote_wiring,
)
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.remote_transport import HttpRemoteTransport
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.core.static_capabilities import (
    DEFAULT_STATIC_CAPABILITY_NAMES,
    validate_static_capabilities,
)
from home_ai_cluster.local_runtime_composition import (
    add_local_runtime_arguments,
    create_local_runtime_composition,
    resolve_local_runtime_composition_values,
    validate_local_runtime_arguments,
)
from home_ai_cluster.main import create_app
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedConfigurationError,
    load_retained_configuration,
)
from home_ai_cluster.static_cluster_declaration import (
    RemoteNodeDeclaration as ParsedRemoteNodeDeclaration,
)
from home_ai_cluster.static_cluster_declaration import (
    StaticClusterDeclarationError,
    load_static_cluster_declarations,
)
from home_ai_cluster.static_cluster_validation import (
    LOCAL_NODE_ID,  # noqa: F401
    remote_base_url,
    remote_node_id,
)
from home_ai_cluster.web.loopback_browser import add_loopback_browser_routes

STATIC_CLUSTER_HOST = "127.0.0.1"
STATIC_CLUSTER_PORT = 25042
REMOTE_HTTP_ADAPTER_NAME = "remote-http"
"""Cluster-facing label for caller-side declared remote HTTP execution."""


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="home-ai-cluster-static-cluster",
        description="Run one foreground explicit local-plus-remote static HAC process.",
    )
    parser.add_argument(
        "-d",
        "--declaration",
        type=Path,
        help="Explicit static topology declaration file.",
    )
    parser.add_argument(
        "--remote-node-id",
        type=remote_node_id,
        help="ID for one inline static remote node.",
    )
    parser.add_argument(
        "--remote-base-url",
        type=remote_base_url,
        help="Base URL for one inline static remote node.",
    )
    parser.add_argument(
        "--local-capability",
        action="append",
        help="Caller-local routing capability; repeat as needed.",
    )
    parser.add_argument(
        "--remote-capability",
        action="append",
        help="Inline remote capability; repeat as needed.",
    )
    add_local_runtime_arguments(parser)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse exactly one complete static topology input mode."""
    parser = _create_argument_parser()
    if argv in (["-h"], ["--help"]):
        parser.prog = "home-ai-cluster static-cluster"
    args = parser.parse_args(argv)

    has_declaration = args.declaration is not None
    has_remote_node_id = args.remote_node_id is not None
    has_remote_base_url = args.remote_base_url is not None
    has_local_capabilities = args.local_capability is not None
    has_remote_capabilities = args.remote_capability is not None

    if has_declaration and (
        has_remote_node_id
        or has_remote_base_url
        or has_local_capabilities
        or has_remote_capabilities
    ):
        parser.error("--declaration cannot be combined with inline topology arguments")

    if has_local_capabilities and (not has_remote_node_id or not has_remote_base_url):
        parser.error(
            "--local-capability requires --remote-node-id and --remote-base-url"
        )

    if has_remote_capabilities and (not has_remote_node_id or not has_remote_base_url):
        parser.error(
            "--remote-capability requires --remote-node-id and --remote-base-url"
        )

    if has_remote_node_id != has_remote_base_url:
        parser.error("--remote-node-id and --remote-base-url must be provided together")

    if has_remote_capabilities:
        try:
            args.remote_capability = validate_static_capabilities(
                args.remote_capability,
                subject="remote",
            )
        except ValueError as exc:
            parser.error(str(exc))
    else:
        args.remote_capability = DEFAULT_STATIC_CAPABILITY_NAMES

    if has_local_capabilities:
        try:
            args.local_capability = validate_static_capabilities(
                args.local_capability,
                subject="local",
            )
        except ValueError as exc:
            parser.error(str(exc))
    else:
        args.local_capability = DEFAULT_STATIC_CAPABILITY_NAMES

    needs_retained_runtime = args.runtime_config is None
    needs_retained_topology = not has_declaration and not has_remote_node_id
    retained = RetainedConfiguration()
    if needs_retained_runtime or needs_retained_topology:
        try:
            retained = load_retained_configuration()
        except RetainedConfigurationError as error:
            parser.error(str(error))

    retained_values = retained.local.runtime if retained.local is not None else None
    if needs_retained_runtime and retained.local is not None:
        args.retained_execution_limit = retained.local.execution_limit
    validate_local_runtime_arguments(
        parser,
        args,
        retained_values if needs_retained_runtime else None,
    )
    if needs_retained_topology:
        if not retained.remote_nodes:
            parser.error(
                "provide --declaration, complete inline remote arguments, "
                "or retained topology"
            )
        args.retained_remote_nodes = retained.remote_nodes
        args.local_capability = (
            retained.local.local_capabilities
            if retained.local is not None
            and retained.local.local_capabilities is not None
            else DEFAULT_STATIC_CAPABILITY_NAMES
        )
    return args


def create_remote_declaration(
    node_id: str,
    base_url: str,
    capabilities: Sequence[str] = DEFAULT_STATIC_CAPABILITY_NAMES,
) -> RemoteNodeDeclaration:
    """Create one static runtime remote declaration for this process."""
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id=node_id,
            name=f"Declared remote node {node_id}",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name=name) for name in capabilities],
            adapters=[REMOTE_HTTP_ADAPTER_NAME],
        ),
        transport_address=base_url,
    )


def create_static_cluster_http_client() -> httpx.AsyncClient:
    """Create the process-owned remote client without a model read timeout."""
    return httpx.AsyncClient(timeout=None, trust_env=False)


def _create_lifespan(
    process_client: httpx.AsyncClient,
):
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await process_client.aclose()

    return lifespan


def create_static_cluster_app(
    node_id: str,
    base_url: str,
    *,
    capabilities: Sequence[str] = DEFAULT_STATIC_CAPABILITY_NAMES,
    local_app_composition: LocalAppComposition,
    client: httpx.AsyncClient | None = None,
) -> FastAPI:
    """Construct the ordinary static local-plus-one-remote application."""
    process_client = client or create_static_cluster_http_client()
    wiring = build_static_remote_wiring(
        node_registry=local_app_composition.node_registry,
        adapter_registry=local_app_composition.adapter_registry,
        remote_declaration=create_remote_declaration(node_id, base_url, capabilities),
        remote_transport=HttpRemoteTransport(process_client),
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
        execution_intervals=local_app_composition.execution_intervals,
    )
    app = create_app(
        local_app_composition=local_app_composition,
        static_remote_wiring=wiring,
        lifespan=_create_lifespan(process_client),
    )
    app.state.static_cluster_http_client = process_client
    return app


def create_static_cluster_collection_app(
    remote_nodes: Sequence[ParsedRemoteNodeDeclaration],
    *,
    local_app_composition: LocalAppComposition,
    client: httpx.AsyncClient | None = None,
) -> FastAPI:
    """Construct an application retaining one ordered remote collection."""
    process_client = client or create_static_cluster_http_client()
    declarations = [
        create_remote_declaration(
            remote.node_id,
            remote.base_url,
            remote.capabilities,
        )
        for remote in remote_nodes
    ]
    wiring = build_static_remote_collection_wiring(
        node_registry=local_app_composition.node_registry,
        adapter_registry=local_app_composition.adapter_registry,
        remote_declarations=declarations,
        remote_transport=HttpRemoteTransport(process_client),
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
        execution_intervals=local_app_composition.execution_intervals,
    )
    app = create_app(
        local_app_composition=local_app_composition,
        static_remote_collection_wiring=wiring,
        lifespan=_create_lifespan(process_client),
    )
    app.state.static_cluster_http_client = process_client
    return app


def main(argv: Sequence[str] | None = None) -> None:
    """Run one ordinary loopback-only static multi-node application process."""
    args = parse_args(argv)
    values = resolve_local_runtime_composition_values(_create_argument_parser(), args)

    composition_arguments = dict(
        runtime=values.runtime,
        ollama_model=values.ollama_model,
        ollama_disable_thinking=values.ollama_disable_thinking,
        llama_server_base_url=values.llama_server_base_url,
        llama_server_model=values.llama_server_model,
    )
    if getattr(args, "retained_execution_limit", None) is not None:
        composition_arguments["execution_limit"] = args.retained_execution_limit

    if args.declaration is not None:
        try:
            declarations = load_static_cluster_declarations(args.declaration)
        except StaticClusterDeclarationError as exc:
            _create_argument_parser().error(str(exc))
        local_app_composition = create_local_runtime_composition(
            **composition_arguments,
            capabilities=declarations.local_capabilities,
        )
        app = create_static_cluster_collection_app(
            declarations.remote_nodes,
            local_app_composition=local_app_composition,
        )
    elif args.remote_node_id is not None:
        local_app_composition = create_local_runtime_composition(
            **composition_arguments,
            capabilities=args.local_capability,
        )
        app = create_static_cluster_app(
            args.remote_node_id,
            args.remote_base_url,
            capabilities=args.remote_capability,
            local_app_composition=local_app_composition,
        )
    else:
        local_app_composition = create_local_runtime_composition(
            **composition_arguments,
            capabilities=args.local_capability,
        )
        app = create_static_cluster_collection_app(
            args.retained_remote_nodes,
            local_app_composition=local_app_composition,
        )

    uvicorn.run(
        add_loopback_browser_routes(app),
        host=STATIC_CLUSTER_HOST,
        port=STATIC_CLUSTER_PORT,
    )
