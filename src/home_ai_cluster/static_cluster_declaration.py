"""Local parsing for one RFC-0039 static cluster declaration."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from home_ai_cluster.static_cluster import remote_base_url, remote_node_id

_DECLARATION_KEYS = ("remote_node_id", "remote_base_url")
_DECLARATION_KEY_SET = frozenset(_DECLARATION_KEYS)


class StaticClusterDeclarationError(Exception):
    """Raised when one static cluster declaration cannot be loaded safely."""


@dataclass(frozen=True)
class StaticClusterDeclaration:
    """Validated process-startup facts for one declared remote node."""

    remote_node_id: str
    remote_base_url: str


def load_static_cluster_declaration(
    path: Path | str,
) -> StaticClusterDeclaration:
    """Read and validate one explicitly selected local TOML declaration."""
    declaration_path = Path(path)
    document = _load_toml_document(declaration_path)
    _validate_declaration_shape(document)

    return StaticClusterDeclaration(
        remote_node_id=_validated_remote_node_id(
            document["remote_node_id"], declaration_path
        ),
        remote_base_url=_validated_remote_base_url(
            document["remote_base_url"], declaration_path
        ),
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


def _validate_declaration_shape(document: dict[str, Any]) -> None:
    unknown_keys = document.keys() - _DECLARATION_KEY_SET
    if unknown_keys:
        raise StaticClusterDeclarationError("unknown declaration key")

    for key in _DECLARATION_KEYS:
        if key not in document:
            raise StaticClusterDeclarationError(f"missing declaration key: {key}")
        if not isinstance(document[key], str):
            raise StaticClusterDeclarationError(
                f"declaration value must be a string: {key}"
            )


def _validated_remote_node_id(value: str, path: Path) -> str:
    try:
        return remote_node_id(value)
    except Exception as exc:
        raise StaticClusterDeclarationError(
            f"invalid remote node ID declaration: {path}"
        ) from exc


def _validated_remote_base_url(value: str, path: Path) -> str:
    try:
        return remote_base_url(value)
    except Exception as exc:
        raise StaticClusterDeclarationError(
            f"invalid remote base URL declaration: {path}"
        ) from exc
