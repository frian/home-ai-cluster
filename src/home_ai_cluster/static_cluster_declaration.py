"""Local parsing for RFC-0039 and RFC-0040 static cluster declarations."""

import argparse
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from home_ai_cluster.core.static_capabilities import (
    DEFAULT_STATIC_CAPABILITY_NAMES,
    validate_static_capabilities,
)
from home_ai_cluster.static_cluster_validation import remote_base_url, remote_node_id

_SINGLE_DECLARATION_KEYS = ("remote_node_id", "remote_base_url")
_SINGLE_CAPABILITY_KEY = "remote_capabilities"
_LOCAL_CAPABILITY_KEY = "local_capabilities"
_SINGLE_DECLARATION_KEY_SET = frozenset(
    (*_SINGLE_DECLARATION_KEYS, _SINGLE_CAPABILITY_KEY, _LOCAL_CAPABILITY_KEY)
)
_MULTI_DECLARATION_KEY = "remote_nodes"
_MULTI_DECLARATION_KEY_SET = frozenset({_MULTI_DECLARATION_KEY, _LOCAL_CAPABILITY_KEY})
_REMOTE_ENTRY_KEYS = ("node_id", "base_url")
_REMOTE_CAPABILITY_KEY = "capabilities"
_REMOTE_ENTRY_KEY_SET = frozenset((*_REMOTE_ENTRY_KEYS, _REMOTE_CAPABILITY_KEY))


class StaticClusterDeclarationError(Exception):
    """Raised when one static cluster declaration cannot be loaded safely."""


@dataclass(frozen=True)
class RemoteNodeDeclaration:
    """Validated process-startup facts for one declared remote node."""

    node_id: str
    base_url: str
    capabilities: tuple[str, ...] = DEFAULT_STATIC_CAPABILITY_NAMES


@dataclass(frozen=True)
class StaticClusterDeclarations:
    """One caller-local declaration plus ordered immutable remote nodes."""

    remote_nodes: tuple[RemoteNodeDeclaration, ...]
    local_capabilities: tuple[str, ...] = DEFAULT_STATIC_CAPABILITY_NAMES


@dataclass(frozen=True)
class StaticClusterDeclaration:
    """Backward-compatible RFC-0039 single-remote declaration result."""

    remote_node_id: str
    remote_base_url: str
    remote_capabilities: tuple[str, ...] = DEFAULT_STATIC_CAPABILITY_NAMES
    local_capabilities: tuple[str, ...] = DEFAULT_STATIC_CAPABILITY_NAMES


def load_static_cluster_declarations(
    path: Path | str,
) -> StaticClusterDeclarations:
    """Read and validate one RFC-0039 or RFC-0040 declaration file."""
    declaration_path = Path(path)
    document = _load_toml_document(declaration_path)

    if _MULTI_DECLARATION_KEY in document:
        if document.keys() & frozenset(
            (*_SINGLE_DECLARATION_KEYS, _SINGLE_CAPABILITY_KEY)
        ):
            raise StaticClusterDeclarationError("invalid declaration shape")
        remote_nodes = _parse_multiple_remotes(document, declaration_path)
    else:
        remote_nodes = (_parse_single_remote(document, declaration_path),)

    _validate_unique_remote_nodes(remote_nodes)
    return StaticClusterDeclarations(
        remote_nodes=remote_nodes,
        local_capabilities=(
            _parse_local_capabilities(document[_LOCAL_CAPABILITY_KEY])
            if _LOCAL_CAPABILITY_KEY in document
            else DEFAULT_STATIC_CAPABILITY_NAMES
        ),
    )


def load_static_cluster_declaration(
    path: Path | str,
) -> StaticClusterDeclaration:
    """Preserve the existing RFC-0039 single-remote loader contract."""
    declarations = load_static_cluster_declarations(path)
    if len(declarations.remote_nodes) != 1:
        raise StaticClusterDeclarationError(
            "single-remote declaration required by current startup integration"
        )

    remote = declarations.remote_nodes[0]
    return StaticClusterDeclaration(
        remote_node_id=remote.node_id,
        remote_base_url=remote.base_url,
        remote_capabilities=remote.capabilities,
        local_capabilities=declarations.local_capabilities,
    )


def _load_toml_document(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as declaration_file:
            document = tomllib.load(declaration_file)
    except FileNotFoundError as exc:
        raise StaticClusterDeclarationError(
            f"declaration file not found: {path}"
        ) from exc
    except OSError as exc:
        raise StaticClusterDeclarationError(
            f"unable to read declaration: {path}"
        ) from exc
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise StaticClusterDeclarationError(
            f"invalid TOML declaration: {path}"
        ) from exc

    if not isinstance(document, dict):
        raise StaticClusterDeclarationError(f"invalid declaration shape: {path}")

    return document


def _parse_single_remote(
    document: dict[str, Any],
    path: Path,
) -> RemoteNodeDeclaration:
    unknown_keys = document.keys() - _SINGLE_DECLARATION_KEY_SET
    if unknown_keys:
        raise StaticClusterDeclarationError("unknown declaration key")

    for key in _SINGLE_DECLARATION_KEYS:
        if key not in document:
            raise StaticClusterDeclarationError(f"missing declaration key: {key}")
        if not isinstance(document[key], str):
            raise StaticClusterDeclarationError(
                f"declaration value must be a string: {key}"
            )

    return RemoteNodeDeclaration(
        node_id=_validated_remote_node_id(document["remote_node_id"], path),
        base_url=_validated_remote_base_url(document["remote_base_url"], path),
        capabilities=(
            _parse_remote_capabilities(document[_SINGLE_CAPABILITY_KEY])
            if _SINGLE_CAPABILITY_KEY in document
            else DEFAULT_STATIC_CAPABILITY_NAMES
        ),
    )


def _parse_multiple_remotes(
    document: dict[str, Any],
    path: Path,
) -> tuple[RemoteNodeDeclaration, ...]:
    unknown_keys = document.keys() - _MULTI_DECLARATION_KEY_SET
    if unknown_keys:
        raise StaticClusterDeclarationError("unknown declaration key")

    entries = document[_MULTI_DECLARATION_KEY]
    if not isinstance(entries, list):
        raise StaticClusterDeclarationError("remote_nodes must be an array of tables")
    if not entries:
        raise StaticClusterDeclarationError("remote_nodes must not be empty")

    return tuple(_parse_remote_entry(entry, path) for entry in entries)


def _parse_remote_entry(entry: Any, path: Path) -> RemoteNodeDeclaration:
    if not isinstance(entry, dict):
        raise StaticClusterDeclarationError("remote node entry must be a table")

    unknown_keys = entry.keys() - _REMOTE_ENTRY_KEY_SET
    if unknown_keys:
        raise StaticClusterDeclarationError("unknown remote node declaration key")

    for key in _REMOTE_ENTRY_KEYS:
        if key not in entry:
            raise StaticClusterDeclarationError(
                f"missing remote node declaration key: {key}"
            )
        if not isinstance(entry[key], str):
            raise StaticClusterDeclarationError(
                f"remote node declaration value must be a string: {key}"
            )

    return RemoteNodeDeclaration(
        node_id=_validated_remote_node_id(entry["node_id"], path),
        base_url=_validated_remote_base_url(entry["base_url"], path),
        capabilities=(
            _parse_remote_capabilities(entry[_REMOTE_CAPABILITY_KEY])
            if _REMOTE_CAPABILITY_KEY in entry
            else DEFAULT_STATIC_CAPABILITY_NAMES
        ),
    )


def _parse_remote_capabilities(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise StaticClusterDeclarationError("remote capabilities must be an array")
    try:
        return validate_static_capabilities(value, subject="remote")
    except ValueError as exc:
        raise StaticClusterDeclarationError(str(exc)) from exc


def _parse_local_capabilities(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise StaticClusterDeclarationError("local capabilities must be an array")
    try:
        return validate_static_capabilities(value, subject="local")
    except ValueError as exc:
        raise StaticClusterDeclarationError(str(exc)) from exc


def _validate_unique_remote_nodes(
    remote_nodes: tuple[RemoteNodeDeclaration, ...],
) -> None:
    node_ids = [remote.node_id for remote in remote_nodes]
    if len(node_ids) != len(set(node_ids)):
        raise StaticClusterDeclarationError("duplicate remote node ID declaration")

    base_urls = [remote.base_url for remote in remote_nodes]
    if len(base_urls) != len(set(base_urls)):
        raise StaticClusterDeclarationError("duplicate remote base URL declaration")


def _validated_remote_node_id(value: str, path: Path) -> str:
    try:
        return remote_node_id(value)
    except argparse.ArgumentTypeError as exc:
        raise StaticClusterDeclarationError(
            f"invalid remote node ID declaration: {path}"
        ) from exc


def _validated_remote_base_url(value: str, path: Path) -> str:
    try:
        return remote_base_url(value)
    except argparse.ArgumentTypeError as exc:
        raise StaticClusterDeclarationError(
            f"invalid remote base URL declaration: {path}"
        ) from exc
