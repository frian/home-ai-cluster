"""Concrete local compositions for the supported ordinary runtimes."""

import argparse

from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.api.wiring import LocalAppComposition
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.local_http import local_http_url

LOCAL_RUNTIMES = ("ollama", "llama-server")


class LocalRuntimeCompositionError(ValueError):
    """Raised when one concrete local runtime composition is invalid."""


def non_empty_value(value: str) -> str:
    """Require one explicit non-empty operator-supplied value."""
    if not value:
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def add_local_runtime_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the closed local runtime argument set to one ordinary parser."""
    parser.add_argument(
        "--runtime",
        choices=LOCAL_RUNTIMES,
        default="ollama",
    )
    parser.add_argument("--llama-server-base-url", type=local_http_url)
    parser.add_argument("--llama-server-model", type=non_empty_value)


def validate_local_runtime_values(
    *,
    runtime: str,
    llama_server_base_url: str | None,
    llama_server_model: str | None,
) -> str | None:
    """Validate local runtime values and normalize a llama-server base URL."""
    if runtime not in LOCAL_RUNTIMES:
        raise LocalRuntimeCompositionError("runtime must be ollama or llama-server")

    if runtime == "ollama":
        if llama_server_base_url is not None or llama_server_model is not None:
            raise LocalRuntimeCompositionError(
                "llama-server arguments require --runtime llama-server"
            )
        return None

    if llama_server_base_url is None:
        raise LocalRuntimeCompositionError(
            "--llama-server-base-url is required for llama-server"
        )
    if llama_server_model is None:
        raise LocalRuntimeCompositionError(
            "--llama-server-model is required for llama-server"
        )
    if not llama_server_model:
        raise LocalRuntimeCompositionError("value must not be empty")

    try:
        return local_http_url(llama_server_base_url)
    except argparse.ArgumentTypeError as error:
        raise LocalRuntimeCompositionError(str(error)) from error


def validate_local_runtime_arguments(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    """Apply shared local runtime validation through the supplied parser."""
    try:
        validate_local_runtime_values(
            runtime=args.runtime,
            llama_server_base_url=args.llama_server_base_url,
            llama_server_model=args.llama_server_model,
        )
    except LocalRuntimeCompositionError as error:
        parser.error(str(error))


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


def create_local_runtime_composition(
    *,
    runtime: str,
    llama_server_base_url: str | None = None,
    llama_server_model: str | None = None,
) -> LocalAppComposition:
    """Validate and construct one supported ordinary local composition."""
    base_url = validate_local_runtime_values(
        runtime=runtime,
        llama_server_base_url=llama_server_base_url,
        llama_server_model=llama_server_model,
    )

    if runtime == "ollama":
        return create_ollama_local_app_composition()

    assert base_url is not None
    assert llama_server_model is not None
    return create_llama_server_local_app_composition(
        base_url=base_url,
        model=llama_server_model,
    )
