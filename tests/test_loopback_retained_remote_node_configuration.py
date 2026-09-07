"""RFC-0113 native-loopback retained remote-node facade tests."""

import asyncio
import socket
from pathlib import Path

import httpx
import pytest

from home_ai_cluster.main import create_app, create_receiver_app
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    load_retained_configuration,
    save_retained_configuration,
)
from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration
from home_ai_cluster.web.loopback_browser import add_loopback_browser_routes


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))


def request(
    app,
    method: str,
    path: str,
    *,
    port: int = 25042,
    headers: dict[str, str] | None = None,
    json: object | None = None,
) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url=f"http://127.0.0.1:{port}",
        ) as client:
            return await client.request(method, path, headers=headers, json=json)

    return asyncio.run(send())


def native_app(*, composition: object | None = None):
    return add_loopback_browser_routes(create_app(local_app_composition=composition))


def mutation_headers(port: int = 25042) -> dict[str, str]:
    return {
        "Origin": f"http://127.0.0.1:{port}",
        "Content-Type": "application/json",
    }


def node_document(
    base_url: str = "http://192.0.2.10:25042",
    capabilities: list[str] | None = None,
) -> dict[str, object]:
    return {
        "base_url": base_url,
        "capabilities": ["chat", "summarize"] if capabilities is None else capabilities,
    }


def test_read_returns_only_retained_nodes_in_order_without_dns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    save_retained_configuration(
        RetainedConfiguration(
            remote_nodes=(
                RemoteNodeDeclaration("first", "http://192.0.2.10:25042"),
                RemoteNodeDeclaration("second", "https://example.invalid"),
            ),
            external_information_plugin="tavily",
            chat_external_information_fallback=True,
        )
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("retained-node read must not resolve DNS")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    response = request(native_app(), "GET", "/retained-remote-nodes")

    assert response.status_code == 200
    assert response.json() == {
        "remote_nodes": [
            {"node_id": "first", **node_document()},
            {"node_id": "second", **node_document("https://example.invalid")},
        ]
    }


def test_read_requires_native_host_authority() -> None:
    response = request(
        native_app(),
        "GET",
        "/retained-remote-nodes",
        headers={"Host": "foreign.example"},
    )

    assert response.status_code == 400


def test_add_update_and_remove_preserve_retained_domains_and_composition() -> None:
    save_retained_configuration(
        RetainedConfiguration(
            remote_nodes=(
                RemoteNodeDeclaration("first", "http://192.0.2.10:25042"),
                RemoteNodeDeclaration("second", "http://192.0.2.11:25042"),
            ),
            external_information_plugin="tavily",
            chat_external_information_fallback=True,
        )
    )
    composition = object()
    app = native_app(composition=composition)

    added = request(
        app,
        "PUT",
        "/retained-remote-nodes/third",
        headers=mutation_headers(),
        json=node_document("https://example.invalid"),
    )
    updated = request(
        app,
        "PUT",
        "/retained-remote-nodes/second",
        headers=mutation_headers(),
        json=node_document("http://192.0.2.12:25042", ["code"]),
    )
    removed = request(
        app,
        "DELETE",
        "/retained-remote-nodes/first",
        headers=mutation_headers(),
    )

    assert added.status_code == updated.status_code == removed.status_code == 200
    retained = load_retained_configuration()
    assert [
        (node.node_id, node.base_url, node.capabilities)
        for node in retained.remote_nodes
    ] == [
        ("second", "http://192.0.2.12:25042", ("code",)),
        ("third", "https://example.invalid", ("chat", "summarize")),
    ]
    assert retained.external_information_plugin == "tavily"
    assert retained.chat_external_information_fallback is True
    assert app.state.local_app_composition is composition


@pytest.mark.parametrize(
    "document",
    [
        node_document(capabilities=[]),
        node_document(capabilities=["chat", "chat"]),
        node_document(capabilities=["unknown"]),
        node_document(base_url="not a URL"),
        {
            "base_url": "http://192.0.2.10:25042",
            "capabilities": ["chat"],
            "node_id": "other",
        },
    ],
)
def test_invalid_mutation_does_not_persist(document: dict[str, object]) -> None:
    response = request(
        native_app(),
        "PUT",
        "/retained-remote-nodes/remote",
        headers=mutation_headers(),
        json=document,
    )

    assert response.status_code == 400
    assert load_retained_configuration().remote_nodes == ()


@pytest.mark.parametrize(
    ("headers", "port"),
    [
        ({}, 25042),
        ({"Origin": "null"}, 25042),
        ({"Origin": "http://foreign.example"}, 25042),
        ({"Host": "foreign.example", "Origin": "http://foreign.example"}, 25042),
        (mutation_headers(), 25043),
    ],
)
def test_mutation_requires_native_host_and_exact_origin(
    headers: dict[str, str], port: int
) -> None:
    response = request(
        native_app(),
        "PUT",
        "/retained-remote-nodes/remote",
        port=port,
        headers=headers,
        json=node_document(),
    )

    assert response.status_code in {400, 403, 415}
    assert load_retained_configuration().remote_nodes == ()


def test_non_default_port_and_missing_delete_are_bounded() -> None:
    port = 25123
    app = native_app()
    added = request(
        app,
        "PUT",
        "/retained-remote-nodes/remote",
        port=port,
        headers=mutation_headers(port),
        json=node_document(),
    )
    missing = request(
        app,
        "DELETE",
        "/retained-remote-nodes/missing",
        port=port,
        headers=mutation_headers(port),
    )

    assert added.status_code == 200
    assert "access-control-allow-origin" not in added.headers
    assert missing.status_code == 404
    assert [node.node_id for node in load_retained_configuration().remote_nodes] == [
        "remote"
    ]


def test_receiver_has_no_retained_remote_node_routes() -> None:
    receiver = create_receiver_app(local_app_composition=object())

    for method in ("GET", "PUT", "DELETE"):
        response = request(
            receiver,
            method,
            "/retained-remote-nodes/remote"
            if method != "GET"
            else "/retained-remote-nodes",
            headers=mutation_headers(),
            json=node_document(),
        )
        assert response.status_code == 404
