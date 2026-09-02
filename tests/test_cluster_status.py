import asyncio

import httpx
import pytest

from home_ai_cluster.core.cluster_status import collect_static_cluster_status
from home_ai_cluster.core.models import (
    AdapterHealth,
    ApplicationStatus,
    Capability,
    ClusterRequest,
    ClusterStatusNode,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
    RuntimeStatus,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.remote_transport import HttpRemoteStatusTransport


class LocalAdapter:
    def __init__(self, health_result: AdapterHealth | Exception) -> None:
        self._health_result = health_result
        self.health_calls = 0
        self.chat_calls = 0

    @property
    def name(self) -> str:
        return "private-local-adapter"

    def health(self) -> AdapterHealth:
        self.health_calls += 1
        if isinstance(self._health_result, Exception):
            raise self._health_result
        return self._health_result

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.chat_calls += 1
        raise AssertionError("status collection must not execute chat")


class RecordingRemoteStatusTransport(HttpRemoteStatusTransport):
    def __init__(self, results: dict[str, ClusterStatusNode]) -> None:
        self._results = results
        self.calls: list[str] = []
        self.events: list[str] = []
        self._active_node_id: str | None = None

    async def observe(
        self,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterStatusNode:
        node_id = declaration.node.id
        self.events.append(f"start:{node_id}")
        if self._active_node_id is not None:
            raise AssertionError("remote status observations must be sequential")
        self._active_node_id = node_id
        self.calls.append(node_id)
        await asyncio.sleep(0)
        assert self._active_node_id == node_id
        self._active_node_id = None
        self.events.append(f"complete:{node_id}")
        return self._results[node_id]


def make_local_node() -> NodeDescription:
    return NodeDescription(
        id="private-local-machine",
        name="Private local machine",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["private-local-adapter"],
    )


def make_remote_declaration(node_id: str) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id=node_id,
            name=f"Private remote machine {node_id}",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="chat")],
            adapters=[f"private-adapter-{node_id}"],
        ),
        transport_address=f"http://{node_id}.private.example:8000",
    )


def remote_status(
    node_id: str,
    application_status: ApplicationStatus = ApplicationStatus.REACHABLE,
    runtime_status: RuntimeStatus = RuntimeStatus.AVAILABLE,
) -> ClusterStatusNode:
    return ClusterStatusNode(
        node_id=node_id,
        application_status=application_status,
        runtime_status=runtime_status,
    )


def collect(
    adapter: LocalAdapter,
    declarations: list[RemoteNodeDeclaration],
    transport: RecordingRemoteStatusTransport,
):
    return asyncio.run(
        collect_static_cluster_status(
            NodeRegistry([make_local_node()]),
            AdapterRegistry([adapter]),
            RemoteNodeDeclarationRegistry(declarations),
            transport,
        )
    )


def test_collects_only_the_fixed_local_node_when_no_remotes_are_declared() -> None:
    adapter = LocalAdapter(AdapterHealth(available=True))
    transport = RecordingRemoteStatusTransport({})

    result = collect(adapter, [], transport)

    assert result.model_dump(mode="json") == {
        "declaration_status": "coherent",
        "nodes": [
            {
                "node_id": "local",
                "application_status": "local",
                "runtime_status": "available",
            }
        ],
    }
    assert adapter.health_calls == 1
    assert adapter.chat_calls == 0
    assert transport.calls == []


def test_collects_local_then_every_remote_in_declaration_order() -> None:
    declarations = [
        make_remote_declaration("remote-z"),
        make_remote_declaration("remote-a"),
        make_remote_declaration("remote-m"),
    ]
    transport = RecordingRemoteStatusTransport(
        {
            declaration.node.id: remote_status(declaration.node.id)
            for declaration in declarations
        }
    )

    result = collect(
        LocalAdapter(AdapterHealth(available=True)), declarations, transport
    )

    assert [node.node_id for node in result.nodes] == [
        "local",
        "remote-z",
        "remote-a",
        "remote-m",
    ]
    assert transport.calls == ["remote-z", "remote-a", "remote-m"]
    assert transport.events == [
        "start:remote-z",
        "complete:remote-z",
        "start:remote-a",
        "complete:remote-a",
        "start:remote-m",
        "complete:remote-m",
    ]


@pytest.mark.parametrize(
    "failed_status",
    [
        remote_status(
            "remote-first",
            ApplicationStatus.UNREACHABLE,
            RuntimeStatus.UNKNOWN,
        ),
        remote_status(
            "remote-first",
            ApplicationStatus.REQUEST_FAILED,
            RuntimeStatus.UNKNOWN,
        ),
        remote_status(
            "remote-first",
            ApplicationStatus.INVALID_RESPONSE,
            RuntimeStatus.UNKNOWN,
        ),
    ],
)
def test_continues_after_each_normalized_remote_failure(
    failed_status: ClusterStatusNode,
) -> None:
    declarations = [
        make_remote_declaration("remote-first"),
        make_remote_declaration("remote-second"),
    ]
    transport = RecordingRemoteStatusTransport(
        {
            "remote-first": failed_status,
            "remote-second": remote_status("remote-second"),
        }
    )

    result = collect(
        LocalAdapter(AdapterHealth(available=True)), declarations, transport
    )

    assert [node.node_id for node in result.nodes] == [
        "local",
        "remote-first",
        "remote-second",
    ]
    assert result.nodes[1] is failed_status
    assert result.nodes[2] == remote_status("remote-second")
    assert transport.calls == ["remote-first", "remote-second"]


@pytest.mark.parametrize(
    ("health_result", "expected_runtime_status"),
    [
        (AdapterHealth(available=True), RuntimeStatus.AVAILABLE),
        (AdapterHealth(available=False), RuntimeStatus.UNAVAILABLE),
        (RuntimeError("private local error"), RuntimeStatus.OBSERVATION_FAILED),
    ],
)
def test_projects_one_local_health_observation(
    health_result: AdapterHealth | Exception,
    expected_runtime_status: RuntimeStatus,
) -> None:
    adapter = LocalAdapter(health_result)
    transport = RecordingRemoteStatusTransport({})

    result = collect(adapter, [], transport)

    assert result.nodes == (
        ClusterStatusNode(
            node_id="local",
            application_status=ApplicationStatus.LOCAL,
            runtime_status=expected_runtime_status,
        ),
    )
    assert adapter.health_calls == 1
    assert adapter.chat_calls == 0


def test_collection_uses_only_the_provided_remote_status_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*_: object, **__: object) -> None:
        raise AssertionError("collection must not construct an HTTP client")

    monkeypatch.setattr(httpx, "AsyncClient", fail_if_called)
    declaration = make_remote_declaration("remote-status")
    transport = RecordingRemoteStatusTransport(
        {"remote-status": remote_status("remote-status")}
    )

    result = collect(
        LocalAdapter(AdapterHealth(available=True)), [declaration], transport
    )

    assert result.nodes[-1].node_id == "remote-status"
    assert transport.calls == ["remote-status"]


def test_serialized_collection_result_excludes_private_declaration_details() -> None:
    declaration = make_remote_declaration("private-remote")
    transport = RecordingRemoteStatusTransport(
        {
            "private-remote": remote_status(
                "private-remote",
                ApplicationStatus.UNREACHABLE,
                RuntimeStatus.UNKNOWN,
            )
        }
    )

    result = collect(
        LocalAdapter(RuntimeError("private local exception secret")),
        [declaration],
        transport,
    )
    serialized = result.model_dump_json()

    assert set(type(result).model_fields) == {"declaration_status", "nodes"}
    assert set(ClusterStatusNode.model_fields) == {
        "node_id",
        "application_status",
        "runtime_status",
    }
    for forbidden in (
        "private.example",
        "Private remote machine",
        "private-adapter",
        "private-local-machine",
        "Private local machine",
        "private-local-adapter",
        "private local exception",
        "secret",
        "transport_address",
        "reason",
    ):
        assert forbidden not in serialized
