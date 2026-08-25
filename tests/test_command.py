"""Tests for the additive RFC-0050 root command."""

import tomllib
from pathlib import Path

import httpx
import pytest

from home_ai_cluster import (
    aider_command,
    chat_command,
    command,
    external_information_command,
    local_health_snapshot,
    static_preflight,
    status_command,
    summarize_command,
)
from home_ai_cluster.core.models import ClusterStatusResult

HELP = """usage: home-ai-cluster <command> [arguments...]

Foreground process commands:
  local           Run one local runtime process.
  static-cluster  Run one static-cluster process.
  compatibility   Run one loopback compatibility process.

Finite commands:
  aider           Run one bounded Aider code edit.
  external-information  Acquire one bounded source-grounded chat request.
  chat            Send one ordinary chat request.
  code            Send one bounded textual code request.
  code-file       Replace one selected file from one bounded code request.
  classify        Send one ordinary classify request.
  summarize       Send one ordinary summarize request.
  preflight       Inspect static declaration coherence.
  health          Observe local runtime health.
  status          Inspect static-cluster status.

Use 'home-ai-cluster <command> --help' for command-specific help.
"""


def test_project_scripts_preserve_the_unified_and_standalone_entry_points() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    scripts = project["project"]["scripts"]

    assert scripts["home-ai-cluster"] == "home_ai_cluster.command:main"
    assert scripts["hac"] == scripts["home-ai-cluster"]
    assert set(command._COMMANDS) == {
        "local",
        "static-cluster",
        "compatibility",
        "aider",
        "external-information",
        "chat",
        "code",
        "code-file",
        "classify",
        "summarize",
        "preflight",
        "health",
        "status",
    }
    assert {
        name: scripts[name]
        for name in (
            "home-ai-cluster-static-cluster",
            "home-ai-cluster-explain-routing",
            "home-ai-cluster-explain-request",
            "home-ai-cluster-openai-compatibility",
            "home-ai-cluster-health",
            "home-ai-cluster-preflight",
            "home-ai-cluster-status",
            "home-ai-cluster-history",
            "home-ai-cluster-clear-history",
            "home-ai-cluster-local",
            "home-ai-cluster-chat",
        )
    } == {
        "home-ai-cluster-static-cluster": "home_ai_cluster.static_cluster:main",
        "home-ai-cluster-explain-routing": "home_ai_cluster.routing_explanation:main",
        "home-ai-cluster-explain-request": (
            "home_ai_cluster.actual_request_explanation:main"
        ),
        "home-ai-cluster-openai-compatibility": (
            "home_ai_cluster.openai_compatibility:main"
        ),
        "home-ai-cluster-health": "home_ai_cluster.local_health_snapshot:main",
        "home-ai-cluster-preflight": "home_ai_cluster.static_preflight:main",
        "home-ai-cluster-status": "home_ai_cluster.status_command:main",
        "home-ai-cluster-history": "home_ai_cluster.request_history:history_main",
        "home-ai-cluster-clear-history": (
            "home_ai_cluster.request_history:clear_history_main"
        ),
        "home-ai-cluster-local": "home_ai_cluster.local_runtime:main",
        "home-ai-cluster-chat": "home_ai_cluster.chat_command:main",
    }
    assert {
        "home-ai-cluster-static-proof",
        "home-ai-cluster-automatic-proof",
        "home-ai-cluster-fallback-proof",
        "home-ai-cluster-phase-12-heterogeneous-receiver",
    }.isdisjoint(scripts)


@pytest.mark.parametrize("argv", ([], ["--help"]))
def test_no_arguments_and_help_emit_static_root_help(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    command.main(argv)

    captured = capsys.readouterr()

    assert captured.out == HELP
    assert captured.err == ""


def test_version_emits_only_installed_package_version(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(command, "version", lambda name: "9.8.7")

    command.main(["--version"])

    captured = capsys.readouterr()

    assert captured.out == "9.8.7\n"
    assert captured.err == ""


def test_root_help_and_ordinary_chat_do_not_discover_plugins(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    discoveries = 0

    def entry_points() -> object:
        nonlocal discoveries
        discoveries += 1
        raise AssertionError("ordinary root behavior must not discover plugins")

    monkeypatch.setattr(
        external_information_command.importlib.metadata, "entry_points", entry_points
    )
    command.main([])

    received: list[list[str]] = []

    def chat(argv: list[str] | None = None) -> None:
        assert argv is not None
        received.append(argv)

    monkeypatch.setitem(command._COMMANDS, "chat", chat)
    command.main(["chat", "ordinary message"])

    assert discoveries == 0
    assert received == [["ordinary message"]]
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize(
    "argv",
    (
        ["unknown"],
        ["--unknown"],
        ["--help", "extra"],
        ["loc"],
        ["openai"],
        ["static-proof"],
        ["history"],
        ["explain-routing"],
    ),
)
def test_invalid_root_forms_use_the_exact_unknown_command_failure(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as raised:
        command.main(argv)

    captured = capsys.readouterr()

    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == "error: unknown command\n"


@pytest.mark.parametrize(
    ("name", "arguments"),
    (
        ("local", ["--runtime", "ollama"]),
        ("static-cluster", ["--declaration", "cluster.toml"]),
        ("compatibility", ["--declaration", "cluster.toml"]),
        ("aider", ["--file", "target.py", "--message", "Add a function"]),
        ("aider", ["--file", "target.py", "Refactor this function"]),
        ("code", ["--message", "Write a function"]),
        ("code", ["Write a function"]),
        ("code-file", ["--file", "target.py", "--message", "Add validation"]),
        ("code-file", ["--file", "target.py", "Add validation"]),
        (
            "external-information",
            ["--plugin", "selected", "--query", "query", "--question", "question"],
        ),
        ("chat", ["--message", "Hello"]),
        ("summarize", []),
        ("summarize", ["--text", "Source text"]),
        ("summarize", ["--file", "source.txt"]),
        ("preflight", ["--json"]),
        ("health", ["--json"]),
        ("status", ["--declaration", "cluster.toml", "--json"]),
    ),
)
def test_subcommands_delegate_the_exact_remaining_arguments(
    name: str, arguments: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    received: list[tuple[str, list[str]]] = []

    def make_delegate(command_name: str):
        def delegate(argv: list[str] | None = None) -> None:
            assert argv is not None
            received.append((command_name, argv))

        return delegate

    for command_name in command._COMMANDS:
        monkeypatch.setitem(
            command._COMMANDS, command_name, make_delegate(command_name)
        )

    command.main([name, *arguments])

    assert received == [(name, arguments)]


def test_subcommand_system_exit_propagates_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def delegate(argv: list[str] | None = None) -> None:
        raise SystemExit(17)

    monkeypatch.setitem(command._COMMANDS, "chat", delegate)

    with pytest.raises(SystemExit) as raised:
        command.main(["chat", "--message", "Hello"])

    assert raised.value.code == 17


@pytest.mark.parametrize(
    ("name", "target"),
    (
        ("local", command.local_runtime.main),
        ("static-cluster", command.static_cluster.main),
        ("compatibility", command.openai_compatibility.main),
        ("aider", aider_command.main),
        ("chat", command.chat_command.main),
        ("code", command.code_command.main),
        ("summarize", command.summarize_command.main),
        ("preflight", command.static_preflight.main),
        ("health", command.local_health_snapshot.main),
        ("status", command.status_command.main),
    ),
)
def test_dispatch_table_uses_existing_command_main_functions(name: str, target) -> None:
    assert command._COMMANDS[name] is target


def _run(capsys: pytest.CaptureFixture[str], invocation) -> tuple[int, str, str]:
    try:
        invocation()
    except SystemExit as error:
        exit_code = error.code
    else:
        exit_code = 0

    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


@pytest.mark.parametrize("argv", [["Hello"], ["--message", "Hello"]])
def test_chat_root_delegation_preserves_command_owned_request_and_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    requests: list[dict[str, object]] = []

    def post(
        request: dict[str, object], *, timeout_seconds: float, client_factory: object
    ) -> httpx.Response:
        assert timeout_seconds == 120.0
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "content": "answer",
                "adapter": "test-adapter",
                "model": "test-model",
                "node_id": "local",
            },
        )

    monkeypatch.setattr(chat_command, "_post_native_request", post)
    standalone = _run(capsys, lambda: chat_command.main(argv))
    standalone_requests = requests.copy()
    requests.clear()

    root = _run(capsys, lambda: command.main(["chat", *argv]))

    assert root == standalone
    assert (
        requests
        == standalone_requests
        == [
            {
                "messages": [{"role": "user", "content": "Hello"}],
                "capability": "chat",
            }
        ]
    )


def test_summarize_root_delegation_preserves_command_owned_request_and_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    requests: list[dict[str, object]] = []

    def post(
        request: dict[str, object], *, timeout_seconds: float, client_factory: object
    ) -> httpx.Response:
        assert timeout_seconds == 120.0
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "content": "summary",
                "adapter": "test-adapter",
                "model": "test-model",
                "node_id": "local",
            },
        )

    monkeypatch.setattr(summarize_command, "_post_native_request", post)
    standalone = _run(capsys, lambda: summarize_command.main(["--text", "Source text"]))
    standalone_requests = requests.copy()
    requests.clear()

    root = _run(capsys, lambda: command.main(["summarize", "--text", "Source text"]))

    assert root == standalone
    assert requests == standalone_requests == [{"text": "Source text"}]


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        (
            "aider",
            ["--timeout-seconds", "300", "--file", "target.py", "--message", "request"],
        ),
        ("chat", ["--timeout-seconds", "300", "Hello"]),
        ("summarize", ["--timeout-seconds", "300", "--text", "Source text"]),
    ],
)
def test_root_delegates_timeout_option_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    arguments: list[str],
) -> None:
    received: list[list[str]] = []

    def delegate(argv: list[str] | None = None) -> None:
        assert argv is not None
        received.append(argv)

    monkeypatch.setitem(command._COMMANDS, name, delegate)

    command.main([name, *arguments])

    assert received == [arguments]


def test_preflight_root_delegation_preserves_command_owned_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    report = {
        "status": "coherent",
        "operating_mode": "local-only",
        "nodes": [],
        "registered_adapters": [],
        "issues": [],
    }
    calls = 0

    def evaluate() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return report

    monkeypatch.setattr(static_preflight, "evaluate_static_preflight", evaluate)
    argv = ["--json"]

    standalone = _run(capsys, lambda: static_preflight.main(argv))
    standalone_calls = calls
    calls = 0

    root = _run(capsys, lambda: command.main(["preflight", *argv]))

    assert root == standalone
    assert standalone_calls == calls == 1


def test_health_root_delegation_preserves_command_owned_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    snapshot = {
        "nodes": [
            {
                "node_id": "local",
                "name": "Local node",
                "declared": {
                    "availability": "available",
                    "healthy": True,
                    "reason": None,
                    "capabilities": ["chat"],
                    "adapters": [],
                },
                "adapter_observations": [],
            }
        ]
    }
    calls = 0

    def evaluate() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return snapshot

    monkeypatch.setattr(local_health_snapshot, "evaluate_health_snapshot", evaluate)
    argv = ["--json"]

    standalone = _run(capsys, lambda: local_health_snapshot.main(argv))
    standalone_calls = calls
    calls = 0

    root = _run(capsys, lambda: command.main(["health", *argv]))

    assert root == standalone
    assert standalone_calls == calls == 1


def test_status_root_delegation_preserves_command_owned_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    declaration = tmp_path / "cluster.toml"
    declaration.write_text(
        'remote_node_id = "remote"\nbase_url = "http://remote.test:8000"\n',
        encoding="utf-8",
    )
    result = ClusterStatusResult.model_validate(
        {
            "declaration_status": "coherent",
            "nodes": [
                {
                    "node_id": "local",
                    "application_status": "local",
                    "runtime_status": "available",
                },
                {
                    "node_id": "remote",
                    "application_status": "reachable",
                    "runtime_status": "available",
                },
            ],
        }
    )

    async def evaluate(*_: object) -> ClusterStatusResult:
        return result

    monkeypatch.setattr(status_command, "evaluate_static_cluster_status", evaluate)
    argv = ["--declaration", str(declaration), "--json"]

    standalone = _run(capsys, lambda: status_command.main(argv))
    root_arguments: list[list[str]] = []

    def root_status(root_argv: list[str] | None = None) -> None:
        assert root_argv is not None
        root_arguments.append(root_argv)
        status_command.main(root_argv)

    monkeypatch.setitem(command._COMMANDS, "status", root_status)
    root = _run(capsys, lambda: command.main(["status", *argv]))

    assert root == standalone
    assert root_arguments == [argv]
