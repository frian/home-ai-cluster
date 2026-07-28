import json
import socket

import httpx
import pytest

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.static_cluster import REMOTE_HTTP_ADAPTER_NAME
from home_ai_cluster.static_cluster_declaration import (
    StaticClusterDeclarationError,
    load_static_cluster_declarations,
)
from home_ai_cluster.static_preflight import (
    MISSING_ADAPTER_REASON,
    PREFLIGHT_FAILURE_MESSAGE,
    evaluate_static_declarations_preflight,
    evaluate_static_multi_node_preflight,
    evaluate_static_preflight,
    format_static_preflight_report,
    main,
    parse_args,
    project_static_preflight,
)


class FakeAdapter:
    def __init__(self, name: str) -> None:
        self._name = name
        self.health_calls = 0
        self.capability_calls = 0
        self.chat_calls = 0

    @property
    def name(self) -> str:
        return self._name

    def health(self) -> AdapterHealth:
        self.health_calls += 1
        raise AssertionError("preflight must not call health")

    def capabilities(self) -> list[Capability]:
        self.capability_calls += 1
        raise AssertionError("preflight must not call capabilities")

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.chat_calls += 1
        raise AssertionError("preflight must not call chat")


def make_node(
    node_id: str,
    capabilities: list[str],
    adapters: list[str],
) -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"Private display name for {node_id}",
        availability="unknown",
        health=NodeHealth(healthy=False, reason="private configured reason"),
        capabilities=[Capability(name=name) for name in capabilities],
        adapters=adapters,
    )


def test_projects_coherent_report_in_registry_order_without_runtime_calls() -> None:
    first = FakeAdapter("ollama")
    second = FakeAdapter("llama-server")
    node_registry = NodeRegistry(
        [
            make_node("local", ["chat", "code"], ["ollama"]),
            make_node("secondary", ["chat"], ["llama-server", "ollama"]),
        ]
    )
    adapter_registry = AdapterRegistry([first, second])

    report = project_static_preflight(node_registry, adapter_registry)

    assert report == {
        "status": "coherent",
        "operating_mode": "local-only",
        "nodes": [
            {
                "node_id": "local",
                "capabilities": ["chat", "code"],
                "declared_adapters": ["ollama"],
            },
            {
                "node_id": "secondary",
                "capabilities": ["chat"],
                "declared_adapters": ["llama-server", "ollama"],
            },
        ],
        "registered_adapters": ["ollama", "llama-server"],
        "issues": [],
    }
    assert first.health_calls == 0
    assert first.capability_calls == 0
    assert first.chat_calls == 0
    assert second.health_calls == 0
    assert second.capability_calls == 0
    assert second.chat_calls == 0


def test_projects_missing_adapters_in_node_and_declaration_order() -> None:
    present = FakeAdapter("present")
    report = project_static_preflight(
        NodeRegistry(
            [
                make_node("first", ["chat"], ["missing-a", "present"]),
                make_node("second", ["code"], ["missing-b", "missing-c"]),
            ]
        ),
        AdapterRegistry([present]),
    )

    assert report["status"] == "incoherent"
    assert report["issues"] == [
        {
            "status": "missing-adapter",
            "node_id": "first",
            "adapter": "missing-a",
            "reason": MISSING_ADAPTER_REASON,
        },
        {
            "status": "missing-adapter",
            "node_id": "second",
            "adapter": "missing-b",
            "reason": MISSING_ADAPTER_REASON,
        },
        {
            "status": "missing-adapter",
            "node_id": "second",
            "adapter": "missing-c",
            "reason": MISSING_ADAPTER_REASON,
        },
    ]


def test_report_excludes_private_and_runtime_details() -> None:
    report = project_static_preflight(
        NodeRegistry([make_node("local", ["chat"], ["missing"])]),
        AdapterRegistry(),
    )

    serialized = json.dumps(report)
    assert "Private display name" not in serialized
    assert "private configured reason" not in serialized
    assert "availability" not in serialized
    assert "healthy" not in serialized
    assert "runtime_url" not in serialized


def test_evaluate_uses_ordinary_static_local_registries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node_registry = NodeRegistry([make_node("local", ["chat"], ["ollama"])])
    adapter_registry = AdapterRegistry([FakeAdapter("ollama")])
    calls: list[str] = []

    def create_nodes() -> NodeRegistry:
        calls.append("nodes")
        return node_registry

    def create_adapters() -> AdapterRegistry:
        calls.append("adapters")
        return adapter_registry

    monkeypatch.setattr(
        "home_ai_cluster.static_preflight.create_static_local_node_registry",
        create_nodes,
    )
    monkeypatch.setattr(
        "home_ai_cluster.static_preflight.create_static_runtime_adapter_registry",
        create_adapters,
    )

    report = evaluate_static_preflight()

    assert calls == ["nodes", "adapters"]
    assert report["status"] == "coherent"


def test_parse_args_preserves_local_only_without_remote_declaration() -> None:
    args = parse_args([])

    assert args.json is False
    assert args.remote_node_id is None
    assert args.remote_base_url is None


@pytest.mark.parametrize(
    "argv",
    [
        ["--json"],
        ["--declaration", "cluster.toml", "--json"],
        [
            "--remote-node-id",
            "declared-remote",
            "--remote-base-url",
            "https://remote.example",
            "--remote-capability",
            "chat",
            "--json",
        ],
    ],
)
def test_parse_args_accepts_json_for_each_valid_preflight_mode(
    argv: list[str],
) -> None:
    assert parse_args(argv).json is True


@pytest.mark.parametrize(
    "argv",
    [
        ["--json", "true"],
        ["--declaration", "cluster.toml", "--json", "true"],
        ["--json", "--unexpected"],
    ],
)
def test_parse_args_rejects_invalid_json_usage(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        parse_args(argv)


@pytest.mark.parametrize(
    "argv",
    [
        ["--remote-node-id", "declared-remote"],
        ["--remote-base-url", "https://remote.example"],
        [
            "--remote-node-id",
            "",
            "--remote-base-url",
            "https://remote.example",
        ],
        [
            "--remote-node-id",
            "local",
            "--remote-base-url",
            "https://remote.example",
        ],
        [
            "--remote-node-id",
            "declared-remote",
            "--remote-base-url",
            "remote.example",
        ],
        [
            "--declaration",
            "cluster.toml",
            "--remote-node-id",
            "declared-remote",
            "--remote-base-url",
            "https://remote.example",
            "--json",
        ],
        ["--remote-capability", "chat"],
        [
            "--remote-node-id",
            "declared-remote",
            "--remote-capability",
            "chat",
        ],
        [
            "--remote-base-url",
            "https://remote.example",
            "--remote-capability",
            "chat",
        ],
        [
            "--declaration",
            "cluster.toml",
            "--remote-capability",
            "chat",
        ],
    ],
)
def test_parse_args_rejects_incomplete_or_invalid_remote_declaration(
    argv: list[str],
) -> None:
    with pytest.raises(SystemExit):
        parse_args(argv)


def test_parse_args_normalizes_remote_url_like_static_cluster() -> None:
    args = parse_args(
        [
            "--remote-node-id",
            "declared-remote",
            "--remote-base-url",
            "https://remote.example:8000/",
        ]
    )

    assert args.remote_node_id == "declared-remote"
    assert args.remote_base_url == "https://remote.example:8000"


def test_multi_node_preflight_projects_local_then_remote_without_network_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*_: object, **__: object) -> None:
        raise AssertionError("preflight must not construct or use a network client")

    monkeypatch.setattr(httpx, "AsyncClient", fail_network)
    monkeypatch.setattr(socket, "getaddrinfo", fail_network)

    remote_url = "https://private.example:9443"
    report = evaluate_static_multi_node_preflight("declared-remote", remote_url)

    assert report == {
        "status": "coherent",
        "operating_mode": "static-multi-node",
        "nodes": [
            {
                "node_id": "local",
                "capabilities": ["chat", "summarize"],
                "declared_adapters": ["ollama"],
            },
            {
                "node_id": "declared-remote",
                "capabilities": ["chat", "summarize"],
                "declared_adapters": [REMOTE_HTTP_ADAPTER_NAME],
            },
        ],
        "registered_adapters": ["ollama"],
        "issues": [],
    }
    assert remote_url not in json.dumps(report)


def test_multi_node_preflight_does_not_resolve_remote_http_boundary_locally() -> None:
    local = make_node("local", ["chat"], ["local-adapter"])
    report = evaluate_static_multi_node_preflight(
        "declared-remote",
        "https://remote.example",
        node_registry=NodeRegistry([local]),
        adapter_registry=AdapterRegistry([FakeAdapter("local-adapter")]),
    )

    assert report["status"] == "coherent"
    assert report["issues"] == []
    assert report["nodes"][-1]["declared_adapters"] == [REMOTE_HTTP_ADAPTER_NAME]


@pytest.mark.parametrize(
    ("capabilities", "expected"),
    [
        (("chat",), ["chat"]),
        (("summarize",), ["summarize"]),
        (("chat", "summarize"), ["chat", "summarize"]),
    ],
)
def test_inline_multi_node_preflight_projects_explicit_capabilities(
    capabilities: tuple[str, ...],
    expected: list[str],
) -> None:
    report = evaluate_static_multi_node_preflight(
        "declared-remote",
        "https://remote.example",
        capabilities=capabilities,
    )

    assert report["nodes"][-1]["capabilities"] == expected


@pytest.mark.parametrize(
    ("capabilities", "message"),
    [
        (("unknown",), "unknown remote capability"),
        (("chat", "chat"), "duplicate remote capability"),
        ((), "remote capabilities must not be empty"),
    ],
)
def test_inline_multi_node_preflight_rejects_invalid_capabilities(
    capabilities: tuple[str, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        evaluate_static_multi_node_preflight(
            "declared-remote",
            "https://remote.example",
            capabilities=capabilities,
        )


@pytest.mark.parametrize(
    ("local_capabilities", "expected"),
    [
        ('["chat"]', ["chat"]),
        ('["summarize"]', ["summarize"]),
        ('["summarize", "chat"]', ["summarize", "chat"]),
        (None, ["chat", "summarize"]),
    ],
)
def test_declaration_preflight_projects_caller_local_capabilities_without_network_use(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    local_capabilities: str | None,
    expected: list[str],
) -> None:
    def fail_network(*_: object, **__: object) -> None:
        raise AssertionError("declaration preflight must not use the network")

    monkeypatch.setattr(httpx, "AsyncClient", fail_network)
    monkeypatch.setattr(socket, "getaddrinfo", fail_network)
    local_line = (
        f"local_capabilities = {local_capabilities}\n" if local_capabilities else ""
    )
    path = tmp_path / "cluster.toml"
    path.write_text(
        local_line
        + "[[remote_nodes]]\n"
        + 'node_id = "summary-remote"\n'
        + 'base_url = "https://remote.example"\n'
        + 'capabilities = ["summarize"]\n',
        encoding="utf-8",
    )

    report = evaluate_static_declarations_preflight(
        load_static_cluster_declarations(path)
    )

    assert report["nodes"] == [
        {
            "node_id": "local",
            "capabilities": expected,
            "declared_adapters": ["ollama"],
        },
        {
            "node_id": "summary-remote",
            "capabilities": ["summarize"],
            "declared_adapters": [REMOTE_HTTP_ADAPTER_NAME],
        },
    ]


@pytest.mark.parametrize(
    "local_capabilities",
    ["[]", '["chat", "chat"]', '["unknown"]'],
)
def test_declaration_preflight_rejects_invalid_local_capabilities_before_network_use(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    local_capabilities: str,
) -> None:
    def fail_network(*_: object, **__: object) -> None:
        raise AssertionError("invalid local capabilities must fail before network use")

    monkeypatch.setattr(httpx, "AsyncClient", fail_network)
    monkeypatch.setattr(socket, "getaddrinfo", fail_network)
    path = tmp_path / "cluster.toml"
    path.write_text(
        f"local_capabilities = {local_capabilities}\n"
        "[[remote_nodes]]\n"
        'node_id = "summary-remote"\n'
        'base_url = "https://remote.example"\n',
        encoding="utf-8",
    )

    with pytest.raises(StaticClusterDeclarationError):
        evaluate_static_declarations_preflight(load_static_cluster_declarations(path))


def test_main_json_emits_compact_coherent_report_and_exits_zero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = {
        "status": "coherent",
        "operating_mode": "local-only",
        "nodes": [],
        "registered_adapters": [],
        "issues": [],
    }
    monkeypatch.setattr(
        "home_ai_cluster.static_preflight.evaluate_static_preflight",
        lambda: report,
    )

    main(["--json"])

    captured = capsys.readouterr()
    assert captured.out == json.dumps(report, separators=(",", ":")) + "\n"
    assert captured.err == ""
    assert "Preflight:" not in captured.out


def test_main_json_emits_static_multi_node_report_without_remote_url(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = {
        "status": "coherent",
        "operating_mode": "static-multi-node",
        "nodes": [],
        "registered_adapters": [],
        "issues": [],
    }
    remote_url = "https://private.example:9443"
    calls: list[tuple[str, str, tuple[str, ...]]] = []

    def evaluate_multi(
        node_id: str,
        base_url: str,
        *,
        capabilities: tuple[str, ...],
    ) -> dict[str, object]:
        calls.append((node_id, base_url, capabilities))
        return report

    monkeypatch.setattr(
        "home_ai_cluster.static_preflight.evaluate_static_multi_node_preflight",
        evaluate_multi,
    )

    main(
        [
            "--remote-node-id",
            "declared-remote",
            "--remote-base-url",
            remote_url,
            "--remote-capability",
            "summarize",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert calls == [("declared-remote", remote_url, ("summarize",))]
    assert captured.out == json.dumps(report, separators=(",", ":")) + "\n"
    assert captured.err == ""
    assert remote_url not in captured.out


def test_main_json_emits_incoherent_report_and_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = {
        "status": "incoherent",
        "operating_mode": "local-only",
        "nodes": [],
        "registered_adapters": [],
        "issues": [
            {
                "status": "missing-adapter",
                "node_id": "local",
                "adapter": "missing",
                "reason": MISSING_ADAPTER_REASON,
            }
        ],
    }
    monkeypatch.setattr(
        "home_ai_cluster.static_preflight.evaluate_static_preflight",
        lambda: report,
    )

    with pytest.raises(SystemExit) as raised:
        main(["--json"])

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == json.dumps(report, separators=(",", ":")) + "\n"
    assert captured.err == ""


def test_main_human_emits_coherent_local_only_report(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = {
        "status": "coherent",
        "operating_mode": "local-only",
        "nodes": [
            {
                "node_id": "local",
                "capabilities": ["chat"],
                "declared_adapters": ["ollama"],
            }
        ],
        "registered_adapters": ["ollama"],
        "issues": [],
    }
    monkeypatch.setattr(
        "home_ai_cluster.static_preflight.evaluate_static_preflight",
        lambda: report,
    )

    main([])

    captured = capsys.readouterr()
    assert captured.out == (
        "Preflight: coherent\n"
        "Operating mode: local-only\n"
        "\n"
        "Nodes:\n"
        "- local\n"
        "  Capabilities: chat\n"
        "  Declared adapters: ollama\n"
        "\n"
        "Registered adapters: ollama\n"
        "Issues: none\n"
    )
    assert captured.err == ""
    assert "\x1b[" not in captured.out
    assert not captured.out.lstrip().startswith("{")


def test_main_human_emits_incoherent_report_and_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = {
        "status": "incoherent",
        "operating_mode": "local-only",
        "nodes": [
            {
                "node_id": "local",
                "capabilities": ["chat"],
                "declared_adapters": ["missing-adapter"],
            }
        ],
        "registered_adapters": ["ollama"],
        "issues": [
            {
                "status": "missing-adapter",
                "node_id": "local",
                "adapter": "missing-adapter",
                "reason": MISSING_ADAPTER_REASON,
            }
        ],
    }
    monkeypatch.setattr(
        "home_ai_cluster.static_preflight.evaluate_static_preflight",
        lambda: report,
    )

    with pytest.raises(SystemExit) as raised:
        main([])

    captured = capsys.readouterr()
    assert raised.value.code == 1
    assert captured.out == (
        "Preflight: incoherent\n"
        "Operating mode: local-only\n"
        "\n"
        "Nodes:\n"
        "- local\n"
        "  Capabilities: chat\n"
        "  Declared adapters: missing-adapter\n"
        "\n"
        "Registered adapters: ollama\n"
        "\n"
        "Issues:\n"
        "- Status: missing-adapter\n"
        "  Node: local\n"
        "  Adapter: missing-adapter\n"
        f"  Reason: {MISSING_ADAPTER_REASON}\n"
    )
    assert captured.err == ""


def test_format_static_preflight_report_preserves_node_and_issue_order() -> None:
    report = {
        "status": "incoherent",
        "operating_mode": "static-multi-node",
        "nodes": [
            {
                "node_id": "local",
                "capabilities": ["chat", "code"],
                "declared_adapters": ["ollama", "missing-a"],
            },
            {
                "node_id": "remote",
                "capabilities": ["chat"],
                "declared_adapters": ["remote-http"],
            },
        ],
        "registered_adapters": ["ollama", "llama-server"],
        "issues": [
            {
                "status": "missing-adapter",
                "node_id": "local",
                "adapter": "missing-a",
                "reason": "first issue",
            },
            {
                "status": "missing-adapter",
                "node_id": "remote",
                "adapter": "missing-b",
                "reason": "second issue",
            },
        ],
    }

    formatted = format_static_preflight_report(report)

    assert formatted == (
        "Preflight: incoherent\n"
        "Operating mode: static-multi-node\n"
        "\n"
        "Nodes:\n"
        "- local\n"
        "  Capabilities: chat, code\n"
        "  Declared adapters: ollama, missing-a\n"
        "- remote\n"
        "  Capabilities: chat\n"
        "  Declared adapters: remote-http\n"
        "\n"
        "Registered adapters: ollama, llama-server\n"
        "\n"
        "Issues:\n"
        "- Status: missing-adapter\n"
        "  Node: local\n"
        "  Adapter: missing-a\n"
        "  Reason: first issue\n"
        "- Status: missing-adapter\n"
        "  Node: remote\n"
        "  Adapter: missing-b\n"
        "  Reason: second issue"
    )
    assert not formatted.endswith("\n")
    assert "\x1b[" not in formatted


def test_format_static_preflight_report_makes_empty_values_explicit() -> None:
    report = {
        "status": "coherent",
        "operating_mode": "local-only",
        "nodes": [
            {
                "node_id": "local",
                "capabilities": [],
                "declared_adapters": [],
            }
        ],
        "registered_adapters": [],
        "issues": [],
    }

    assert format_static_preflight_report(report) == (
        "Preflight: coherent\n"
        "Operating mode: local-only\n"
        "\n"
        "Nodes:\n"
        "- local\n"
        "  Capabilities: none\n"
        "  Declared adapters: none\n"
        "\n"
        "Registered adapters: none\n"
        "Issues: none"
    )


def test_format_static_preflight_report_makes_empty_nodes_explicit() -> None:
    report = {
        "status": "coherent",
        "operating_mode": "local-only",
        "nodes": [],
        "registered_adapters": [],
        "issues": [],
    }

    assert format_static_preflight_report(report) == (
        "Preflight: coherent\n"
        "Operating mode: local-only\n"
        "\n"
        "Nodes: none\n"
        "\n"
        "Registered adapters: none\n"
        "Issues: none"
    )


def test_main_reports_safe_construction_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_report() -> dict[str, object]:
        raise RuntimeError("http://private-host:11434 authorization=secret")

    monkeypatch.setattr(
        "home_ai_cluster.static_preflight.evaluate_static_preflight",
        fail_report,
    )

    with pytest.raises(SystemExit) as raised:
        main([])

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == ""
    assert captured.err == PREFLIGHT_FAILURE_MESSAGE + "\n"
    assert "private-host" not in captured.err


def test_main_hides_remote_url_when_multi_node_construction_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    remote_url = "https://private.example:9443"

    def fail_declaration(*_: object) -> None:
        raise RuntimeError(remote_url)

    monkeypatch.setattr(
        "home_ai_cluster.static_preflight.create_remote_declaration",
        fail_declaration,
    )

    with pytest.raises(SystemExit) as raised:
        main(
            [
                "--remote-node-id",
                "declared-remote",
                "--remote-base-url",
                remote_url,
            ]
        )

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == ""
    assert captured.err == PREFLIGHT_FAILURE_MESSAGE + "\n"
    assert remote_url not in captured.err
