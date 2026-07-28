import json
import socket
from pathlib import Path

import httpx
import pytest

from home_ai_cluster.static_preflight import main, parse_args


def write_declaration(tmp_path: Path) -> Path:
    path = tmp_path / "cluster.toml"
    path.write_text(
        "[[remote_nodes]]\n"
        'node_id = "remote-a"\n'
        'base_url = "https://private-a.example:8000"\n\n'
        "[[remote_nodes]]\n"
        'node_id = "remote-b"\n'
        'base_url = "https://private-b.example:8000"\n',
        encoding="utf-8",
    )
    return path


def test_parse_args_accepts_explicit_declaration_path(tmp_path: Path) -> None:
    path = tmp_path / "cluster.toml"

    args = parse_args(["--declaration", str(path)])

    assert args.declaration == path
    assert args.remote_node_id is None
    assert args.remote_base_url is None


@pytest.mark.parametrize(
    "argv",
    [
        ["--declaration", "cluster.toml", "--remote-node-id", "remote-a"],
        [
            "--declaration",
            "cluster.toml",
            "--remote-base-url",
            "https://remote.example",
        ],
    ],
)
def test_parse_args_rejects_mixed_declaration_and_inline_modes(
    argv: list[str],
) -> None:
    with pytest.raises(SystemExit):
        parse_args(argv)


def test_main_projects_local_then_ordered_remotes_without_network_use(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_network(*_: object, **__: object) -> None:
        raise AssertionError("preflight must not use the network")

    monkeypatch.setattr(httpx, "AsyncClient", fail_network)
    monkeypatch.setattr(socket, "getaddrinfo", fail_network)

    path = write_declaration(tmp_path)
    main(["--declaration", str(path), "--json"])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert [node["node_id"] for node in report["nodes"]] == [
        "local",
        "remote-a",
        "remote-b",
    ]
    assert report["operating_mode"] == "static-multi-node"
    assert "private-a.example" not in captured.out
    assert "private-b.example" not in captured.out
    assert captured.err == ""


def test_main_rejects_invalid_declaration_before_projection(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "cluster.toml"
    path.write_text("remote_nodes = []\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        main(["--declaration", str(path)])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "remote_nodes must not be empty" in captured.err


def test_main_projects_explicit_remote_capabilities_in_declaration_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_network(*_: object, **__: object) -> None:
        raise AssertionError("preflight must not use the network")

    path = tmp_path / "cluster.toml"
    path.write_text(
        "[[remote_nodes]]\n"
        'node_id = "chat-node"\n'
        'base_url = "http://example.invalid:8000"\n'
        'capabilities = ["chat"]\n\n'
        "[[remote_nodes]]\n"
        'node_id = "summary-node"\n'
        'base_url = "http://example.invalid:8001"\n'
        'capabilities = ["summarize"]\n\n'
        "[[remote_nodes]]\n"
        'node_id = "default-node"\n'
        'base_url = "http://example.invalid:8002"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(httpx, "AsyncClient", fail_network)
    monkeypatch.setattr(socket, "getaddrinfo", fail_network)

    main(["--declaration", str(path), "--json"])

    report = json.loads(capsys.readouterr().out)
    assert [node["node_id"] for node in report["nodes"]] == [
        "local",
        "chat-node",
        "summary-node",
        "default-node",
    ]
    assert [node["capabilities"] for node in report["nodes"][1:]] == [
        ["chat"],
        ["summarize"],
        ["chat", "summarize"],
    ]
