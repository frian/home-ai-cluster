"""Bounded operator-facing retained configuration commands."""

import argparse
import sys
from collections.abc import Sequence

from home_ai_cluster.local_runtime_composition import (
    LOCAL_RUNTIMES,
    LocalRuntimeCompositionError,
    LocalRuntimeCompositionValues,
    non_empty_value,
    validate_local_runtime_values,
)
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedConfigurationError,
    RetainedLocalConfiguration,
    load_retained_configuration,
    save_retained_configuration,
    validate_external_information_plugin_name,
)
from home_ai_cluster.static_capabilities import (
    DEFAULT_STATIC_CAPABILITY_NAMES,
    validate_static_capabilities,
)
from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration
from home_ai_cluster.static_cluster_validation import remote_base_url, remote_node_id


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="home-ai-cluster config")
    commands = parser.add_subparsers(dest="command", required=True)

    local = commands.add_parser("local")
    local.add_argument("--reset", action="store_true")
    local.add_argument("--runtime", choices=LOCAL_RUNTIMES)
    local.add_argument("--ollama-model", type=non_empty_value)
    local.add_argument("--ollama-disable-thinking", action="store_true")
    local.add_argument("--llama-server-base-url")
    local.add_argument("--llama-server-model", type=non_empty_value)
    local.add_argument("--local-capability", action="append")

    node = commands.add_parser("node")
    node.add_argument("node_id", type=remote_node_id)
    node.add_argument("--remove", action="store_true")
    node.add_argument("--base-url", type=remote_base_url)
    node.add_argument("--capability", action="append")

    external_information = commands.add_parser("external-information")
    external_information.add_argument("--reset", action="store_true")
    external_information.add_argument(
        "--plugin", type=_external_information_plugin_name
    )

    commands.add_parser("show")
    return parser


def _external_information_plugin_name(value: str) -> str:
    try:
        return validate_external_information_plugin_name(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def _validated_capabilities(
    parser: argparse.ArgumentParser,
    values: list[str] | None,
    *,
    subject: str,
) -> tuple[str, ...] | None:
    if values is None:
        return None
    try:
        return validate_static_capabilities(values, subject=subject)
    except ValueError as error:
        parser.error(str(error))


def _local_configuration(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> RetainedLocalConfiguration:
    if args.runtime is None:
        parser.error("--runtime is required unless --reset")
    try:
        base_url = validate_local_runtime_values(
            runtime=args.runtime,
            ollama_model=args.ollama_model,
            ollama_disable_thinking=args.ollama_disable_thinking,
            llama_server_base_url=args.llama_server_base_url,
            llama_server_model=args.llama_server_model,
        )
    except LocalRuntimeCompositionError as error:
        parser.error(str(error))
    return RetainedLocalConfiguration(
        runtime=LocalRuntimeCompositionValues(
            runtime=args.runtime,
            ollama_model=args.ollama_model,
            ollama_disable_thinking=args.ollama_disable_thinking,
            llama_server_base_url=base_url,
            llama_server_model=args.llama_server_model,
        ),
        local_capabilities=_validated_capabilities(
            parser, args.local_capability, subject="local"
        ),
    )


def _node_declaration(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> RemoteNodeDeclaration:
    if args.base_url is None:
        parser.error("--base-url is required unless --remove")
    capabilities = _validated_capabilities(parser, args.capability, subject="remote")
    return RemoteNodeDeclaration(
        node_id=args.node_id,
        base_url=args.base_url,
        capabilities=(
            DEFAULT_STATIC_CAPABILITY_NAMES if capabilities is None else capabilities
        ),
    )


def _validate_reset(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if (
        args.runtime is not None
        or args.ollama_model is not None
        or args.ollama_disable_thinking
        or args.llama_server_base_url is not None
        or args.llama_server_model is not None
        or args.local_capability is not None
    ):
        parser.error("--reset cannot be combined with local configuration options")


def _validate_remove(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.base_url is not None or args.capability is not None:
        parser.error("--remove cannot be combined with node configuration options")


def format_retained_configuration(configuration: RetainedConfiguration) -> str:
    """Format retained facts only, without contacting a runtime or node."""
    lines = ["Local:"]
    if configuration.local is None:
        lines.append("  not configured")
    else:
        local = configuration.local
        values = local.runtime
        lines.append(f"  runtime: {values.runtime}")
        if values.runtime == "ollama":
            lines.extend(
                [
                    f"  ollama model: {values.ollama_model or 'not retained'}",
                    "  ollama disable thinking: "
                    f"{'true' if values.ollama_disable_thinking else 'false'}",
                ]
            )
        else:
            lines.extend(
                [
                    f"  llama-server base URL: {values.llama_server_base_url}",
                    f"  llama-server model: {values.llama_server_model}",
                ]
            )
        lines.append(
            "  caller-local capabilities: "
            + (
                "not retained"
                if local.local_capabilities is None
                else ", ".join(local.local_capabilities)
            )
        )

    lines.append("Remote nodes:")
    if not configuration.remote_nodes:
        lines.append("  none")
    else:
        for node in configuration.remote_nodes:
            lines.extend(
                [
                    f"  {node.node_id}",
                    f"    base URL: {node.base_url}",
                    f"    capabilities: {', '.join(node.capabilities)}",
                ]
            )
    lines.append("External information:")
    if configuration.external_information_plugin is None:
        lines.append("  not configured")
    else:
        lines.append(f"  plugin: {configuration.external_information_plugin}")
    return "\n".join(lines) + "\n"


def _mutate_local(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.reset:
        _validate_reset(parser, args)
        configuration = load_retained_configuration()
        save_retained_configuration(
            RetainedConfiguration(
                local=None,
                remote_nodes=configuration.remote_nodes,
                external_information_plugin=configuration.external_information_plugin,
            )
        )
        print("local configuration reset")
        return
    local = _local_configuration(parser, args)
    configuration = load_retained_configuration()
    save_retained_configuration(
        RetainedConfiguration(
            local=local,
            remote_nodes=configuration.remote_nodes,
            external_information_plugin=configuration.external_information_plugin,
        )
    )
    print("local configuration retained")


def _mutate_node(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.remove:
        _validate_remove(parser, args)
        configuration = load_retained_configuration()
        nodes = tuple(
            node for node in configuration.remote_nodes if node.node_id != args.node_id
        )
        if len(nodes) == len(configuration.remote_nodes):
            print("error: retained node not found", file=sys.stderr)
            raise SystemExit(1)
        save_retained_configuration(
            RetainedConfiguration(
                local=configuration.local,
                remote_nodes=nodes,
                external_information_plugin=configuration.external_information_plugin,
            )
        )
        print("node configuration removed")
        return

    declaration = _node_declaration(parser, args)
    configuration = load_retained_configuration()
    nodes = list(configuration.remote_nodes)
    for index, node in enumerate(nodes):
        if node.node_id == declaration.node_id:
            nodes[index] = declaration
            break
    else:
        nodes.append(declaration)
    save_retained_configuration(
        RetainedConfiguration(
            local=configuration.local,
            remote_nodes=tuple(nodes),
            external_information_plugin=configuration.external_information_plugin,
        )
    )
    print("node configuration retained")


def _mutate_external_information(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    if args.reset and args.plugin is not None:
        parser.error("--reset cannot be combined with --plugin")
    if not args.reset and args.plugin is None:
        parser.error("--plugin is required unless --reset")
    configuration = load_retained_configuration()
    save_retained_configuration(
        RetainedConfiguration(
            local=configuration.local,
            remote_nodes=configuration.remote_nodes,
            external_information_plugin=None if args.reset else args.plugin,
        )
    )
    print(
        "external-information configuration reset"
        if args.reset
        else "external-information configuration retained"
    )


def main(argv: Sequence[str] | None = None) -> None:
    """Manage and inspect retained configuration without startup consumption."""
    parser = _create_argument_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "show":
            sys.stdout.write(
                format_retained_configuration(load_retained_configuration())
            )
        elif args.command == "local":
            _mutate_local(parser, args)
        elif args.command == "node":
            _mutate_node(parser, args)
        else:
            _mutate_external_information(parser, args)
    except RetainedConfigurationError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
