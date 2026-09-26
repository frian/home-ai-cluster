"""Bounded operator-facing retained configuration commands."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from home_ai_cluster.core.static_capabilities import (
    DEFAULT_STATIC_CAPABILITY_NAMES,
    validate_static_capabilities,
)
from home_ai_cluster.local_http import local_http_url
from home_ai_cluster.local_runtime_composition import (
    LOCAL_RUNTIMES,
    LocalCapabilityBindingValues,
    LocalRuntimeCompositionError,
    LocalRuntimeCompositionValues,
    MultiBindingRuntimeCompositionValues,
    load_local_runtime_config,
    load_retained_multi_binding_runtime_config,
    non_empty_value,
    temperature_value,
)
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedConfigurationError,
    RetainedLocalConfiguration,
    build_retained_image_generation_configuration,
    build_retained_local_configuration,
    build_retained_remote_node_declaration,
    load_retained_configuration,
    mutate_retained_local_binding,
    mutate_retained_local_capabilities,
    mutate_retained_remote_capabilities,
    remove_retained_configuration,
    remove_retained_remote_node,
    replace_retained_external_information_plugin,
    replace_retained_image_generation_configuration,
    replace_retained_local_configuration,
    replace_retained_local_runtime_composition,
    replace_retained_remote_node,
    reset_retained_image_generation_configuration,
    reset_retained_local_configuration,
    set_retained_chat_external_information_fallback,
    set_retained_execution_limit,
    validate_external_information_plugin_name,
)
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

    image_generation = commands.add_parser(
        "image-generation",
        help="Configure or reset the retained local Image Generation companion.",
        description="Configure or reset the retained local Image Generation companion.",
    )
    image_generation.add_argument(
        "--reset",
        action="store_true",
        help="Clear the retained Image Generation companion.",
    )
    image_generation.add_argument(
        "--base-url",
        type=local_http_url,
        help="Retained stable-diffusion.cpp loopback HTTP base URL.",
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
    local.add_argument("--vllm-base-url", help="Retained vLLM base URL.")
    local.add_argument(
        "--temperature",
        type=temperature_value,
        help="Finite non-negative retained local free-text sampling temperature.",
    )
    local.add_argument(
        "--vllm-model",
        type=non_empty_value,
        help="Retained vLLM served-model identity.",
    )
    local.add_argument(
        "--local-capability",
        action="append",
        help="Retained caller-local routing capability; repeat as needed.",
    )
    local.add_argument(
        "--execution-limit",
        type=_execution_limit,
        help="Retained HAC execution limit.",
    )
    local.add_argument(
        "--runtime-config",
        type=Path,
        help="Validate and retain one complete RFC-0110 multi-binding runtime config.",
    )
    local_actions = local.add_subparsers(dest="local_action")
    binding = local_actions.add_parser(
        "binding", help="Mutate complete local bindings."
    )
    binding_actions = binding.add_subparsers(dest="binding_action", required=True)
    for action in ("add", "replace"):
        mutation = binding_actions.add_parser(action)
        if action == "replace":
            mutation.add_argument(
                "--owning", required=True, help="Currently owned capability."
            )
        _add_binding_arguments(mutation)
    remove_binding = binding_actions.add_parser("remove")
    remove_binding.add_argument(
        "--owning", required=True, help="Currently owned capability."
    )
    capability = local_actions.add_parser(
        "capability", help="Mutate caller-local routing capabilities."
    )
    capability_actions = capability.add_subparsers(
        dest="local_capability_action", required=True
    )
    for action in ("add", "remove"):
        mutation = capability_actions.add_parser(action)
        mutation.add_argument("capability")
    capability_actions.add_parser("clear")
    execution_limit = local_actions.add_parser(
        "execution-limit", help="Set the retained HAC execution limit."
    )
    execution_limit_actions = execution_limit.add_subparsers(
        dest="execution_limit_action", required=True
    )
    set_limit = execution_limit_actions.add_parser("set")
    set_limit.add_argument("limit", type=_execution_limit)
    execution_limit_actions.add_parser("clear")

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
    node_actions = node.add_subparsers(dest="node_action")
    node_capability = node_actions.add_parser(
        "capability", help="Mutate this node's retained capabilities."
    )
    node_capability_actions = node_capability.add_subparsers(
        dest="node_capability_action", required=True
    )
    for action in ("add", "remove"):
        mutation = node_capability_actions.add_parser(action)
        mutation.add_argument("capability")

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


def _execution_limit(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "execution limit must be a positive integer"
        ) from error
    if parsed <= 0:
        raise argparse.ArgumentTypeError("execution limit must be a positive integer")
    return parsed


def _add_binding_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--capability", action="append", help="Owned capability; repeat as needed."
    )
    parser.add_argument(
        "--runtime", choices=("ollama", "llama-server", "vllm", "ollaya")
    )
    parser.add_argument("--model", type=non_empty_value)
    parser.add_argument("--base-url")
    parser.add_argument("--disable-thinking", action="store_true")
    parser.add_argument("--temperature", type=temperature_value)


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
        return build_retained_local_configuration(
            runtime=args.runtime,
            ollama_model=args.ollama_model,
            ollama_disable_thinking=args.ollama_disable_thinking,
            llama_server_base_url=args.llama_server_base_url,
            llama_server_model=args.llama_server_model,
            vllm_base_url=args.vllm_base_url,
            vllm_model=args.vllm_model,
            temperature=args.temperature,
            local_capabilities=args.local_capability,
            execution_limit=args.execution_limit,
        )
    except LocalRuntimeCompositionError as error:
        parser.error(str(error))
    except ValueError as error:
        parser.error(str(error))


def _binding_from_arguments(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> LocalCapabilityBindingValues:
    capabilities = getattr(args, "capability", None)
    runtime = getattr(args, "runtime", None)
    model = getattr(args, "model", None)
    base_url = getattr(args, "base_url", None)
    disable_thinking = getattr(args, "disable_thinking", False)
    temperature = getattr(args, "temperature", None)
    if (
        capabilities is None
        and runtime is None
        and model is None
        and base_url is None
        and not disable_thinking
        and temperature is None
    ):
        if not sys.stdin.isatty():
            parser.error(
                "complete binding facts are required when standard input is not a "
                "terminal"
            )
        runtime = input("Runtime: ").strip()
        capabilities = [
            value.strip()
            for value in input("Capabilities (comma-separated): ").split(",")
        ]
        base_url = input("Base URL (blank for Ollama): ").strip() or None
        model = input("Model (blank for default Ollama): ").strip() or None
        if runtime == "ollama":
            disable_thinking = input("Disable thinking? [y/N] ").strip().lower() in {
                "y",
                "yes",
            }
        if runtime != "ollaya":
            temperature_input = input("Temperature (blank for default): ").strip()
            if temperature_input:
                try:
                    temperature = temperature_value(temperature_input)
                except argparse.ArgumentTypeError as error:
                    parser.error(str(error))
        if input("Apply? [y/N] ").strip().lower() not in {"y", "yes"}:
            raise ValueError("interactive configuration cancelled")
    elif runtime is None or capabilities is None:
        parser.error("complete binding requires --capability and --runtime")
    document: dict[str, object] = {
        "capabilities": capabilities,
        "runtime": runtime,
    }
    if model is not None:
        document["model"] = model
    if base_url is not None:
        document["base_url"] = base_url
    if disable_thinking:
        document["disable_thinking"] = True
    if temperature is not None:
        document["temperature"] = temperature
    try:
        return load_retained_multi_binding_runtime_config(
            {"bindings": [document]}
        ).bindings[0]
    except LocalRuntimeCompositionError as error:
        parser.error(str(error))


def _mutate_local_binding(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    action = args.binding_action
    try:
        binding = None if action == "remove" else _binding_from_arguments(parser, args)
        mutate_retained_local_binding(
            action, binding=binding, owning_capability=getattr(args, "owning", None)
        )
    except (LocalRuntimeCompositionError, ValueError) as error:
        parser.error(str(error))
    messages = {
        "add": "local binding added",
        "replace": "local binding replaced",
        "remove": "local binding removed",
    }
    print(messages[action])


def _mutate_local_capability(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    try:
        mutate_retained_local_capabilities(
            args.local_capability_action, getattr(args, "capability", None)
        )
    except ValueError as error:
        parser.error(str(error))
    print(
        "local capability removed"
        if args.local_capability_action == "remove"
        else f"local capability {args.local_capability_action}ed"
    )


def _mutate_execution_limit(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    try:
        set_retained_execution_limit(
            None if args.execution_limit_action == "clear" else args.limit
        )
    except ValueError as error:
        parser.error(str(error))
    print(
        "local execution limit cleared"
        if args.execution_limit_action == "clear"
        else "local execution limit retained"
    )


def _node_declaration(parser: argparse.ArgumentParser, args: argparse.Namespace):
    if args.base_url is None:
        parser.error("--base-url is required unless --remove")
    capabilities = _validated_capabilities(parser, args.capability, subject="remote")
    return build_retained_remote_node_declaration(
        node_id=args.node_id,
        base_url=args.base_url,
        capabilities=DEFAULT_STATIC_CAPABILITY_NAMES
        if capabilities is None
        else capabilities,
    )


def _validate_reset(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if (
        args.runtime is not None
        or args.ollama_model is not None
        or args.ollama_disable_thinking
        or args.llama_server_base_url is not None
        or args.llama_server_model is not None
        or args.vllm_base_url is not None
        or args.vllm_model is not None
        or args.temperature is not None
        or args.local_capability is not None
        or args.execution_limit is not None
        or args.runtime_config is not None
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
        if isinstance(values, MultiBindingRuntimeCompositionValues):
            lines.append("  runtime composition: multi-binding")
            for binding in values.bindings:
                lines.append(
                    f"  binding: capabilities: {', '.join(binding.capabilities)}"
                    f"; runtime: {binding.runtime}"
                )
                if binding.base_url is not None:
                    lines.append(f"    base URL: {binding.base_url}")
                if binding.model is not None:
                    lines.append(f"    model: {binding.model}")
                if binding.runtime == "ollama":
                    lines.append(
                        "    disable thinking: "
                        f"{'true' if binding.disable_thinking else 'false'}"
                    )
                if binding.temperature is not None:
                    lines.append(f"    temperature: {binding.temperature}")
        else:
            lines.append(f"  runtime: {values.runtime}")
        if (
            isinstance(values, LocalRuntimeCompositionValues)
            and values.runtime == "ollama"
        ):
            lines.extend(
                [
                    f"  ollama model: {values.ollama_model or 'not retained'}",
                    "  ollama disable thinking: "
                    f"{'true' if values.ollama_disable_thinking else 'false'}",
                ]
            )
        elif (
            isinstance(values, LocalRuntimeCompositionValues)
            and values.runtime == "llama-server"
        ):
            lines.extend(
                [
                    f"  llama-server base URL: {values.llama_server_base_url}",
                    f"  llama-server model: {values.llama_server_model}",
                ]
            )
        elif isinstance(values, LocalRuntimeCompositionValues):
            lines.extend(
                [
                    f"  vLLM base URL: {values.vllm_base_url}",
                    f"  vLLM model: {values.vllm_model}",
                ]
            )
            lines.append(
                "  temperature: "
                + (
                    "not retained"
                    if values.temperature is None
                    else str(values.temperature)
                )
            )
        if (
            isinstance(values, LocalRuntimeCompositionValues)
            and values.runtime != "vllm"
        ):
            lines.append(
                "  temperature: "
                + (
                    "not retained"
                    if values.temperature is None
                    else str(values.temperature)
                )
            )
        lines.append(
            "  caller-local capabilities: "
            + (
                "not retained"
                if local.local_capabilities is None
                else ", ".join(local.local_capabilities)
            )
        )
        lines.append(
            "  HAC execution limit: "
            + (
                "not retained"
                if local.execution_limit is None
                else str(local.execution_limit)
            )
        )

    lines.append("Image Generation:")
    if configuration.image_generation is None:
        lines.append("  not configured")
    else:
        lines.extend(
            [
                "  runtime: stable-diffusion-cpp",
                f"  base URL: {configuration.image_generation.base_url}",
            ]
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
    if getattr(args, "local_action", None) == "binding":
        _mutate_local_binding(parser, args)
        return
    if getattr(args, "local_action", None) == "capability":
        _mutate_local_capability(parser, args)
        return
    if getattr(args, "local_action", None) == "execution-limit":
        _mutate_execution_limit(parser, args)
        return
    if args.reset:
        _validate_reset(parser, args)
        reset_retained_local_configuration()
        print("local configuration reset")
        return
    if args.runtime_config is not None:
        if any(
            (
                args.runtime is not None,
                args.ollama_model is not None,
                args.ollama_disable_thinking,
                args.llama_server_base_url is not None,
                args.llama_server_model is not None,
                args.vllm_base_url is not None,
                args.vllm_model is not None,
                args.temperature is not None,
                args.local_capability is not None,
                args.execution_limit is not None,
            )
        ):
            parser.error(
                "--runtime-config cannot be combined with local configuration options"
            )
        try:
            values = load_local_runtime_config(args.runtime_config)
        except LocalRuntimeCompositionError as error:
            parser.error(str(error))
        if not isinstance(values, MultiBindingRuntimeCompositionValues):
            parser.error(
                "--runtime-config must contain RFC-0110 multi-binding configuration"
            )
        try:
            replace_retained_local_runtime_composition(values)
        except LocalRuntimeCompositionError as error:
            parser.error(str(error))
        print("local configuration retained")
        return
    local = _local_configuration(parser, args)
    replace_retained_local_configuration(local)
    print("local configuration retained")


def _mutate_image_generation(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    if args.reset and args.base_url is not None:
        parser.error("--reset cannot be combined with --base-url")
    if not args.reset and args.base_url is None:
        parser.error("--base-url is required unless --reset")
    if args.reset:
        reset_retained_image_generation_configuration()
        print("image-generation configuration reset")
        return
    try:
        configuration = build_retained_image_generation_configuration(
            base_url=args.base_url
        )
    except ValueError as error:
        parser.error(str(error))
    replace_retained_image_generation_configuration(configuration)
    print("image-generation configuration retained")


def _mutate_node(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if getattr(args, "node_action", None) == "capability":
        try:
            mutate_retained_remote_capabilities(
                args.node_id, args.node_capability_action, args.capability
            )
        except ValueError as error:
            parser.error(str(error))
        print(
            "node capability removed"
            if args.node_capability_action == "remove"
            else f"node capability {args.node_capability_action}ed"
        )
        return
    if args.remove:
        _validate_remove(parser, args)
        if not remove_retained_remote_node(args.node_id):
            print("error: retained node not found", file=sys.stderr)
            raise SystemExit(1)
        print("node configuration removed")
        return

    declaration = _node_declaration(parser, args)
    replace_retained_remote_node(declaration)
    print("node configuration retained")


def _mutate_external_information(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    if args.reset and args.plugin is not None:
        parser.error("--reset cannot be combined with --plugin")
    if not args.reset and args.plugin is None:
        parser.error("--plugin is required unless --reset")
    replace_retained_external_information_plugin(None if args.reset else args.plugin)
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
    set_retained_chat_external_information_fallback(not args.reset)
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
        elif args.command == "image-generation":
            _mutate_image_generation(parser, args)
        elif args.command == "node":
            _mutate_node(parser, args)
        elif args.command == "chat":
            _mutate_chat(parser, args)
        else:
            _mutate_external_information(parser, args)
    except RetainedConfigurationError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
