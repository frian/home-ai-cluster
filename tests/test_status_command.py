import json
from pathlib import Path

import pytest

from home_ai_cluster.core.models import (
    ApplicationStatus,
    ClusterStatusNode,
    ClusterStatusResult,
    DeclarationStatus,
    RuntimeStatus,
)
from home_ai_cluster.status_command import STATUS_FAILURE_MESSAGE, main


def write_declaration(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "cluster.toml"
    path.write_text(text, encoding="utf-8")
    return path


def status_result(*remote_ids: str) -> ClusterStatusResult:
    return ClusterStatusResult(
        declaration_status=DeclarationStatus.COHERENT,
        nodes=(
            ClusterStatusNode(
                node_id="local",
                application_status=ApplicationStatus.LOCAL,
                runtime_status=RuntimeStatus.AVAILABLE,
            ),
            *(
                ClusterStatusNode(
                    node_id=node_id,
                    application_status=ApplicationStatus.REACHABLE,
                    runtime_status=RuntimeStatus.AVAILABLE,
                )
                for node_id in remote_ids
            ),
        ),
    )


def test_console_script_entry_exists() -> None:
    project = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'home-ai-cluster-status = "home_ai_cluster.status_command:main"' in project


def test_status_command_requires_declaration() -> None:
    with pytest.raises(SystemExit) as raised:
        main([])

    assert raised.value.code != 0


def test_status_command_prints_compact_single_remote_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster import status_command

    declaration = write_declaration(
        tmp_path,
        'remote_node_id = "remote-a"\nremote_base_url = "http://remote-a.test:8000"\n',
    )
    calls: list[list[str]] = []

    async def collect(*args: object) -> ClusterStatusResult:
        registry = args[2]
        calls.append([item.node.id for item in registry.list_declarations()])
        return status_result("remote-a")

    monkeypatch.setattr(status_command, "collect_static_cluster_status", collect)

    main(["--declaration", str(declaration)])

    captured = capsys.readouterr()
    expected = json.dumps(
        status_result("remote-a").model_dump(mode="json"),
        separators=(",", ":"),
    )
    assert captured.out == expected + "\n"
    assert captured.err == ""
    assert calls == [["remote-a"]]


def test_status_command_preserves_multiple_declaration_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster import status_command

    declaration = write_declaration(
        tmp_path,
        '[[remote_nodes]]\nnode_id = "remote-z"\nbase_url = "http://z.test:8000"\n'
        '[[remote_nodes]]\nnode_id = "remote-a"\nbase_url = "http://a.test:8000"\n',
    )
    calls = 0

    async def collect(*args: object) -> ClusterStatusResult:
        nonlocal calls
        calls += 1
        registry = args[2]
        ids = [item.node.id for item in registry.list_declarations()]
        return status_result(*ids)

    monkeypatch.setattr(status_command, "collect_static_cluster_status", collect)

    main(["--declaration", str(declaration)])

    assert calls == 1
    assert json.loads(capsys.readouterr().out)["nodes"] == status_result(
        "remote-z", "remote-a"
    ).model_dump(mode="json")["nodes"]


def test_status_command_creates_and_closes_one_http_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import status_command

    declaration = write_declaration(
        tmp_path,
        'remote_node_id = "remote"\nremote_base_url = "http://remote.test:8000"\n',
    )
    clients: list[object] = []

    class CapturingClient:
        async def __aenter__(self) -> "CapturingClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            self.closed = True

        closed = False

    def create_client() -> CapturingClient:
        client = CapturingClient()
        clients.append(client)
        return client

    async def collect(*_: object) -> ClusterStatusResult:
        return status_result("remote")

    monkeypatch.setattr(status_command.httpx, "AsyncClient", create_client)
    monkeypatch.setattr(status_command, "collect_static_cluster_status", collect)

    main(["--declaration", str(declaration)])

    assert len(clients) == 1
    assert clients[0].closed is True


def test_invalid_declaration_prevents_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster import status_command

    declaration = write_declaration(tmp_path, 'remote_node_id = "local"\n')
    monkeypatch.setattr(
        status_command,
        "create_static_local_node_registry",
        lambda: (_ for _ in ()).throw(AssertionError("must not observe")),
    )

    with pytest.raises(SystemExit):
        main(["--declaration", str(declaration)])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "must not observe" not in captured.err


@pytest.mark.parametrize(
    "result",
    [
        ClusterStatusResult(
            declaration_status=DeclarationStatus.COHERENT,
            nodes=(
                ClusterStatusNode(
                    node_id="local",
                    application_status=ApplicationStatus.LOCAL,
                    runtime_status=RuntimeStatus.OBSERVATION_FAILED,
                ),
                ClusterStatusNode(
                    node_id="remote", application_status=ApplicationStatus.UNREACHABLE,
                    runtime_status=RuntimeStatus.UNKNOWN,
                ),
            ),
        ),
        ClusterStatusResult(
            declaration_status=DeclarationStatus.COHERENT,
            nodes=(
                ClusterStatusNode(
                    node_id="local",
                    application_status=ApplicationStatus.LOCAL,
                    runtime_status=RuntimeStatus.AVAILABLE,
                ),
                ClusterStatusNode(
                    node_id="remote",
                    application_status=ApplicationStatus.INVALID_RESPONSE,
                    runtime_status=RuntimeStatus.UNKNOWN,
                ),
            ),
        ),
    ],
)
def test_normalized_node_failures_exit_successfully(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    result: ClusterStatusResult,
) -> None:
    from home_ai_cluster import status_command

    declaration = write_declaration(
        tmp_path,
        'remote_node_id = "remote"\nremote_base_url = "http://remote.test:8000"\n',
    )

    async def collect(*_: object) -> ClusterStatusResult:
        return result

    monkeypatch.setattr(status_command, "collect_static_cluster_status", collect)
    main(["--declaration", str(declaration)])

    assert capsys.readouterr().err == ""


def test_status_command_hides_unexpected_failure_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster import status_command

    declaration = write_declaration(
        tmp_path,
        'remote_node_id = "remote"\nremote_base_url = "http://remote.test:8000"\n',
    )

    async def fail(*_: object) -> ClusterStatusResult:
        raise RuntimeError("http://private.example secret adapter model")

    monkeypatch.setattr(status_command, "collect_static_cluster_status", fail)

    with pytest.raises(SystemExit) as raised:
        main(["--declaration", str(declaration)])

    captured = capsys.readouterr()
    assert raised.value.code == 1
    assert captured.out == ""
    assert captured.err == STATUS_FAILURE_MESSAGE + "\n"
    assert "private.example" not in captured.err
