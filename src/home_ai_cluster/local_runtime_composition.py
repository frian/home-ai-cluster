"""Concrete local compositions for the supported ordinary runtimes."""

import argparse
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.api.wiring import LocalAppComposition
from home_ai_cluster.core.execution_intervals import ExecutionIntervalCardinality
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.local_http import local_http_url

LOCAL_RUNTIMES = ("ollama", "llama-server")
LOCAL_RUNTIME_CAPABILITY_NAMES = ("chat", "summarize", "classify", "code")


class LocalRuntimeCompositionError(ValueError):
    """Raised when one concrete local runtime composition is invalid."""


@dataclass(frozen=True)
class LocalRuntimeCompositionValues:
    """Closed process-local inputs for one ordinary runtime composition."""

    runtime: str
    ollama_model: str | None = None
    ollama_disable_thinking: bool = False
    llama_server_base_url: str | None = None
    llama_server_model: str | None = None


_RUNTIME_CONFIG_KEYS = frozenset({"runtime", "ollama", "llama_server"})
_OLLAMA_CONFIG_KEYS = frozenset({"model", "disable_thinking"})
_LLAMA_SERVER_CONFIG_KEYS = frozenset({"base_url", "model"})
_EXPLICIT_RUNTIME_ARGUMENTS = "_explicit_runtime_composition_arguments"
_RESOLVED_RUNTIME_VALUES = "_resolved_runtime_composition_values"


def _record_explicit_runtime_argument(
    namespace: argparse.Namespace,
    option_string: str | None,
) -> None:
    arguments = set(getattr(namespace, _EXPLICIT_RUNTIME_ARGUMENTS, ()))
    if option_string is not None:
        arguments.add(option_string)
    setattr(namespace, _EXPLICIT_RUNTIME_ARGUMENTS, frozenset(arguments))


class _ExplicitRuntimeValueAction(argparse.Action):
    """Store one value and retain that the operator supplied its option."""

    def __call__(
        self,
        _parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str,
        option_string: str | None = None,
    ) -> None:
        setattr(namespace, self.dest, values)
        _record_explicit_runtime_argument(namespace, option_string)


class _ExplicitRuntimeTrueAction(argparse.Action):
    """Store true and retain that the operator supplied its option."""

    def __call__(
        self,
        _parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        _values: object,
        option_string: str | None = None,
    ) -> None:
        setattr(namespace, self.dest, True)
        _record_explicit_runtime_argument(namespace, option_string)


def non_empty_value(value: str) -> str:
    """Require one explicit non-empty operator-supplied value."""
    if not value:
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def add_local_runtime_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the closed local runtime argument set to one ordinary parser."""
    parser.set_defaults(**{_EXPLICIT_RUNTIME_ARGUMENTS: frozenset()})
    parser.add_argument(
        "--runtime",
        choices=LOCAL_RUNTIMES,
        default="ollama",
        action=_ExplicitRuntimeValueAction,
        help="Supported operator-managed runtime composition to use.",
    )
    parser.add_argument(
        "--runtime-config", type=Path, help="Explicit runtime-composition TOML file."
    )
    parser.add_argument(
        "--ollama-model",
        type=non_empty_value,
        action=_ExplicitRuntimeValueAction,
        help="Ollama model identifier for this process.",
    )
    parser.add_argument(
        "--ollama-disable-thinking",
        action=_ExplicitRuntimeTrueAction,
        default=False,
        nargs=0,
        help="Disable Ollama thinking for this process.",
    )
    parser.add_argument(
        "--llama-server-base-url",
        type=local_http_url,
        action=_ExplicitRuntimeValueAction,
        help="Loopback base URL for an operator-managed llama-server.",
    )
    parser.add_argument(
        "--llama-server-model",
        type=non_empty_value,
        action=_ExplicitRuntimeValueAction,
        help="llama-server model identifier for this process.",
    )


def _non_blank_config_string(value: Any, key: str) -> str:
    if not isinstance(value, str):
        raise LocalRuntimeCompositionError(f"runtime config {key} must be a string")
    if not value.strip():
        raise LocalRuntimeCompositionError(f"runtime config {key} must not be blank")
    return value


def _config_table(document: dict[str, Any], key: str) -> dict[str, Any] | None:
    if key not in document:
        return None
    table = document[key]
    if not isinstance(table, dict):
        raise LocalRuntimeCompositionError(f"runtime config {key} must be a table")
    return table


def load_local_runtime_config(path: Path) -> LocalRuntimeCompositionValues:
    """Load one explicit RFC-0074 runtime-composition TOML document."""
    try:
        with path.open("rb") as config_file:
            document = tomllib.load(config_file)
    except FileNotFoundError as error:
        raise LocalRuntimeCompositionError(
            f"runtime config file not found: {path}"
        ) from error
    except OSError as error:
        raise LocalRuntimeCompositionError(
            f"unable to read runtime config: {path}"
        ) from error
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise LocalRuntimeCompositionError(
            f"invalid TOML runtime config: {path}"
        ) from error

    unknown_keys = document.keys() - _RUNTIME_CONFIG_KEYS
    if unknown_keys:
        raise LocalRuntimeCompositionError("unknown runtime config key")
    if "runtime" not in document:
        raise LocalRuntimeCompositionError("missing runtime config key: runtime")
    runtime = document["runtime"]
    if not isinstance(runtime, str) or runtime not in LOCAL_RUNTIMES:
        raise LocalRuntimeCompositionError(
            "runtime config runtime must be ollama or llama-server"
        )

    ollama = _config_table(document, "ollama")
    llama_server = _config_table(document, "llama_server")
    if runtime == "ollama":
        if llama_server is not None:
            raise LocalRuntimeCompositionError(
                "llama_server table requires runtime llama-server"
            )
        if ollama is None:
            return LocalRuntimeCompositionValues(runtime="ollama")
        if ollama.keys() - _OLLAMA_CONFIG_KEYS:
            raise LocalRuntimeCompositionError("unknown ollama runtime config key")
        model = (
            _non_blank_config_string(ollama["model"], "ollama.model")
            if "model" in ollama
            else None
        )
        disable_thinking = ollama.get("disable_thinking", False)
        if not isinstance(disable_thinking, bool):
            raise LocalRuntimeCompositionError(
                "runtime config ollama.disable_thinking must be a boolean"
            )
        return LocalRuntimeCompositionValues(
            runtime="ollama",
            ollama_model=model,
            ollama_disable_thinking=disable_thinking,
        )

    if ollama is not None:
        raise LocalRuntimeCompositionError("ollama table requires runtime ollama")
    if llama_server is None:
        raise LocalRuntimeCompositionError("missing runtime config table: llama_server")
    if llama_server.keys() - _LLAMA_SERVER_CONFIG_KEYS:
        raise LocalRuntimeCompositionError("unknown llama_server runtime config key")
    if "base_url" not in llama_server:
        raise LocalRuntimeCompositionError(
            "missing runtime config key: llama_server.base_url"
        )
    if "model" not in llama_server:
        raise LocalRuntimeCompositionError(
            "missing runtime config key: llama_server.model"
        )
    base_url = _non_blank_config_string(
        llama_server["base_url"], "llama_server.base_url"
    )
    model = _non_blank_config_string(llama_server["model"], "llama_server.model")
    normalized_base_url = validate_local_runtime_values(
        runtime="llama-server",
        llama_server_base_url=base_url,
        llama_server_model=model,
    )
    assert normalized_base_url is not None
    return LocalRuntimeCompositionValues(
        runtime="llama-server",
        llama_server_base_url=normalized_base_url,
        llama_server_model=model,
    )


def resolve_local_runtime_composition_values(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    retained_values: LocalRuntimeCompositionValues | None = None,
) -> LocalRuntimeCompositionValues:
    """Resolve one explicit file, retained baseline, or CLI composition source."""
    cached = getattr(args, _RESOLVED_RUNTIME_VALUES, None)
    if cached is not None:
        return cached
    runtime_config = getattr(args, "runtime_config", None)
    if runtime_config is not None:
        explicit_arguments = getattr(args, _EXPLICIT_RUNTIME_ARGUMENTS, frozenset())
        if explicit_arguments:
            parser.error(
                "--runtime-config cannot be combined with explicitly supplied "
                "runtime composition arguments"
            )
        try:
            values = load_local_runtime_config(runtime_config)
        except LocalRuntimeCompositionError as error:
            parser.error(str(error))
    elif retained_values is None:
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
        values = LocalRuntimeCompositionValues(
            runtime=args.runtime,
            ollama_model=args.ollama_model,
            ollama_disable_thinking=args.ollama_disable_thinking,
            llama_server_base_url=base_url,
            llama_server_model=args.llama_server_model,
        )
    else:
        explicit_arguments = getattr(args, _EXPLICIT_RUNTIME_ARGUMENTS, frozenset())
        replaces_runtime = (
            "--runtime" in explicit_arguments
            and args.runtime != retained_values.runtime
        )
        if replaces_runtime:
            runtime = args.runtime
            ollama_model = args.ollama_model
            disable_thinking = args.ollama_disable_thinking
            llama_server_base_url = args.llama_server_base_url
            llama_server_model = args.llama_server_model
        else:
            runtime = retained_values.runtime
            ollama_model = retained_values.ollama_model
            disable_thinking = retained_values.ollama_disable_thinking
            llama_server_base_url = retained_values.llama_server_base_url
            llama_server_model = retained_values.llama_server_model
            if "--ollama-model" in explicit_arguments:
                ollama_model = args.ollama_model
            if "--ollama-disable-thinking" in explicit_arguments:
                disable_thinking = True
            if "--llama-server-base-url" in explicit_arguments:
                llama_server_base_url = args.llama_server_base_url
            if "--llama-server-model" in explicit_arguments:
                llama_server_model = args.llama_server_model
        try:
            base_url = validate_local_runtime_values(
                runtime=runtime,
                ollama_model=ollama_model,
                ollama_disable_thinking=disable_thinking,
                llama_server_base_url=llama_server_base_url,
                llama_server_model=llama_server_model,
            )
        except LocalRuntimeCompositionError as error:
            parser.error(str(error))
        values = LocalRuntimeCompositionValues(
            runtime=runtime,
            ollama_model=ollama_model,
            ollama_disable_thinking=disable_thinking,
            llama_server_base_url=base_url,
            llama_server_model=llama_server_model,
        )
    setattr(args, _RESOLVED_RUNTIME_VALUES, values)
    return values


def validate_local_runtime_values(
    *,
    runtime: str,
    llama_server_base_url: str | None,
    llama_server_model: str | None,
    ollama_model: str | None = None,
    ollama_disable_thinking: bool = False,
) -> str | None:
    """Validate local runtime values and normalize a llama-server base URL."""
    if runtime not in LOCAL_RUNTIMES:
        raise LocalRuntimeCompositionError("runtime must be ollama or llama-server")

    if runtime == "ollama":
        if ollama_model is not None and not ollama_model:
            raise LocalRuntimeCompositionError("value must not be empty")
        if llama_server_base_url is not None or llama_server_model is not None:
            raise LocalRuntimeCompositionError(
                "llama-server arguments require --runtime llama-server"
            )
        return None

    if ollama_model is not None or ollama_disable_thinking:
        raise LocalRuntimeCompositionError("ollama arguments require --runtime ollama")

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
    retained_values: LocalRuntimeCompositionValues | None = None,
) -> None:
    """Apply shared local runtime validation through the supplied parser."""
    resolve_local_runtime_composition_values(parser, args, retained_values)


def _create_local_node(
    adapter_name: str,
    capabilities: Sequence[str] = LOCAL_RUNTIME_CAPABILITY_NAMES,
) -> NodeDescription:
    return NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name=name) for name in capabilities],
        adapters=[adapter_name],
    )


def create_ollama_local_app_composition(
    *,
    model: str | None = None,
    disable_thinking: bool = False,
    capabilities: Sequence[str] = LOCAL_RUNTIME_CAPABILITY_NAMES,
    execution_limit: int = 1,
) -> LocalAppComposition:
    """Construct the ordinary local Ollama composition with existing defaults."""
    adapter = (
        OllamaAdapter(disable_thinking=disable_thinking)
        if model is None
        else OllamaAdapter(model=model, disable_thinking=disable_thinking)
    )
    return LocalAppComposition(
        node_registry=NodeRegistry([_create_local_node(adapter.name, capabilities)]),
        adapter_registry=AdapterRegistry([adapter]),
        execution_intervals=ExecutionIntervalCardinality(limit=execution_limit),
    )


def create_llama_server_local_app_composition(
    *,
    base_url: str,
    model: str,
    capabilities: Sequence[str] = LOCAL_RUNTIME_CAPABILITY_NAMES,
    execution_limit: int = 1,
) -> LocalAppComposition:
    """Construct one ordinary local llama-server composition."""
    adapter = LlamaServerAdapter(base_url=base_url, model=model)
    return LocalAppComposition(
        node_registry=NodeRegistry([_create_local_node(adapter.name, capabilities)]),
        adapter_registry=AdapterRegistry([adapter]),
        execution_intervals=ExecutionIntervalCardinality(limit=execution_limit),
    )


def create_local_runtime_composition(
    *,
    runtime: str,
    ollama_model: str | None = None,
    ollama_disable_thinking: bool = False,
    llama_server_base_url: str | None = None,
    llama_server_model: str | None = None,
    capabilities: Sequence[str] = LOCAL_RUNTIME_CAPABILITY_NAMES,
    execution_limit: int = 1,
) -> LocalAppComposition:
    """Validate and construct one supported ordinary local composition."""
    base_url = validate_local_runtime_values(
        runtime=runtime,
        ollama_model=ollama_model,
        ollama_disable_thinking=ollama_disable_thinking,
        llama_server_base_url=llama_server_base_url,
        llama_server_model=llama_server_model,
    )

    if runtime == "ollama":
        return create_ollama_local_app_composition(
            model=ollama_model,
            disable_thinking=ollama_disable_thinking,
            capabilities=capabilities,
            execution_limit=execution_limit,
        )

    assert base_url is not None
    assert llama_server_model is not None
    return create_llama_server_local_app_composition(
        base_url=base_url,
        model=llama_server_model,
        capabilities=capabilities,
        execution_limit=execution_limit,
    )
