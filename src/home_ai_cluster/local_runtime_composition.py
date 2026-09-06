"""Concrete local compositions for the supported ordinary runtimes."""

import argparse
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from home_ai_cluster.adapters.llama_server import LlamaServerAdapter
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.adapters.vllm import VllmAdapter
from home_ai_cluster.api.wiring import LocalAppComposition
from home_ai_cluster.core.execution_intervals import ExecutionIntervalCardinality
from home_ai_cluster.core.local_capability_binding import (
    LocalCapabilityBinding,
    LocalCapabilityBindings,
)
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.local_http import local_http_url

LOCAL_RUNTIMES = ("ollama", "llama-server", "vllm")
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
    vllm_base_url: str | None = None
    vllm_model: str | None = None


@dataclass(frozen=True)
class LocalCapabilityBindingValues:
    """Closed operator inputs for one RFC-0110 local capability binding."""

    capabilities: tuple[str, ...]
    runtime: str
    model: str | None = None
    base_url: str | None = None
    disable_thinking: bool = False


@dataclass(frozen=True)
class MultiBindingRuntimeCompositionValues:
    """One explicit RFC-0110 multi-binding runtime-config document."""

    bindings: tuple[LocalCapabilityBindingValues, ...]


_RUNTIME_CONFIG_KEYS = frozenset({"runtime", "ollama", "llama_server", "vllm"})
_OLLAMA_CONFIG_KEYS = frozenset({"model", "disable_thinking"})
_LLAMA_SERVER_CONFIG_KEYS = frozenset({"base_url", "model"})
_VLLM_CONFIG_KEYS = frozenset({"base_url", "model"})
_BINDING_CONFIG_KEYS = frozenset(
    {"capabilities", "runtime", "model", "base_url", "disable_thinking"}
)
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
    parser.add_argument(
        "--vllm-base-url",
        type=local_http_url,
        action=_ExplicitRuntimeValueAction,
        help="Loopback base URL for an operator-managed vLLM server.",
    )
    parser.add_argument(
        "--vllm-model",
        type=non_empty_value,
        action=_ExplicitRuntimeValueAction,
        help="vLLM served-model identity for this process.",
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


def _load_runtime_config_document(path: Path) -> dict[str, Any]:
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

    return document


def _load_multi_binding_runtime_config(
    document: dict[str, Any],
) -> MultiBindingRuntimeCompositionValues:
    if set(document) != {"bindings"}:
        raise LocalRuntimeCompositionError(
            "multi-binding runtime config has invalid keys"
        )
    raw_bindings = document["bindings"]
    if not isinstance(raw_bindings, list) or not raw_bindings:
        raise LocalRuntimeCompositionError("runtime config bindings must be non-empty")

    bindings: list[LocalCapabilityBindingValues] = []
    claimed: set[str] = set()
    for raw_binding in raw_bindings:
        if not isinstance(raw_binding, dict):
            raise LocalRuntimeCompositionError("runtime config binding must be a table")
        if raw_binding.keys() - _BINDING_CONFIG_KEYS:
            raise LocalRuntimeCompositionError("unknown runtime config binding key")
        capabilities = raw_binding.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities:
            raise LocalRuntimeCompositionError(
                "runtime config binding capabilities must be non-empty"
            )
        if not all(isinstance(capability, str) for capability in capabilities):
            raise LocalRuntimeCompositionError(
                "runtime config binding capabilities must be strings"
            )
        if len(set(capabilities)) != len(capabilities):
            raise LocalRuntimeCompositionError(
                "runtime config binding capabilities must not duplicate"
            )
        if any(
            capability not in LOCAL_RUNTIME_CAPABILITY_NAMES
            for capability in capabilities
        ):
            raise LocalRuntimeCompositionError(
                "unknown runtime config binding capability"
            )
        if claimed.intersection(capabilities):
            raise LocalRuntimeCompositionError(
                "runtime config binding capabilities overlap"
            )
        claimed.update(capabilities)

        runtime = raw_binding.get("runtime")
        if runtime not in LOCAL_RUNTIMES:
            raise LocalRuntimeCompositionError(
                "runtime config binding runtime must be ollama, llama-server, or vllm"
            )
        allowed_keys = {"capabilities", "runtime"}
        if runtime == "ollama":
            allowed_keys.update({"model", "disable_thinking"})
        else:
            allowed_keys.update({"base_url", "model"})
        if raw_binding.keys() - allowed_keys:
            raise LocalRuntimeCompositionError(
                "runtime config binding has keys for another runtime"
            )

        if runtime == "ollama":
            model = (
                _non_blank_config_string(raw_binding["model"], "binding.model")
                if "model" in raw_binding
                else None
            )
            disable_thinking = raw_binding.get("disable_thinking", False)
            if not isinstance(disable_thinking, bool):
                raise LocalRuntimeCompositionError(
                    "runtime config binding disable_thinking must be a boolean"
                )
            bindings.append(
                LocalCapabilityBindingValues(
                    capabilities=tuple(capabilities),
                    runtime=runtime,
                    model=model,
                    disable_thinking=disable_thinking,
                )
            )
            continue

        if "base_url" not in raw_binding or "model" not in raw_binding:
            raise LocalRuntimeCompositionError(
                "runtime config binding requires base_url and model"
            )
        base_url = _non_blank_config_string(raw_binding["base_url"], "binding.base_url")
        model = _non_blank_config_string(raw_binding["model"], "binding.model")
        llama_base_url, vllm_base_url = validate_local_runtime_values(
            runtime=runtime,
            llama_server_base_url=base_url if runtime == "llama-server" else None,
            llama_server_model=model if runtime == "llama-server" else None,
            vllm_base_url=base_url if runtime == "vllm" else None,
            vllm_model=model if runtime == "vllm" else None,
        )
        bindings.append(
            LocalCapabilityBindingValues(
                capabilities=tuple(capabilities),
                runtime=runtime,
                base_url=llama_base_url if runtime == "llama-server" else vllm_base_url,
                model=model,
            )
        )
    return MultiBindingRuntimeCompositionValues(bindings=tuple(bindings))


def load_local_runtime_config(
    path: Path,
) -> LocalRuntimeCompositionValues | MultiBindingRuntimeCompositionValues:
    """Load one explicit RFC-0074 or RFC-0110 runtime-config document."""
    document = _load_runtime_config_document(path)
    if "bindings" in document:
        return _load_multi_binding_runtime_config(document)

    unknown_keys = document.keys() - _RUNTIME_CONFIG_KEYS
    if unknown_keys:
        raise LocalRuntimeCompositionError("unknown runtime config key")
    if "runtime" not in document:
        raise LocalRuntimeCompositionError("missing runtime config key: runtime")
    runtime = document["runtime"]
    if not isinstance(runtime, str) or runtime not in LOCAL_RUNTIMES:
        raise LocalRuntimeCompositionError(
            "runtime config runtime must be ollama, llama-server, or vllm"
        )

    ollama = _config_table(document, "ollama")
    llama_server = _config_table(document, "llama_server")
    vllm = _config_table(document, "vllm")
    if runtime == "ollama":
        if llama_server is not None:
            raise LocalRuntimeCompositionError(
                "llama_server table requires runtime llama-server"
            )
        if vllm is not None:
            raise LocalRuntimeCompositionError("vllm table requires runtime vllm")
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

    if runtime == "llama-server":
        if ollama is not None:
            raise LocalRuntimeCompositionError("ollama table requires runtime ollama")
        if vllm is not None:
            raise LocalRuntimeCompositionError("vllm table requires runtime vllm")
        if llama_server is None:
            raise LocalRuntimeCompositionError(
                "missing runtime config table: llama_server"
            )
        if llama_server.keys() - _LLAMA_SERVER_CONFIG_KEYS:
            raise LocalRuntimeCompositionError(
                "unknown llama_server runtime config key"
            )
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
        normalized_base_url, _ = validate_local_runtime_values(
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

    if ollama is not None:
        raise LocalRuntimeCompositionError("ollama table requires runtime ollama")
    if llama_server is not None:
        raise LocalRuntimeCompositionError(
            "llama_server table requires runtime llama-server"
        )
    if vllm is None:
        raise LocalRuntimeCompositionError("missing runtime config table: vllm")
    if vllm.keys() - _VLLM_CONFIG_KEYS:
        raise LocalRuntimeCompositionError("unknown vllm runtime config key")
    if "base_url" not in vllm:
        raise LocalRuntimeCompositionError("missing runtime config key: vllm.base_url")
    if "model" not in vllm:
        raise LocalRuntimeCompositionError("missing runtime config key: vllm.model")
    base_url = _non_blank_config_string(vllm["base_url"], "vllm.base_url")
    model = _non_blank_config_string(vllm["model"], "vllm.model")
    _, normalized_base_url = validate_local_runtime_values(
        runtime="vllm",
        llama_server_base_url=None,
        llama_server_model=None,
        vllm_base_url=base_url,
        vllm_model=model,
    )
    assert normalized_base_url is not None
    return LocalRuntimeCompositionValues(
        runtime="vllm",
        vllm_base_url=normalized_base_url,
        vllm_model=model,
    )


def resolve_local_runtime_composition_values(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    retained_values: LocalRuntimeCompositionValues | None = None,
) -> LocalRuntimeCompositionValues | MultiBindingRuntimeCompositionValues:
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
            llama_base_url, vllm_base_url = validate_local_runtime_values(
                runtime=args.runtime,
                ollama_model=args.ollama_model,
                ollama_disable_thinking=args.ollama_disable_thinking,
                llama_server_base_url=args.llama_server_base_url,
                llama_server_model=args.llama_server_model,
                vllm_base_url=args.vllm_base_url,
                vllm_model=args.vllm_model,
            )
        except LocalRuntimeCompositionError as error:
            parser.error(str(error))
        values = LocalRuntimeCompositionValues(
            runtime=args.runtime,
            ollama_model=args.ollama_model,
            ollama_disable_thinking=args.ollama_disable_thinking,
            llama_server_base_url=llama_base_url,
            llama_server_model=args.llama_server_model,
            vllm_base_url=vllm_base_url,
            vllm_model=args.vllm_model,
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
            vllm_base_url = args.vllm_base_url
            vllm_model = args.vllm_model
        else:
            runtime = retained_values.runtime
            ollama_model = retained_values.ollama_model
            disable_thinking = retained_values.ollama_disable_thinking
            llama_server_base_url = retained_values.llama_server_base_url
            llama_server_model = retained_values.llama_server_model
            vllm_base_url = retained_values.vllm_base_url
            vllm_model = retained_values.vllm_model
            if "--ollama-model" in explicit_arguments:
                ollama_model = args.ollama_model
            if "--ollama-disable-thinking" in explicit_arguments:
                disable_thinking = True
            if "--llama-server-base-url" in explicit_arguments:
                llama_server_base_url = args.llama_server_base_url
            if "--llama-server-model" in explicit_arguments:
                llama_server_model = args.llama_server_model
            if "--vllm-base-url" in explicit_arguments:
                vllm_base_url = args.vllm_base_url
            if "--vllm-model" in explicit_arguments:
                vllm_model = args.vllm_model
        try:
            llama_base_url, normalized_vllm_base_url = validate_local_runtime_values(
                runtime=runtime,
                ollama_model=ollama_model,
                ollama_disable_thinking=disable_thinking,
                llama_server_base_url=llama_server_base_url,
                llama_server_model=llama_server_model,
                vllm_base_url=vllm_base_url,
                vllm_model=vllm_model,
            )
        except LocalRuntimeCompositionError as error:
            parser.error(str(error))
        values = LocalRuntimeCompositionValues(
            runtime=runtime,
            ollama_model=ollama_model,
            ollama_disable_thinking=disable_thinking,
            llama_server_base_url=llama_base_url,
            llama_server_model=llama_server_model,
            vllm_base_url=normalized_vllm_base_url,
            vllm_model=vllm_model,
        )
    setattr(args, _RESOLVED_RUNTIME_VALUES, values)
    return values


def validate_local_runtime_values(
    *,
    runtime: str,
    llama_server_base_url: str | None,
    llama_server_model: str | None,
    vllm_base_url: str | None = None,
    vllm_model: str | None = None,
    ollama_model: str | None = None,
    ollama_disable_thinking: bool = False,
) -> tuple[str | None, str | None]:
    """Validate local runtime values and normalize one runtime base URL."""
    if runtime not in LOCAL_RUNTIMES:
        raise LocalRuntimeCompositionError(
            "runtime must be ollama, llama-server, or vllm"
        )

    if runtime == "ollama":
        if ollama_model is not None and not ollama_model:
            raise LocalRuntimeCompositionError("value must not be empty")
        if llama_server_base_url is not None or llama_server_model is not None:
            raise LocalRuntimeCompositionError(
                "llama-server arguments require --runtime llama-server"
            )
        if vllm_base_url is not None or vllm_model is not None:
            raise LocalRuntimeCompositionError("vllm arguments require --runtime vllm")
        return None, None

    if runtime == "llama-server":
        if ollama_model is not None or ollama_disable_thinking:
            raise LocalRuntimeCompositionError(
                "ollama arguments require --runtime ollama"
            )
        if vllm_base_url is not None or vllm_model is not None:
            raise LocalRuntimeCompositionError("vllm arguments require --runtime vllm")
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
            return local_http_url(llama_server_base_url), None
        except argparse.ArgumentTypeError as error:
            raise LocalRuntimeCompositionError(str(error)) from error

    if ollama_model is not None or ollama_disable_thinking:
        raise LocalRuntimeCompositionError("ollama arguments require --runtime ollama")
    if llama_server_base_url is not None or llama_server_model is not None:
        raise LocalRuntimeCompositionError(
            "llama-server arguments require --runtime llama-server"
        )
    if vllm_base_url is None:
        raise LocalRuntimeCompositionError("--vllm-base-url is required for vllm")
    if vllm_model is None:
        raise LocalRuntimeCompositionError("--vllm-model is required for vllm")
    if not vllm_model:
        raise LocalRuntimeCompositionError("value must not be empty")
    try:
        return None, local_http_url(vllm_base_url)
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


def _create_single_adapter_local_app_composition(
    adapter: OllamaAdapter | LlamaServerAdapter | VllmAdapter,
    capabilities: Sequence[str],
    execution_limit: int,
) -> LocalAppComposition:
    bindings = LocalCapabilityBindings(
        [
            LocalCapabilityBinding(
                capabilities=frozenset(capabilities),
                adapter=adapter,
            )
        ]
    )
    return LocalAppComposition(
        node_registry=NodeRegistry([_create_local_node(adapter.name, capabilities)]),
        adapter_registry=AdapterRegistry([adapter], local_capability_bindings=bindings),
        execution_intervals=ExecutionIntervalCardinality(limit=execution_limit),
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
    return _create_single_adapter_local_app_composition(
        adapter, capabilities, execution_limit
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
    return _create_single_adapter_local_app_composition(
        adapter, capabilities, execution_limit
    )


def create_vllm_local_app_composition(
    *,
    base_url: str,
    model: str,
    capabilities: Sequence[str] = LOCAL_RUNTIME_CAPABILITY_NAMES,
    execution_limit: int = 1,
) -> LocalAppComposition:
    """Construct one ordinary local vLLM composition."""
    adapter = VllmAdapter(base_url=base_url, model=model)
    return _create_single_adapter_local_app_composition(
        adapter, capabilities, execution_limit
    )


def _create_adapter_for_binding(
    binding: LocalCapabilityBindingValues,
) -> OllamaAdapter | LlamaServerAdapter | VllmAdapter:
    if binding.runtime == "ollama":
        return (
            OllamaAdapter(disable_thinking=binding.disable_thinking)
            if binding.model is None
            else OllamaAdapter(
                model=binding.model,
                disable_thinking=binding.disable_thinking,
            )
        )
    assert binding.base_url is not None
    assert binding.model is not None
    if binding.runtime == "llama-server":
        return LlamaServerAdapter(base_url=binding.base_url, model=binding.model)
    return VllmAdapter(base_url=binding.base_url, model=binding.model)


def create_multi_binding_local_app_composition(
    values: MultiBindingRuntimeCompositionValues,
    *,
    node_capabilities: Sequence[str] | None = None,
    execution_limit: int = 1,
) -> LocalAppComposition:
    """Construct one local node with RFC-0110's explicit adapter bindings."""
    constructed = [
        (binding, _create_adapter_for_binding(binding)) for binding in values.bindings
    ]
    bindings = LocalCapabilityBindings(
        LocalCapabilityBinding(
            capabilities=frozenset(binding.capabilities), adapter=adapter
        )
        for binding, adapter in constructed
    )
    owned_capabilities = tuple(
        capability for binding in values.bindings for capability in binding.capabilities
    )
    visible_capabilities = (
        owned_capabilities if node_capabilities is None else tuple(node_capabilities)
    )
    return LocalAppComposition(
        node_registry=NodeRegistry(
            [
                NodeDescription(
                    id="local",
                    name="Local node",
                    availability="available",
                    health=NodeHealth(healthy=True),
                    capabilities=[
                        Capability(name=name) for name in visible_capabilities
                    ],
                    adapters=[adapter.name for _, adapter in constructed],
                )
            ]
        ),
        adapter_registry=AdapterRegistry(
            [adapter for _, adapter in constructed],
            local_capability_bindings=bindings,
        ),
        execution_intervals=ExecutionIntervalCardinality(limit=execution_limit),
    )


def create_local_runtime_composition(
    *,
    runtime: str,
    ollama_model: str | None = None,
    ollama_disable_thinking: bool = False,
    llama_server_base_url: str | None = None,
    llama_server_model: str | None = None,
    vllm_base_url: str | None = None,
    vllm_model: str | None = None,
    capabilities: Sequence[str] = LOCAL_RUNTIME_CAPABILITY_NAMES,
    execution_limit: int = 1,
) -> LocalAppComposition:
    """Validate and construct one supported ordinary local composition."""
    llama_base_url, normalized_vllm_base_url = validate_local_runtime_values(
        runtime=runtime,
        ollama_model=ollama_model,
        ollama_disable_thinking=ollama_disable_thinking,
        llama_server_base_url=llama_server_base_url,
        llama_server_model=llama_server_model,
        vllm_base_url=vllm_base_url,
        vllm_model=vllm_model,
    )

    if runtime == "ollama":
        return create_ollama_local_app_composition(
            model=ollama_model,
            disable_thinking=ollama_disable_thinking,
            capabilities=capabilities,
            execution_limit=execution_limit,
        )

    if runtime == "llama-server":
        assert llama_base_url is not None
        assert llama_server_model is not None
        return create_llama_server_local_app_composition(
            base_url=llama_base_url,
            model=llama_server_model,
            capabilities=capabilities,
            execution_limit=execution_limit,
        )

    assert normalized_vllm_base_url is not None
    assert vllm_model is not None
    return create_vllm_local_app_composition(
        base_url=normalized_vllm_base_url,
        model=vllm_model,
        capabilities=capabilities,
        execution_limit=execution_limit,
    )
