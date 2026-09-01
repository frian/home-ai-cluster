"""Private storage for accepted retained-configuration facts."""

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from home_ai_cluster.local_runtime_composition import (
    LocalRuntimeCompositionError,
    LocalRuntimeCompositionValues,
    validate_local_runtime_values,
)
from home_ai_cluster.static_capabilities import validate_static_capabilities
from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration
from home_ai_cluster.static_cluster_validation import remote_base_url, remote_node_id

_CONFIGURATION_DIRECTORY = "home-ai-cluster"
_CONFIGURATION_FILENAME = "retained-config.json"
_TOP_LEVEL_KEYS = (
    "local",
    "remote_nodes",
    "external_information_plugin",
    "chat_external_information_fallback",
)
_LOCAL_KEYS = (
    "runtime",
    "ollama_model",
    "ollama_disable_thinking",
    "llama_server_base_url",
    "llama_server_model",
    "local_capabilities",
)
_REMOTE_NODE_KEYS = ("node_id", "base_url", "capabilities")


class RetainedConfigurationError(Exception):
    """Raised when private retained configuration cannot be used safely."""


def validate_external_information_plugin_name(value: object) -> str:
    """Validate one exact RFC-0078 acquisition-plugin entry-point name."""
    if not isinstance(value, str):
        raise ValueError("external-information plugin name must be a string")
    if not value.strip():
        raise ValueError("external-information plugin name must be nonblank")
    if len(value.encode("utf-8")) > 64:
        raise ValueError(
            "external-information plugin name must be at most 64 UTF-8 bytes"
        )
    return value


@dataclass(frozen=True)
class RetainedLocalConfiguration:
    """Retained local runtime composition and caller-local routing permission."""

    runtime: LocalRuntimeCompositionValues
    local_capabilities: tuple[str, ...] | None = None


@dataclass(frozen=True)
class RetainedConfiguration:
    """The complete ordered retained configuration baseline."""

    local: RetainedLocalConfiguration | None = None
    remote_nodes: tuple[RemoteNodeDeclaration, ...] = ()
    external_information_plugin: str | None = None
    chat_external_information_fallback: bool = False


def _retained_configuration_home() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data and Path(local_app_data).is_absolute():
            return Path(local_app_data)
        return Path.home() / "AppData" / "Local"
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home and Path(config_home).is_absolute():
        return Path(config_home)
    return Path.home() / ".config"


def retained_configuration_file() -> Path:
    """Return the private retained-configuration path without creating it."""
    return (
        _retained_configuration_home()
        / _CONFIGURATION_DIRECTORY
        / _CONFIGURATION_FILENAME
    )


def remove_retained_configuration(path: Path | None = None) -> None:
    """Remove private retained configuration without loading it."""
    configuration_path = path or retained_configuration_file()
    try:
        configuration_path.unlink()
    except FileNotFoundError:
        pass
    except OSError as error:
        raise RetainedConfigurationError(
            "unable to remove retained configuration"
        ) from error


def load_retained_configuration(
    path: Path | None = None,
) -> RetainedConfiguration:
    """Load one fully validated private retained-configuration document."""
    configuration_path = path or retained_configuration_file()
    try:
        contents = configuration_path.read_bytes()
    except FileNotFoundError:
        return RetainedConfiguration()
    except OSError as error:
        raise RetainedConfigurationError(
            "unable to read retained configuration"
        ) from error

    try:
        document = json.loads(contents.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RetainedConfigurationError("invalid retained configuration") from error

    try:
        return _parse_configuration(document)
    except RetainedConfigurationError:
        raise
    except (TypeError, ValueError) as error:
        raise RetainedConfigurationError("invalid retained configuration") from error


def save_retained_configuration(
    configuration: RetainedConfiguration,
    path: Path | None = None,
) -> None:
    """Validate and atomically save one private retained-configuration document."""
    document = _serialize_configuration(configuration)
    serialized = (
        json.dumps(
            document,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    )
    configuration_path = path or retained_configuration_file()
    temporary_path: Path | None = None
    try:
        configuration_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=configuration_path.parent,
            prefix=".retained-config-",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            os.chmod(temporary_path, 0o600)
            temporary.write(serialized)
        os.replace(temporary_path, configuration_path)
    except OSError as error:
        raise RetainedConfigurationError(
            "unable to save retained configuration"
        ) from error
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def _parse_configuration(document: Any) -> RetainedConfiguration:
    if not isinstance(document, dict):
        raise RetainedConfigurationError("invalid retained configuration")
    keys = set(document)
    if keys == {"local", "remote_nodes"}:
        external_information_plugin = None
        chat_external_information_fallback = False
    elif keys == {
        "local",
        "remote_nodes",
        "external_information_plugin",
    }:
        external_information_plugin = document["external_information_plugin"]
        chat_external_information_fallback = False
    elif keys == set(_TOP_LEVEL_KEYS):
        external_information_plugin = document["external_information_plugin"]
        chat_external_information_fallback = document[
            "chat_external_information_fallback"
        ]
    else:
        raise RetainedConfigurationError("invalid retained configuration shape")
    local_value = document["local"]
    remote_nodes_value = document["remote_nodes"]
    if local_value is not None and not isinstance(local_value, dict):
        raise RetainedConfigurationError("invalid retained local configuration")
    if not isinstance(remote_nodes_value, list):
        raise RetainedConfigurationError("invalid retained remote nodes")
    if not isinstance(chat_external_information_fallback, bool):
        raise RetainedConfigurationError("invalid retained Chat configuration")
    remote_nodes = tuple(_parse_remote_node(value) for value in remote_nodes_value)
    _validate_unique_remote_nodes(remote_nodes)
    return RetainedConfiguration(
        local=None if local_value is None else _parse_local(local_value),
        remote_nodes=remote_nodes,
        external_information_plugin=_parse_external_information_plugin(
            external_information_plugin
        ),
        chat_external_information_fallback=chat_external_information_fallback,
    )


def _parse_external_information_plugin(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return validate_external_information_plugin_name(value)
    except ValueError as error:
        raise RetainedConfigurationError(
            "invalid retained external-information plugin"
        ) from error


def _parse_local(value: dict[str, Any]) -> RetainedLocalConfiguration:
    _require_exact_keys(value, _LOCAL_KEYS, "retained local configuration")
    runtime = value["runtime"]
    ollama_model = value["ollama_model"]
    disable_thinking = value["ollama_disable_thinking"]
    llama_base_url = value["llama_server_base_url"]
    llama_model = value["llama_server_model"]
    local_capabilities = value["local_capabilities"]
    if not isinstance(runtime, str) or not isinstance(disable_thinking, bool):
        raise RetainedConfigurationError("invalid retained local configuration")
    _require_nullable_string(ollama_model, "retained local configuration")
    _require_nullable_string(llama_base_url, "retained local configuration")
    _require_nullable_string(llama_model, "retained local configuration")
    capabilities = _parse_capabilities(local_capabilities, "local", allow_none=True)
    values = _validated_runtime_values(
        runtime=runtime,
        ollama_model=ollama_model,
        ollama_disable_thinking=disable_thinking,
        llama_server_base_url=llama_base_url,
        llama_server_model=llama_model,
    )
    return RetainedLocalConfiguration(runtime=values, local_capabilities=capabilities)


def _parse_remote_node(value: Any) -> RemoteNodeDeclaration:
    _require_exact_keys(value, _REMOTE_NODE_KEYS, "retained remote node")
    node_id = value["node_id"]
    base_url = value["base_url"]
    if not isinstance(node_id, str) or not isinstance(base_url, str):
        raise RetainedConfigurationError("invalid retained remote node")
    try:
        validated_node_id = remote_node_id(node_id)
        validated_base_url = remote_base_url(base_url)
    except argparse.ArgumentTypeError as error:
        raise RetainedConfigurationError("invalid retained remote node") from error
    return RemoteNodeDeclaration(
        node_id=validated_node_id,
        base_url=validated_base_url,
        capabilities=_parse_capabilities(value["capabilities"], "remote"),
    )


def _serialize_configuration(configuration: RetainedConfiguration) -> dict[str, object]:
    if not isinstance(configuration, RetainedConfiguration):
        raise RetainedConfigurationError("invalid retained configuration")
    if not isinstance(configuration.remote_nodes, tuple):
        raise RetainedConfigurationError("invalid retained remote nodes")
    validated = _parse_configuration(
        {
            "local": _serialize_local(configuration.local),
            "remote_nodes": [
                _serialize_remote_node(remote) for remote in configuration.remote_nodes
            ],
            "external_information_plugin": configuration.external_information_plugin,
            "chat_external_information_fallback": (
                configuration.chat_external_information_fallback
            ),
        }
    )
    _validate_unique_remote_nodes(validated.remote_nodes)
    return {
        "local": _serialize_local(validated.local),
        "remote_nodes": [
            _serialize_remote_node(remote) for remote in validated.remote_nodes
        ],
        "external_information_plugin": validated.external_information_plugin,
        "chat_external_information_fallback": (
            validated.chat_external_information_fallback
        ),
    }


def _serialize_local(
    local: RetainedLocalConfiguration | None,
) -> dict[str, object] | None:
    if local is None:
        return None
    if not isinstance(local, RetainedLocalConfiguration):
        raise RetainedConfigurationError("invalid retained local configuration")
    values = local.runtime
    if not isinstance(values, LocalRuntimeCompositionValues):
        raise RetainedConfigurationError("invalid retained local configuration")
    return {
        "runtime": values.runtime,
        "ollama_model": values.ollama_model,
        "ollama_disable_thinking": values.ollama_disable_thinking,
        "llama_server_base_url": values.llama_server_base_url,
        "llama_server_model": values.llama_server_model,
        "local_capabilities": (
            None if local.local_capabilities is None else list(local.local_capabilities)
        ),
    }


def _serialize_remote_node(remote: RemoteNodeDeclaration) -> dict[str, object]:
    if not isinstance(remote, RemoteNodeDeclaration):
        raise RetainedConfigurationError("invalid retained remote node")
    return {
        "node_id": remote.node_id,
        "base_url": remote.base_url,
        "capabilities": list(remote.capabilities),
    }


def _validated_runtime_values(
    *,
    runtime: str,
    ollama_model: str | None,
    ollama_disable_thinking: bool,
    llama_server_base_url: str | None,
    llama_server_model: str | None,
) -> LocalRuntimeCompositionValues:
    try:
        normalized_base_url = validate_local_runtime_values(
            runtime=runtime,
            ollama_model=ollama_model,
            ollama_disable_thinking=ollama_disable_thinking,
            llama_server_base_url=llama_server_base_url,
            llama_server_model=llama_server_model,
        )
    except LocalRuntimeCompositionError as error:
        raise RetainedConfigurationError(
            "invalid retained local configuration"
        ) from error
    return LocalRuntimeCompositionValues(
        runtime=runtime,
        ollama_model=ollama_model,
        ollama_disable_thinking=ollama_disable_thinking,
        llama_server_base_url=normalized_base_url,
        llama_server_model=llama_server_model,
    )


def _parse_capabilities(
    value: Any,
    subject: str,
    *,
    allow_none: bool = False,
) -> tuple[str, ...] | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, list):
        raise RetainedConfigurationError(f"invalid retained {subject} capabilities")
    try:
        return validate_static_capabilities(value, subject=subject)
    except ValueError as error:
        raise RetainedConfigurationError(
            f"invalid retained {subject} capabilities"
        ) from error


def _validate_unique_remote_nodes(
    remote_nodes: tuple[RemoteNodeDeclaration, ...],
) -> None:
    if len({remote.node_id for remote in remote_nodes}) != len(remote_nodes):
        raise RetainedConfigurationError("duplicate retained remote node ID")
    if len({remote.base_url for remote in remote_nodes}) != len(remote_nodes):
        raise RetainedConfigurationError("duplicate retained remote base URL")


def _require_exact_keys(value: Any, keys: tuple[str, ...], subject: str) -> None:
    if not isinstance(value, dict):
        raise RetainedConfigurationError(f"invalid {subject}")
    if set(value) != set(keys):
        raise RetainedConfigurationError(f"invalid {subject} shape")


def _require_nullable_string(value: Any, subject: str) -> None:
    if value is not None and not isinstance(value, str):
        raise RetainedConfigurationError(f"invalid {subject}")
