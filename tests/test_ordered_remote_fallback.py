import asyncio

import pytest

from home_ai_cluster.adapters.base import (
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
    RequestConstraints,
    RuntimeResult,
)
from home_ai_cluster.core.ordered_remote_fallback import (
    orchestrate_request_with_ordered_static_remote_fallback,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)


class RecordingAdapter:
    def __init__(self, outcome: RuntimeResult | Exception) -> None:
        self.outcome = outcome
        self.requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return "recording"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.requests.append(request)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class ScriptedRemoteTransport:
    def __init__(self, outcomes: dict[str, ClusterResult | Exception]) -> None:
        self.outcomes = outcomes
        self.attempted_node_ids: list[str] = []

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        node_id = declaration.node.id
        self.attempted_node_ids.append(node_id)
        outcome = self.outcomes[node_id]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make_request(*, local_only: bool = False) -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
        constraints=RequestConstraints(local_only=local_only),
    )


def make_node(node_id: str, adapter_name: str) -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=[adapter_name],
    )


def make_declaration(node_id: str) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node(node_id, "remote-adapter"),
        transport_address=f"http://{node_id}.local:8000",
    )


def run_fallback(
    *,
    request: ClusterRequest,
    adapter: RecordingAdapter | None,
    transport: ScriptedRemoteTransport,
    declarations: list[RemoteNodeDeclaration],
) -> ClusterResult:
    node_registry = (
        NodeRegistry([make_node("local", "recording")])
        if adapter is not None
        else NodeRegistry()
    )
    adapter_registry = (
        AdapterRegistry([adapter]) if adapter is not None else AdapterRegistry()
    )
    return asyncio.run(
        orchestrate_request_with_ordered_static_remote_fallback(
            request,
            node_registry,
            adapter_registry,
            RemoteNodeDeclarationRegistry(declarations),
            transport,
        )
    )


def test_local_success_stops_before_remote_candidates() -> None:
    adapter = RecordingAdapter(RuntimeResult(content="local", adapter="recording"))
    transport = ScriptedRemoteTransport(
        {"remote-a": ClusterResult(content="a", adapter="remote", node_id="a")}
    )

    result = run_fallback(
        request=make_request(),
        adapter=adapter,
        transport=transport,
        declarations=[make_declaration("remote-a")],
    )

    assert result.content == "local"
    assert len(adapter.requests) == 1
    assert transport.attempted_node_ids == []


def test_advances_through_connection_unavailable_candidates_in_order() -> None:
    unavailable = RuntimeConnectionUnavailableBeforeRequestError("unavailable")
    adapter = RecordingAdapter(unavailable)
    transport = ScriptedRemoteTransport(
        {
            "remote-a": RuntimeConnectionUnavailableBeforeRequestError("a down"),
            "remote-b": ClusterResult(
                content="remote-b",
                adapter="remote",
                node_id="remote-b",
            ),
        }
    )

    result = run_fallback(
        request=make_request(),
        adapter=adapter,
        transport=transport,
        declarations=[make_declaration("remote-a"), make_declaration("remote-b")],
    )

    assert result.content == "remote-b"
    assert transport.attempted_node_ids == ["remote-a", "remote-b"]


def test_remote_only_path_attempts_each_candidate_at_most_once() -> None:
    transport = ScriptedRemoteTransport(
        {
            "remote-a": RuntimeConnectionUnavailableBeforeRequestError("a down"),
            "remote-b": ClusterResult(
                content="remote-b",
                adapter="remote",
                node_id="remote-b",
            ),
        }
    )

    result = run_fallback(
        request=make_request(),
        adapter=None,
        transport=transport,
        declarations=[make_declaration("remote-a"), make_declaration("remote-b")],
    )

    assert result.node_id == "remote-b"
    assert transport.attempted_node_ids == ["remote-a", "remote-b"]


def test_non_connection_failure_stops_without_advancing() -> None:
    transport = ScriptedRemoteTransport(
        {
            "remote-a": ValueError("request failed"),
            "remote-b": ClusterResult(
                content="remote-b",
                adapter="remote",
                node_id="remote-b",
            ),
        }
    )

    with pytest.raises(ValueError, match="request failed"):
        run_fallback(
            request=make_request(),
            adapter=None,
            transport=transport,
            declarations=[make_declaration("remote-a"), make_declaration("remote-b")],
        )

    assert transport.attempted_node_ids == ["remote-a"]


def test_local_only_request_never_attempts_declared_remotes() -> None:
    adapter = RecordingAdapter(
        RuntimeConnectionUnavailableBeforeRequestError("local down")
    )
    transport = ScriptedRemoteTransport(
        {"remote-a": ClusterResult(content="a", adapter="remote", node_id="a")}
    )

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError):
        run_fallback(
            request=make_request(local_only=True),
            adapter=adapter,
            transport=transport,
            declarations=[make_declaration("remote-a")],
        )

    assert transport.attempted_node_ids == []
