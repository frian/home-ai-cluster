import json
from pathlib import Path

import pytest

from home_ai_cluster.commands.status_command import (
    STATUS_FAILURE_MESSAGE,
    format_cluster_status,
    main,
    parse_args,
)
from home_ai_cluster.core.models import (
    ApplicationStatus,
    ClusterStatusNode,
    ClusterStatusResult,
    DeclarationStatus,
    RuntimeStatus,
)


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

    assert (
        'home-ai-cluster-status = "home_ai_cluster.commands.status_command:main"'
        in project
    )


def test_status_command_requires_declaration() -> None:
    with pytest.raises(SystemExit) as raised:
        main([])

    assert raised.value.code != 0


def test_parse_args_selects_json_only_when_requested() -> None:
    _, default_args = parse_args(["--declaration", "cluster.toml"])
    _, json_args = parse_args(["--declaration", "cluster.toml", "--json"])
    _, repeated_json_args = parse_args(
        ["--declaration", "cluster.toml", "--json", "--json"]
    )

    assert default_args.json is False
    assert json_args.json is True
    assert repeated_json_args.json is True


@pytest.mark.parametrize("argv", [["--json", "true"], ["--unknown"]])
def test_invalid_parser_arguments_do_not_collect_status(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster.commands import status_command

    monkeypatch.setattr(
        status_command,
        "evaluate_static_cluster_status",
        lambda *_: (_ for _ in ()).throw(AssertionError("must not collect")),
    )

    with pytest.raises(SystemExit) as raised:
        main(argv)

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == ""
    assert "usage: home-ai-cluster-status" in captured.err


def test_status_command_prints_compact_single_remote_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster.commands import status_command

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

    main(["--declaration", str(declaration), "--json"])

    captured = capsys.readouterr()
    expected = json.dumps(
        status_result("remote-a").model_dump(mode="json"),
        separators=(",", ":"),
    )
    assert captured.out == expected + "\n"
    assert captured.err == ""
    assert calls == [["remote-a"]]


def test_status_command_defaults_to_human_readable_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster.commands import status_command

    declaration = write_declaration(
        tmp_path,
        'remote_node_id = "remote-a"\nremote_base_url = "http://remote-a.test:8000"\n',
    )
    calls = 0

    async def collect(*_: object) -> ClusterStatusResult:
        nonlocal calls
        calls += 1
        return status_result("remote-a")

    monkeypatch.setattr(status_command, "collect_static_cluster_status", collect)

    main(["--declaration", str(declaration)])

    captured = capsys.readouterr()
    assert captured.out == (
        "Cluster status\n"
        "Declaration: coherent\n\n"
        "Nodes:\n"
        "- local\n"
        "  Application status: local\n"
        "  Runtime status: available\n"
        "- remote-a\n"
        "  Application status: reachable\n"
        "  Runtime status: available\n"
    )
    assert captured.err == ""
    assert calls == 1
    assert not captured.out.startswith("{")
    assert "\x1b" not in captured.out


def test_formats_all_normalized_status_values_in_result_order() -> None:
    result = ClusterStatusResult(
        declaration_status=DeclarationStatus.COHERENT,
        nodes=(
            ClusterStatusNode(
                node_id="local",
                application_status=ApplicationStatus.LOCAL,
                runtime_status=RuntimeStatus.UNAVAILABLE,
            ),
            ClusterStatusNode(
                node_id="remote-z",
                application_status=ApplicationStatus.REACHABLE,
                runtime_status=RuntimeStatus.OBSERVATION_FAILED,
            ),
            ClusterStatusNode(
                node_id="remote-a",
                application_status=ApplicationStatus.UNREACHABLE,
                runtime_status=RuntimeStatus.UNKNOWN,
            ),
            ClusterStatusNode(
                node_id="remote-m",
                application_status=ApplicationStatus.REQUEST_FAILED,
                runtime_status=RuntimeStatus.UNKNOWN,
            ),
            ClusterStatusNode(
                node_id="remote-b",
                application_status=ApplicationStatus.INVALID_RESPONSE,
                runtime_status=RuntimeStatus.UNKNOWN,
            ),
        ),
    )

    rendered = format_cluster_status(result)

    assert rendered == (
        "Cluster status\n"
        "Declaration: coherent\n\n"
        "Nodes:\n"
        "- local\n"
        "  Application status: local\n"
        "  Runtime status: unavailable\n"
        "- remote-z\n"
        "  Application status: reachable\n"
        "  Runtime status: observation-failed\n"
        "- remote-a\n"
        "  Application status: unreachable\n"
        "  Runtime status: unknown\n"
        "- remote-m\n"
        "  Application status: request-failed\n"
        "  Runtime status: unknown\n"
        "- remote-b\n"
        "  Application status: invalid-response\n"
        "  Runtime status: unknown"
    )
    assert rendered.index("- local") < rendered.index("- remote-z")
    assert rendered.index("- remote-z") < rendered.index("- remote-a")
    assert "Overall health" not in rendered
    assert "Cluster health" not in rendered
    assert "Degraded" not in rendered
    assert not rendered.endswith("\n")


def test_status_command_preserves_multiple_declaration_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster.commands import status_command

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

    main(["--declaration", str(declaration), "--json"])

    assert calls == 1
    assert (
        json.loads(capsys.readouterr().out)["nodes"]
        == status_result("remote-z", "remote-a").model_dump(mode="json")["nodes"]
    )


def test_status_command_creates_and_closes_one_http_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.commands import status_command

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

    def create_client(**kwargs: object) -> CapturingClient:
        assert kwargs == {"trust_env": False}
        client = CapturingClient()
        clients.append(client)
        return client

    async def collect(*_: object) -> ClusterStatusResult:
        return status_result("remote")

    monkeypatch.setattr(status_command.httpx, "AsyncClient", create_client)
    monkeypatch.setattr(status_command, "collect_static_cluster_status", collect)

    main(["--declaration", str(declaration), "--json"])

    assert len(clients) == 1
    assert clients[0].closed is True


def test_default_status_injects_ollama_composition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.commands import status_command

    declaration = write_declaration(
        tmp_path,
        'remote_node_id = "remote"\nremote_base_url = "http://remote.test:8000"\n',
    )
    observed: list[tuple[list[str], list[str]]] = []

    async def collect(*args: object) -> ClusterStatusResult:
        nodes = [node.adapters[0] for node in args[0].list_nodes()]
        adapters = [adapter.name for adapter in args[1].list_adapters()]
        observed.append((nodes, adapters))
        return status_result("remote")

    monkeypatch.setattr(status_command, "collect_static_cluster_status", collect)

    main(["--declaration", str(declaration), "--json"])

    assert observed == [(["ollama"], ["ollama"])]


def test_explicit_llama_server_injects_selected_composition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.commands import status_command

    declaration = write_declaration(
        tmp_path,
        'remote_node_id = "remote"\nremote_base_url = "http://remote.test:8000"\n',
    )
    observed: list[tuple[list[str], list[str]]] = []

    async def collect(*args: object) -> ClusterStatusResult:
        nodes = [node.adapters[0] for node in args[0].list_nodes()]
        adapters = [adapter.name for adapter in args[1].list_adapters()]
        observed.append((nodes, adapters))
        return status_result("remote")

    monkeypatch.setattr(status_command, "collect_static_cluster_status", collect)

    main(
        [
            "--declaration",
            str(declaration),
            "--runtime",
            "llama-server",
            "--llama-server-base-url",
            "http://127.0.0.1:8080",
            "--llama-server-model",
            "local-model",
            "--json",
        ]
    )

    assert observed == [(["llama-server"], ["llama-server"])]


def test_explicit_ollama_composes_with_json_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.commands import status_command

    declaration = write_declaration(
        tmp_path,
        'remote_node_id = "remote"\nremote_base_url = "http://remote.test:8000"\n',
    )
    observed: list[tuple[list[str], list[str]]] = []

    async def collect(*args: object) -> ClusterStatusResult:
        nodes = [node.adapters[0] for node in args[0].list_nodes()]
        adapters = [adapter.name for adapter in args[1].list_adapters()]
        observed.append((nodes, adapters))
        return status_result("remote")

    monkeypatch.setattr(status_command, "collect_static_cluster_status", collect)

    main(
        [
            "--declaration",
            str(declaration),
            "--runtime",
            "ollama",
            "--json",
        ]
    )

    assert observed == [(["ollama"], ["ollama"])]


def test_invalid_declaration_prevents_composition_construction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster.commands import status_command

    declaration = write_declaration(tmp_path, 'remote_node_id = "local"\n')
    monkeypatch.setattr(
        status_command,
        "create_local_runtime_composition",
        lambda **_: (_ for _ in ()).throw(AssertionError("must not construct")),
    )

    with pytest.raises(SystemExit):
        main(["--declaration", str(declaration)])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "must not construct" not in captured.err


def test_explicit_ollama_model_reaches_status_local_composition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.commands import status_command
    from home_ai_cluster.local_runtime_composition import (
        create_local_runtime_composition,
    )

    declaration = write_declaration(
        tmp_path,
        'remote_node_id = "remote"\nremote_base_url = "http://remote.test:8000"\n',
    )
    recorded: dict[str, object] = {}

    def create_composition(**kwargs: object):
        recorded.update(kwargs)
        return create_local_runtime_composition(runtime="ollama")

    async def evaluate(*_: object) -> ClusterStatusResult:
        return status_result("remote")

    monkeypatch.setattr(
        status_command, "create_local_runtime_composition", create_composition
    )
    monkeypatch.setattr(status_command, "evaluate_static_cluster_status", evaluate)

    main(
        [
            "--declaration",
            str(declaration),
            "--runtime",
            "ollama",
            "--ollama-model",
            "configured-model",
        ]
    )

    assert recorded["ollama_model"] == "configured-model"


def test_invalid_runtime_combination_prevents_construction_and_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster.commands import status_command

    declaration = write_declaration(
        tmp_path,
        'remote_node_id = "remote"\nremote_base_url = "http://remote.test:8000"\n',
    )
    monkeypatch.setattr(
        status_command,
        "create_local_runtime_composition",
        lambda **_: (_ for _ in ()).throw(AssertionError("must not construct")),
    )
    monkeypatch.setattr(
        status_command.httpx,
        "AsyncClient",
        lambda: (_ for _ in ()).throw(AssertionError("must not observe")),
    )

    with pytest.raises(SystemExit):
        main(
            [
                "--declaration",
                str(declaration),
                "--llama-server-model",
                "unexpected",
            ]
        )

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "must not construct" not in captured.err
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
                    node_id="remote",
                    application_status=ApplicationStatus.UNREACHABLE,
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
                    runtime_status=RuntimeStatus.UNAVAILABLE,
                ),
                ClusterStatusNode(
                    node_id="remote",
                    application_status=ApplicationStatus.REQUEST_FAILED,
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
    from home_ai_cluster.commands import status_command

    declaration = write_declaration(
        tmp_path,
        'remote_node_id = "remote"\nremote_base_url = "http://remote.test:8000"\n',
    )

    async def collect(*_: object) -> ClusterStatusResult:
        return result

    monkeypatch.setattr(status_command, "collect_static_cluster_status", collect)
    main(["--declaration", str(declaration), "--json"])

    captured = capsys.readouterr()
    assert captured.out == (
        json.dumps(result.model_dump(mode="json"), separators=(",", ":")) + "\n"
    )
    assert captured.err == ""
    assert "Cluster status" not in captured.out


def test_status_command_hides_unexpected_failure_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster.commands import status_command

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


def test_status_command_hides_formatter_failure_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from home_ai_cluster.commands import status_command

    declaration = write_declaration(
        tmp_path,
        'remote_node_id = "remote"\nremote_base_url = "http://remote.test:8000"\n',
    )

    async def collect(*_: object) -> ClusterStatusResult:
        return status_result("remote")

    def fail_format(_: ClusterStatusResult) -> str:
        raise RuntimeError("http://private.example secret adapter model")

    monkeypatch.setattr(status_command, "collect_static_cluster_status", collect)
    monkeypatch.setattr(status_command, "format_cluster_status", fail_format)

    with pytest.raises(SystemExit) as raised:
        main(["--declaration", str(declaration)])

    captured = capsys.readouterr()
    assert raised.value.code == 1
    assert captured.out == ""
    assert captured.err == STATUS_FAILURE_MESSAGE + "\n"
    assert "private.example" not in captured.err
