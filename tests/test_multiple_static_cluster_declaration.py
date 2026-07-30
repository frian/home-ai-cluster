import socket
from pathlib import Path

import pytest

from home_ai_cluster.static_cluster_declaration import (
    RemoteNodeDeclaration,
    StaticClusterDeclarationError,
    StaticClusterDeclarations,
    load_static_cluster_declaration,
    load_static_cluster_declarations,
)


def write_declaration(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "cluster.toml"
    path.write_text(content, encoding="utf-8")
    return path


def valid_multi_declaration() -> str:
    return (
        "[[remote_nodes]]\n"
        'node_id = "remote-a"\n'
        'base_url = "http://192.0.2.10:8000"\n'
        "\n"
        "[[remote_nodes]]\n"
        'node_id = "remote-b"\n'
        'base_url = "http://192.0.2.11:8000/"\n'
    )


def test_loads_ordered_multiple_remote_declarations_without_network_use(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*_: object, **__: object) -> None:
        raise AssertionError("declaration loading must not use the network")

    monkeypatch.setattr(socket, "getaddrinfo", fail_network)

    declarations = load_static_cluster_declarations(
        write_declaration(tmp_path, valid_multi_declaration())
    )

    assert declarations == StaticClusterDeclarations(
        remote_nodes=(
            RemoteNodeDeclaration(
                node_id="remote-a",
                base_url="http://192.0.2.10:8000",
            ),
            RemoteNodeDeclaration(
                node_id="remote-b",
                base_url="http://192.0.2.11:8000",
            ),
        )
    )


def test_new_loader_preserves_rfc_0039_single_remote_shape(tmp_path: Path) -> None:
    declarations = load_static_cluster_declarations(
        write_declaration(
            tmp_path,
            'remote_node_id = "remote-node"\n'
            'remote_base_url = "http://192.0.2.10:8000"\n',
        )
    )

    assert declarations.remote_nodes == (
        RemoteNodeDeclaration(
            node_id="remote-node",
            base_url="http://192.0.2.10:8000",
        ),
    )


def test_existing_single_remote_loader_rejects_multi_remote_startup_integration(
    tmp_path: Path,
) -> None:
    with pytest.raises(StaticClusterDeclarationError) as raised:
        load_static_cluster_declaration(
            write_declaration(tmp_path, valid_multi_declaration())
        )

    assert str(raised.value) == (
        "single-remote declaration required by current startup integration"
    )


@pytest.mark.parametrize(
    ("content", "expected_message"),
    [
        ("remote_nodes = []\n", "remote_nodes must not be empty"),
        (
            'remote_node_id = "remote-a"\n'
            'remote_base_url = "http://192.0.2.10:8000"\n'
            "[[remote_nodes]]\n"
            'node_id = "remote-b"\n'
            'base_url = "http://192.0.2.11:8000"\n',
            "invalid declaration shape",
        ),
        (
            '[[remote_nodes]]\nnode_id = "remote-a"\n',
            "missing remote node declaration key: base_url",
        ),
        (
            '[[remote_nodes]]\nnode_id = "remote-a"\nbase_url = 7\n',
            "remote node declaration value must be a string: base_url",
        ),
        (
            "[[remote_nodes]]\n"
            'node_id = "remote-a"\n'
            'base_url = "http://192.0.2.10:8000"\n'
            'unexpected = "value"\n',
            "unknown remote node declaration key",
        ),
    ],
)
def test_rejects_invalid_multi_remote_shapes(
    tmp_path: Path,
    content: str,
    expected_message: str,
) -> None:
    with pytest.raises(StaticClusterDeclarationError) as raised:
        load_static_cluster_declarations(write_declaration(tmp_path, content))

    assert str(raised.value) == expected_message


@pytest.mark.parametrize(
    ("content", "expected_message"),
    [
        (
            "[[remote_nodes]]\n"
            'node_id = "remote-a"\n'
            'base_url = "http://192.0.2.10:8000"\n'
            "[[remote_nodes]]\n"
            'node_id = "remote-a"\n'
            'base_url = "http://192.0.2.11:8000"\n',
            "duplicate remote node ID declaration",
        ),
        (
            "[[remote_nodes]]\n"
            'node_id = "remote-a"\n'
            'base_url = "http://192.0.2.10:8000/"\n'
            "[[remote_nodes]]\n"
            'node_id = "remote-b"\n'
            'base_url = "http://192.0.2.10:8000"\n',
            "duplicate remote base URL declaration",
        ),
    ],
)
def test_rejects_duplicate_remote_declarations(
    tmp_path: Path,
    content: str,
    expected_message: str,
) -> None:
    with pytest.raises(StaticClusterDeclarationError) as raised:
        load_static_cluster_declarations(write_declaration(tmp_path, content))

    assert str(raised.value) == expected_message


def test_multi_remote_failure_does_not_expose_private_base_url(tmp_path: Path) -> None:
    private_base_url = "private.example:9443"
    path = write_declaration(
        tmp_path,
        f'[[remote_nodes]]\nnode_id = "remote-a"\nbase_url = "{private_base_url}"\n',
    )

    with pytest.raises(StaticClusterDeclarationError) as raised:
        load_static_cluster_declarations(path)

    assert private_base_url not in str(raised.value)
    assert "private.example" not in str(raised.value)
