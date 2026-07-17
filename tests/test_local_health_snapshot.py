import json
import socket

import httpx
import pytest

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    ClusterStatusNode,
    ClusterStatusResult,
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
    main,
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

    snapshot = project_health_snapshot(
        NodeRegistry([node]), AdapterRegistry([adapter])
    )

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

    def create_nodes() -> NodeRegistry:
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

    result = project_local_cluster_status(snapshot)

    assert result.model_dump(mode="json") == {
        "declaration_status": "coherent",
        "nodes": [
            {
                "node_id": "local",
                "application_status": "local",
                "runtime_status": expected_runtime_status,
            }
        ],
    }
    assert adapter.health_calls == 1
    assert adapter.chat_calls == 0


def test_local_cluster_status_uses_cluster_owned_local_id_and_no_private_fields(
) -> None:
    snapshot = {
        "nodes": [
            {
                "node_id": "private-machine-name",
                "adapter_observations": [{"status": "available"}],
            }
        ]
    }

    result = project_local_cluster_status(snapshot)
    serialized = result.model_dump_json()

    assert result.nodes[0].node_id == "local"
    assert set(ClusterStatusResult.model_fields) == {"declaration_status", "nodes"}
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

    assert project_local_cluster_status(snapshot).nodes[0].runtime_status == "available"


def test_main_emits_one_compact_json_object_and_exits_zero(
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

    main()

    captured = capsys.readouterr()
    assert captured.out == json.dumps(snapshot, separators=(",", ":")) + "\n"
    assert captured.err == ""


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
        main()

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == ""
    assert captured.err == SNAPSHOT_FAILURE_MESSAGE + "\n"
    assert "private-host" not in captured.err
