import json
import socket

import httpx
import pytest

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    ClusterStatusNode,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.local_health_snapshot import (
    MISSING_ADAPTER_REASON,
    PROBE_FAILED_REASON,
    SNAPSHOT_FAILURE_MESSAGE,
    evaluate_health_snapshot,
    format_health_snapshot,
    main,
    parse_args,
    project_health_snapshot,
    project_local_cluster_status,
)


class FakeAdapter:
    def __init__(
        self,
        name: str,
        health_result: AdapterHealth | Exception,
    ) -> None:
        self._name = name
        self._health_result = health_result
        self.health_calls = 0
        self.chat_calls = 0

    @property
    def name(self) -> str:
        return self._name

    def health(self) -> AdapterHealth:
        self.health_calls += 1
        if isinstance(self._health_result, Exception):
            raise self._health_result
        return self._health_result

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.chat_calls += 1
        raise AssertionError("health snapshot must not execute chat")


def make_node(*adapter_names: str) -> NodeDescription:
    return NodeDescription(
        id="configured-local",
        name="Configured local node",
        availability="unknown",
        health=NodeHealth(healthy=False, reason="configured state"),
        capabilities=[Capability(name="chat"), Capability(name="code")],
        adapters=list(adapter_names),
    )


def test_projects_declared_node_metadata_without_rewriting_it() -> None:
    node = make_node("unavailable")
    adapter = FakeAdapter(
        "unavailable", AdapterHealth(available=False, reason="runtime unavailable")
    )

    snapshot = project_health_snapshot(NodeRegistry([node]), AdapterRegistry([adapter]))

    assert snapshot == {
        "nodes": [
            {
                "node_id": "configured-local",
                "name": "Configured local node",
                "declared": {
                    "availability": "unknown",
                    "healthy": False,
                    "reason": "configured state",
                    "capabilities": ["chat", "code"],
                    "adapters": ["unavailable"],
                },
                "adapter_observations": [
                    {
                        "adapter": "unavailable",
                        "status": "unavailable",
                        "reason": "runtime unavailable",
                    }
                ],
            }
        ]
    }


def test_projects_one_observation_per_declared_adapter_and_continues() -> None:
    available = FakeAdapter("available", AdapterHealth(available=True))
    unavailable = FakeAdapter(
        "unavailable", AdapterHealth(available=False, reason="not reachable")
    )
    failed = FakeAdapter(
        "failed", RuntimeError("http://private-host:11434 authorization=secret")
    )

    snapshot = project_health_snapshot(
        NodeRegistry([make_node("available", "unavailable", "missing", "failed")]),
        AdapterRegistry([available, unavailable, failed]),
    )

    observations = snapshot["nodes"][0]["adapter_observations"]
    assert observations == [
        {"adapter": "available", "status": "available", "reason": None},
        {
            "adapter": "unavailable",
            "status": "unavailable",
            "reason": "not reachable",
        },
        {
            "adapter": "missing",
            "status": "missing",
            "reason": MISSING_ADAPTER_REASON,
        },
        {
            "adapter": "failed",
            "status": "probe-failed",
            "reason": PROBE_FAILED_REASON,
        },
    ]
    assert len(observations) == 4
    assert "private-host" not in json.dumps(snapshot)
    assert available.chat_calls == 0
    assert unavailable.chat_calls == 0
    assert failed.chat_calls == 0


def test_evaluate_health_snapshot_uses_ordinary_static_local_registries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node_registry = NodeRegistry([make_node("available")])
    adapter_registry = AdapterRegistry(
        [FakeAdapter("available", AdapterHealth(available=True))]
    )
    calls: list[str] = []

    def create_nodes(*_: object) -> NodeRegistry:
        calls.append("nodes")
        return node_registry

    def create_adapters() -> AdapterRegistry:
        calls.append("adapters")
        return adapter_registry

    monkeypatch.setattr(
        "home_ai_cluster.local_health_snapshot.create_static_local_node_registry",
        create_nodes,
    )
    monkeypatch.setattr(
        "home_ai_cluster.local_health_snapshot.create_static_runtime_adapter_registry",
        create_adapters,
    )

    snapshot = evaluate_health_snapshot()

    assert calls == ["nodes", "adapters"]
    assert snapshot["nodes"][0]["node_id"] == "configured-local"


def test_default_health_snapshot_uses_ordinary_local_capabilities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.local_runtime_composition import LOCAL_RUNTIME_CAPABILITY_NAMES

    captured: list[tuple[str, ...]] = []
    node = make_node("available")
    adapter = FakeAdapter("available", AdapterHealth(available=True))

    def create_nodes(capabilities: tuple[str, ...]) -> NodeRegistry:
        captured.append(capabilities)
        return NodeRegistry(
            [
                node.model_copy(
                    update={
                        "capabilities": [Capability(name=name) for name in capabilities]
                    }
                )
            ]
        )

    monkeypatch.setattr(
        "home_ai_cluster.local_health_snapshot.create_static_local_node_registry",
        create_nodes,
    )
    monkeypatch.setattr(
        "home_ai_cluster.local_health_snapshot.create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    snapshot = evaluate_health_snapshot()

    assert captured == [LOCAL_RUNTIME_CAPABILITY_NAMES]
    assert snapshot["nodes"][0]["declared"]["capabilities"] == [
        "chat",
        "summarize",
        "classify",
    ]


@pytest.mark.parametrize(
    ("health", "expected_runtime_status"),
    [
        (AdapterHealth(available=True), "available"),
        (AdapterHealth(available=False), "unavailable"),
        (RuntimeError("private runtime failure"), "observation-failed"),
    ],
)
def test_projects_completed_local_health_observation_to_normalized_cluster_status(
    health: AdapterHealth | Exception,
    expected_runtime_status: str,
) -> None:
    adapter = FakeAdapter("local-runtime", health)
    snapshot = project_health_snapshot(
        NodeRegistry([make_node("local-runtime")]), AdapterRegistry([adapter])
    )

    node = project_local_cluster_status(snapshot)

    assert node.model_dump(mode="json") == {
        "node_id": "local",
        "application_status": "local",
        "runtime_status": expected_runtime_status,
    }
    assert adapter.health_calls == 1
    assert adapter.chat_calls == 0


def test_local_cluster_status_uses_cluster_owned_local_id_and_no_private_fields() -> (
    None
):
    snapshot = {
        "nodes": [
            {
                "node_id": "private-machine-name",
                "adapter_observations": [{"status": "available"}],
            }
        ]
    }

    node = project_local_cluster_status(snapshot)
    serialized = node.model_dump_json()

    assert node.node_id == "local"
    assert node.application_status == "local"
    assert set(ClusterStatusNode.model_fields) == {
        "node_id",
        "application_status",
        "runtime_status",
    }
    assert "private-machine-name" not in serialized
    assert "adapter" not in serialized
    assert "reason" not in serialized


def test_local_cluster_status_projection_performs_no_network_or_health_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*_: object, **__: object) -> None:
        raise AssertionError("status projection must not access the network")

    monkeypatch.setattr(httpx, "AsyncClient", fail_if_called)
    monkeypatch.setattr(socket, "getaddrinfo", fail_if_called)
    snapshot = {
        "nodes": [
            {
                "node_id": "configured-local",
                "adapter_observations": [{"status": "available"}],
            }
        ]
    }

    assert project_local_cluster_status(snapshot).runtime_status == "available"


def test_parse_args_selects_json_only_when_requested() -> None:
    assert parse_args([]).json is False
    assert parse_args(["--json"]).json is True
    assert parse_args(["--json", "--json"]).json is True


@pytest.mark.parametrize("argv", [["--json", "true"], ["--unknown"]])
def test_invalid_arguments_do_not_evaluate_health_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_evaluation() -> dict[str, object]:
        raise AssertionError("invalid arguments must not evaluate health")

    monkeypatch.setattr(
        "home_ai_cluster.local_health_snapshot.evaluate_health_snapshot",
        fail_evaluation,
    )

    with pytest.raises(SystemExit) as raised:
        main(argv)

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == ""
    assert "usage: home-ai-cluster-health" in captured.err


def test_main_json_preserves_one_compact_json_object_and_exits_zero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
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
    monkeypatch.setattr(
        "home_ai_cluster.local_health_snapshot.evaluate_health_snapshot",
        lambda: snapshot,
    )

    main(["--json"])

    captured = capsys.readouterr()
    assert captured.out == json.dumps(snapshot, separators=(",", ":")) + "\n"
    assert captured.err == ""
    assert "Local health" not in captured.out


def test_main_json_preserves_representative_observation_values_and_order(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot = {
        "nodes": [
            {
                "node_id": "first",
                "name": "First node",
                "declared": {
                    "availability": "available",
                    "healthy": True,
                    "reason": None,
                    "capabilities": ["chat"],
                    "adapters": ["available", "unavailable", "missing", "failed"],
                },
                "adapter_observations": [
                    {"adapter": "available", "status": "available", "reason": None},
                    {
                        "adapter": "unavailable",
                        "status": "unavailable",
                        "reason": "runtime unavailable",
                    },
                    {
                        "adapter": "missing",
                        "status": "missing",
                        "reason": MISSING_ADAPTER_REASON,
                    },
                    {
                        "adapter": "failed",
                        "status": "probe-failed",
                        "reason": PROBE_FAILED_REASON,
                    },
                ],
            }
        ]
    }
    monkeypatch.setattr(
        "home_ai_cluster.local_health_snapshot.evaluate_health_snapshot",
        lambda: snapshot,
    )

    main(["--json"])

    captured = capsys.readouterr()
    assert captured.out == json.dumps(snapshot, separators=(",", ":")) + "\n"
    assert captured.err == ""


def test_main_defaults_to_human_readable_health_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
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
                    "adapters": ["ollama"],
                },
                "adapter_observations": [
                    {"adapter": "ollama", "status": "available", "reason": None}
                ],
            }
        ]
    }
    monkeypatch.setattr(
        "home_ai_cluster.local_health_snapshot.evaluate_health_snapshot",
        lambda: snapshot,
    )

    main([])

    captured = capsys.readouterr()
    assert captured.out == (
        "Local health\n\n"
        "Nodes:\n"
        "- local\n"
        "  Name: Local node\n\n"
        "  Declared state:\n"
        "    Availability: available\n"
        "    Healthy: true\n"
        "    Reason: none\n"
        "    Capabilities: chat\n"
        "    Adapters: ollama\n\n"
        "  Adapter observations:\n"
        "  - Adapter: ollama\n"
        "    Status: available\n"
        "    Reason: none\n"
    )
    assert captured.err == ""
    assert '{"nodes"' not in captured.out
    assert "\x1b" not in captured.out


def test_formats_declared_state_and_observations_without_synthesizing_health() -> None:
    snapshot = {
        "nodes": [
            {
                "node_id": "first",
                "name": "First node",
                "declared": {
                    "availability": "available",
                    "healthy": True,
                    "reason": None,
                    "capabilities": ["chat"],
                    "adapters": ["available", "unavailable"],
                },
                "adapter_observations": [
                    {"adapter": "available", "status": "available", "reason": None},
                    {
                        "adapter": "unavailable",
                        "status": "unavailable",
                        "reason": "runtime unavailable",
                    },
                ],
            },
            {
                "node_id": "second",
                "name": "Second node",
                "declared": {
                    "availability": "unavailable",
                    "healthy": False,
                    "reason": "declared maintenance",
                    "capabilities": [],
                    "adapters": ["missing", "failed"],
                },
                "adapter_observations": [
                    {
                        "adapter": "missing",
                        "status": "missing",
                        "reason": MISSING_ADAPTER_REASON,
                    },
                    {
                        "adapter": "failed",
                        "status": "probe-failed",
                        "reason": PROBE_FAILED_REASON,
                    },
                ],
            },
        ]
    }

    rendered = format_health_snapshot(snapshot)

    assert rendered == (
        "Local health\n\n"
        "Nodes:\n"
        "- first\n"
        "  Name: First node\n\n"
        "  Declared state:\n"
        "    Availability: available\n"
        "    Healthy: true\n"
        "    Reason: none\n"
        "    Capabilities: chat\n"
        "    Adapters: available, unavailable\n\n"
        "  Adapter observations:\n"
        "  - Adapter: available\n"
        "    Status: available\n"
        "    Reason: none\n"
        "  - Adapter: unavailable\n"
        "    Status: unavailable\n"
        "    Reason: runtime unavailable\n\n"
        "- second\n"
        "  Name: Second node\n\n"
        "  Declared state:\n"
        "    Availability: unavailable\n"
        "    Healthy: false\n"
        "    Reason: declared maintenance\n"
        "    Capabilities: none\n"
        "    Adapters: missing, failed\n\n"
        "  Adapter observations:\n"
        "  - Adapter: missing\n"
        f"    Status: missing\n    Reason: {MISSING_ADAPTER_REASON}\n"
        "  - Adapter: failed\n"
        f"    Status: probe-failed\n    Reason: {PROBE_FAILED_REASON}"
    )
    assert rendered.index("- first") < rendered.index("- second")
    assert rendered.index("Adapter: available") < rendered.index("Adapter: unavailable")
    assert "Overall health" not in rendered
    assert "Health status" not in rendered
    assert "Degraded" not in rendered
    assert not rendered.endswith("\n")


def test_formats_empty_collections_explicitly() -> None:
    assert format_health_snapshot({"nodes": []}) == "Local health\n\nNodes: none"

    snapshot = {
        "nodes": [
            {
                "node_id": "empty",
                "name": "Empty node",
                "declared": {
                    "availability": "unknown",
                    "healthy": False,
                    "reason": None,
                    "capabilities": [],
                    "adapters": [],
                },
                "adapter_observations": [],
            }
        ]
    }

    rendered = format_health_snapshot(snapshot)

    assert "Capabilities: none" in rendered
    assert "Adapters: none" in rendered
    assert "Adapter observations: none" in rendered


def test_main_reports_safe_error_for_whole_snapshot_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_snapshot() -> dict[str, object]:
        raise RuntimeError("http://private-host:11434 authorization=secret")

    monkeypatch.setattr(
        "home_ai_cluster.local_health_snapshot.evaluate_health_snapshot",
        fail_snapshot,
    )

    with pytest.raises(SystemExit) as raised:
        main([])

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == ""
    assert captured.err == SNAPSHOT_FAILURE_MESSAGE + "\n"
    assert "private-host" not in captured.err
