import json

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
from home_ai_cluster.static_preflight import (
    MISSING_ADAPTER_REASON,
    PREFLIGHT_FAILURE_MESSAGE,
    evaluate_static_preflight,
    main,
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


def test_main_emits_compact_coherent_report_and_exits_zero(
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

    main()

    captured = capsys.readouterr()
    assert captured.out == json.dumps(report, separators=(",", ":")) + "\n"
    assert captured.err == ""


def test_main_emits_incoherent_report_and_exits_nonzero(
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
        main()

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == json.dumps(report, separators=(",", ":")) + "\n"
    assert captured.err == ""


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
        main()

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == ""
    assert captured.err == PREFLIGHT_FAILURE_MESSAGE + "\n"
    assert "private-host" not in captured.err
