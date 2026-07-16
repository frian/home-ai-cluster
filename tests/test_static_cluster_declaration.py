import socket
from pathlib import Path

import pytest

from home_ai_cluster import static_cluster, static_cluster_declaration
from home_ai_cluster.static_cluster_declaration import (
    StaticClusterDeclaration,
    StaticClusterDeclarationError,
    load_static_cluster_declaration,
)
from home_ai_cluster.static_cluster_validation import remote_base_url, remote_node_id


def write_declaration(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "cluster.toml"
    path.write_text(content, encoding="utf-8")
    return path


def valid_declaration() -> str:
    return (
        'remote_node_id = "remote-node"\n'
        'remote_base_url = "http://192.0.2.10:8000"\n'
    )


def test_static_cluster_and_declaration_share_neutral_validation() -> None:
    assert static_cluster.remote_node_id is remote_node_id
    assert static_cluster.remote_base_url is remote_base_url
    assert static_cluster_declaration.remote_node_id is remote_node_id
    assert static_cluster_declaration.remote_base_url is remote_base_url


def test_loads_valid_static_cluster_declaration_without_network_use(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*_: object, **__: object) -> None:
        raise AssertionError("declaration loading must not use the network")

    monkeypatch.setattr(socket, "getaddrinfo", fail_network)

    declaration = load_static_cluster_declaration(
        write_declaration(tmp_path, valid_declaration())
    )

    assert declaration == StaticClusterDeclaration(
        remote_node_id="remote-node",
        remote_base_url="http://192.0.2.10:8000",
    )


def test_normalizes_remote_base_url_trailing_slash(tmp_path: Path) -> None:
    declaration = load_static_cluster_declaration(
        write_declaration(
            tmp_path,
            'remote_node_id = "remote-node"\n'
            'remote_base_url = "https://remote.example:8000/"\n',
        )
    )

    assert declaration.remote_base_url == "https://remote.example:8000"


def test_missing_declaration_file_is_a_safe_local_failure(tmp_path: Path) -> None:
    path = tmp_path / "missing.toml"

    with pytest.raises(StaticClusterDeclarationError) as raised:
        load_static_cluster_declaration(path)

    assert str(raised.value) == f"declaration file not found: {path}"


def test_unreadable_declaration_is_a_safe_local_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = write_declaration(tmp_path, valid_declaration())

    def fail_open(self: Path, *_: object, **__: object) -> None:
        raise OSError("private operating-system detail")

    monkeypatch.setattr(Path, "open", fail_open)

    with pytest.raises(StaticClusterDeclarationError) as raised:
        load_static_cluster_declaration(path)

    assert str(raised.value) == f"unable to read declaration: {path}"
    assert "private operating-system detail" not in str(raised.value)


@pytest.mark.parametrize(
    ("content", "expected_message"),
    [
        (
            'remote_node_id = "remote-node"\n',
            "missing declaration key: remote_base_url",
        ),
        (
            'remote_base_url = "http://192.0.2.10:8000"\n',
            "missing declaration key: remote_node_id",
        ),
        (
            'remote_node_id = "remote-node"\n'
            'remote_base_url = "http://192.0.2.10:8000"\n'
            'unexpected = "value"\n',
            "unknown declaration key",
        ),
        (
            'remote_node_id = "remote-node"\n'
            'remote_base_url = "http://192.0.2.10:8000"\n'
            '[nested]\n'
            'value = "not allowed"\n',
            "unknown declaration key",
        ),
        (
            'remote_node_id = 7\n'
            'remote_base_url = "http://192.0.2.10:8000"\n',
            "declaration value must be a string: remote_node_id",
        ),
        (
            'remote_node_id = "remote-node"\nremote_base_url = []\n',
            "declaration value must be a string: remote_base_url",
        ),
    ],
)
def test_rejects_invalid_declaration_shape(
    tmp_path: Path,
    content: str,
    expected_message: str,
) -> None:
    with pytest.raises(StaticClusterDeclarationError) as raised:
        load_static_cluster_declaration(write_declaration(tmp_path, content))

    assert str(raised.value) == expected_message


def test_rejects_invalid_toml_without_parser_detail(tmp_path: Path) -> None:
    with pytest.raises(StaticClusterDeclarationError) as raised:
        load_static_cluster_declaration(
            write_declaration(tmp_path, 'remote_node_id = "unterminated\n')
        )

    assert str(raised.value).startswith("invalid TOML declaration:")
    assert "unterminated" not in str(raised.value)


@pytest.mark.parametrize(
    ("node_id", "base_url", "failure_category"),
    [
        ("", "http://192.0.2.10:8000", "invalid remote node ID declaration:"),
        ("local", "http://192.0.2.10:8000", "invalid remote node ID declaration:"),
        ("remote-node", "not-a-url", "invalid remote base URL declaration:"),
    ],
)
def test_reuses_static_cluster_value_validation(
    tmp_path: Path,
    node_id: str,
    base_url: str,
    failure_category: str,
) -> None:
    path = write_declaration(
        tmp_path,
        f'remote_node_id = "{node_id}"\nremote_base_url = "{base_url}"\n',
    )

    with pytest.raises(StaticClusterDeclarationError) as raised:
        load_static_cluster_declaration(path)

    assert str(raised.value).startswith(failure_category)


def test_private_base_url_is_absent_from_failure_messages(tmp_path: Path) -> None:
    private_base_url = "private.example:9443"
    path = write_declaration(
        tmp_path,
        'remote_node_id = "remote-node"\n'
        f'remote_base_url = "{private_base_url}"\n',
    )

    with pytest.raises(StaticClusterDeclarationError) as raised:
        load_static_cluster_declaration(path)

    assert private_base_url not in str(raised.value)
