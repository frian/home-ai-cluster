from pathlib import Path

import pytest
from fastapi import FastAPI

from home_ai_cluster.static_cluster import (
    STATIC_CLUSTER_HOST,
    STATIC_CLUSTER_PORT,
    main,
    parse_args,
)


def test_parse_args_accepts_inline_mode() -> None:
    args = parse_args(
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000/",
        ]
    )

    assert args.declaration is None
    assert args.remote_node_id == "operator-remote"
    assert args.remote_base_url == "https://remote.example:8000"


def test_parse_args_accepts_declaration_mode_without_loading_file(tmp_path: Path) -> None:
    declaration_path = tmp_path / "cluster.toml"

    args = parse_args(["--declaration", str(declaration_path)])

    assert args.declaration == declaration_path
    assert args.remote_node_id is None
    assert args.remote_base_url is None


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--remote-node-id", "operator-remote"],
        ["--remote-base-url", "https://remote.example:8000"],
        [
            "--declaration",
            "cluster.toml",
            "--remote-node-id",
            "operator-remote",
        ],
        [
            "--declaration",
            "cluster.toml",
            "--remote-base-url",
            "https://remote.example:8000",
        ],
        [
            "--declaration",
            "cluster.toml",
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000",
        ],
    ],
)
def test_parse_args_rejects_incomplete_or_combined_modes(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        parse_args(argv)


def test_main_loads_declaration_before_starting_server(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import static_cluster

    declaration_path = tmp_path / "cluster.toml"
    declaration_path.write_text(
        'remote_node_id = "operator-remote"\n'
        'remote_base_url = "https://remote.example:8000/"\n',
        encoding="utf-8",
    )
    app = FastAPI()
    recorded: dict[str, object] = {}

    def create_app(node_id: str, base_url: str) -> FastAPI:
        recorded.update(node_id=node_id, base_url=base_url)
        return app

    monkeypatch.setattr(static_cluster, "create_static_cluster_app", create_app)
    monkeypatch.setattr(
        static_cluster.uvicorn,
        "run",
        lambda run_app, *, host, port: recorded.update(
            app=run_app, host=host, port=port
        ),
    )

    main(["--declaration", str(declaration_path)])

    assert recorded == {
        "node_id": "operator-remote",
        "base_url": "https://remote.example:8000",
        "app": app,
        "host": STATIC_CLUSTER_HOST,
        "port": STATIC_CLUSTER_PORT,
    }


def test_main_does_not_start_server_when_declaration_loading_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster import static_cluster

    declaration_path = tmp_path / "cluster.toml"
    private_url = "https://private.example:9443/not-allowed"
    declaration_path.write_text(
        'remote_node_id = "operator-remote"\n'
        f'remote_base_url = "{private_url}"\n',
        encoding="utf-8",
    )
    started = False

    def run(*args: object, **kwargs: object) -> None:
        nonlocal started
        started = True

    monkeypatch.setattr(static_cluster.uvicorn, "run", run)

    with pytest.raises(SystemExit):
        main(["--declaration", str(declaration_path)])

    captured = capsys.readouterr()
    assert not started
    assert "invalid remote base URL declaration" in captured.err
    assert private_url not in captured.err
    assert "private.example" not in captured.err
