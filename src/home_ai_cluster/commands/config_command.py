"""Bounded operator-facing retained configuration commands."""

import argparse
import sys
from collections.abc import Sequence

from home_ai_cluster.core.static_capabilities import (
    DEFAULT_STATIC_CAPABILITY_NAMES,
    validate_static_capabilities,
)
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
    remove_retained_configuration,
    save_retained_configuration,
    validate_external_information_plugin_name,
)
from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration
from home_ai_cluster.static_cluster_validation import remote_base_url, remote_node_id


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="home-ai-cluster config",
        description="Manage retained Home AI Cluster configuration.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    local = commands.add_parser(
        "local",
        help=(
            "Configure or reset retained local runtime composition and routing "
            "capabilities."
        ),
        description=(
            "Configure or reset retained local runtime composition and routing "
            "capabilities."
        ),
    )
    local.add_argument(
        "--reset", action="store_true", help="Clear retained local configuration."
    )
    local.add_argument(
        "--runtime", choices=LOCAL_RUNTIMES, help="Retained local runtime."
    )
    local.add_argument(
        "--ollama-model", type=non_empty_value, help="Retained Ollama model identifier."
    )
    local.add_argument(
        "--ollama-disable-thinking",
        action="store_true",
        help="Retain disabled Ollama thinking.",
    )
    local.add_argument(
        "--llama-server-base-url", help="Retained llama-server base URL."
    )
    local.add_argument(
        "--llama-server-model",
        type=non_empty_value,
        help="Retained llama-server model identifier.",
    )
    local.add_argument(
        "--local-capability",
        action="append",
        help="Retained caller-local routing capability; repeat as needed.",
    )

    node = commands.add_parser(
        "node",
        help="Add, update, or remove one retained explicit static remote node.",
        description="Add, update, or remove one retained explicit static remote node.",
    )
    node.add_argument(
        "node_id", type=remote_node_id, help="Operator-chosen static remote node ID."
    )
    node.add_argument(
        "--remove", action="store_true", help="Remove this retained remote node."
    )
    node.add_argument(
        "--base-url",
        type=remote_base_url,
        help="Retained base URL for this static remote node.",
    )
    node.add_argument(
        "--capability",
        action="append",
        help="Retained remote capability; repeat as needed.",
    )

    external_information = commands.add_parser(
        "external-information",
        help="Configure or reset the retained external-information plugin choice.",
        description=(
            "Configure or reset the retained external-information plugin choice."
        ),
    )
    external_information.add_argument(
        "--reset", action="store_true", help="Clear the retained plugin name."
    )
    external_information.add_argument(
        "--plugin",
        type=_external_information_plugin_name,
        help="Exact plugin name to retain; no plugin is contacted.",
    )

    chat = commands.add_parser(
        "chat",
        help=(
            "Configure or reset retained Chat external-information fallback "
            "authorization."
        ),
        description=(
            "Configure or reset retained Chat external-information fallback "
            "authorization."
        ),
    )
    chat.add_argument(
        "--reset",
        action="store_true",
        help="Clear retained Chat fallback authorization.",
    )
    chat.add_argument(
        "--external-information-fallback",
        action="store_true",
        help="Retain operator authorization for eligible one-shot Chat fallback.",
    )

    commands.add_parser(
        "reset",
        help="Clear all retained configuration.",
        description="Clear all retained configuration.",
    )

    commands.add_parser(
        "show",
        help=(
            "Print retained configuration only, without runtime or network observation."
        ),
        description=(
            "Print retained configuration only, without runtime or network observation."
        ),
    )
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
    lines.append("Chat external information:")
    lines.append(
        "  automatic fallback: "
        + (
            "authorized"
            if configuration.chat_external_information_fallback
            else "not authorized"
        )
    )
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
                chat_external_information_fallback=(
                    configuration.chat_external_information_fallback
                ),
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
            chat_external_information_fallback=(
                configuration.chat_external_information_fallback
            ),
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
                chat_external_information_fallback=(
                    configuration.chat_external_information_fallback
                ),
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
            chat_external_information_fallback=(
                configuration.chat_external_information_fallback
            ),
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
            chat_external_information_fallback=(
                configuration.chat_external_information_fallback
            ),
        )
    )
    print(
        "external-information configuration reset"
        if args.reset
        else "external-information configuration retained"
    )


def _mutate_chat(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.reset and args.external_information_fallback:
        parser.error("--reset cannot be combined with --external-information-fallback")
    if not args.reset and not args.external_information_fallback:
        parser.error("--external-information-fallback is required unless --reset")
    configuration = load_retained_configuration()
    save_retained_configuration(
        RetainedConfiguration(
            local=configuration.local,
            remote_nodes=configuration.remote_nodes,
            external_information_plugin=configuration.external_information_plugin,
            chat_external_information_fallback=not args.reset,
        )
    )
    print("chat configuration reset" if args.reset else "chat configuration retained")


def _reset_retained_configuration() -> None:
    remove_retained_configuration()
    print("retained configuration reset")


def main(argv: Sequence[str] | None = None) -> None:
    """Manage and inspect retained configuration without startup consumption."""
    parser = _create_argument_parser()
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        parser.print_help()
        return

    args = parser.parse_args(arguments)
    try:
        if args.command == "show":
            sys.stdout.write(
                format_retained_configuration(load_retained_configuration())
            )
        elif args.command == "reset":
            _reset_retained_configuration()
        elif args.command == "local":
            _mutate_local(parser, args)
        elif args.command == "node":
            _mutate_node(parser, args)
        elif args.command == "chat":
            _mutate_chat(parser, args)
        else:
            _mutate_external_information(parser, args)
    except RetainedConfigurationError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
