import asyncio

import pytest

from home_ai_cluster.adapters.base import (
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.core.execution_intervals import ExecutionIntervalCardinality
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
    SummarizeRequest,
)
from home_ai_cluster.core.orchestrator import ExecutionPermissionDeniedError
from home_ai_cluster.core.ordered_remote_fallback import (
    orchestrate_request_with_ordered_static_remote_fallback,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.remote_transport import (
    RemoteExecutionPermissionDeniedError,
    RemoteTransportError,
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


class RecordingSummarizeAdapter:
    def __init__(self) -> None:
        self.requests: list[SummarizeRequest] = []

    @property
    def name(self) -> str:
        return "summarize-local"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="summarize")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        raise AssertionError("summarize adapter must not receive chat")

    async def summarize(self, request: SummarizeRequest) -> RuntimeResult:
        self.requests.append(request)
        return RuntimeResult(content="local summary", adapter=self.name)


class ScriptedRemoteTransport:
    def __init__(self, outcomes: dict[str, ClusterResult | Exception]) -> None:
        self.outcomes = outcomes
        self.attempted_node_ids: list[str] = []
        self.requests: list[ClusterRequest | SummarizeRequest] = []

    async def send(
        self,
        request: ClusterRequest | SummarizeRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        node_id = declaration.node.id
        self.attempted_node_ids.append(node_id)
        self.requests.append(request)
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


def make_summarize_declaration(
    node_id: str, capability: str = "summarize"
) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id=node_id,
            name=f"{node_id} node",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name=capability)],
            adapters=["remote-adapter"],
        ),
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


def run_summarize_fallback(
    request: SummarizeRequest,
    transport: ScriptedRemoteTransport,
    declarations: list[RemoteNodeDeclaration],
) -> ClusterResult:
    return asyncio.run(
        orchestrate_request_with_ordered_static_remote_fallback(
            request,
            NodeRegistry(),
            AdapterRegistry(),
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


def test_concurrent_originating_request_continues_to_remote_when_local_denied() -> None:
    class BlockingLocalAdapter(RecordingAdapter):
        def __init__(self) -> None:
            super().__init__(RuntimeResult(content="local", adapter="recording"))
            self.started = asyncio.Event()
            self.release = asyncio.Event()

        async def chat(self, request: ClusterRequest) -> RuntimeResult:
            self.requests.append(request)
            self.started.set()
            await self.release.wait()
            return self.outcome  # type: ignore[return-value]

    async def run() -> None:
        adapter = BlockingLocalAdapter()
        transport = ScriptedRemoteTransport(
            {"remote-a": ClusterResult(content="remote", adapter="remote", node_id="x")}
        )
        intervals = ExecutionIntervalCardinality()
        nodes = NodeRegistry([make_node("local", "recording")])
        remotes = RemoteNodeDeclarationRegistry([make_declaration("remote-a")])
        first = asyncio.create_task(
            orchestrate_request_with_ordered_static_remote_fallback(
                make_request(),
                nodes,
                AdapterRegistry([adapter]),
                remotes,
                transport,
                intervals,
            )
        )
        await adapter.started.wait()
        assert intervals.value == 1
        second = await orchestrate_request_with_ordered_static_remote_fallback(
            make_request(),
            nodes,
            AdapterRegistry([adapter]),
            remotes,
            transport,
            intervals,
        )
        assert second.content == "remote"
        assert len(adapter.requests) == 1
        assert transport.attempted_node_ids == ["remote-a"]
        adapter.release.set()
        await first
        assert intervals.value == 0

    asyncio.run(run())


def test_local_permission_denial_does_not_mask_remote_failure() -> None:
    async def run() -> None:
        adapter = RecordingAdapter(RuntimeResult(content="unused", adapter="recording"))
        transport = ScriptedRemoteTransport(
            {"remote-a": RemoteTransportError("remote request failed")}
        )
        intervals = ExecutionIntervalCardinality()
        assert await intervals.try_enter()

        with pytest.raises(RemoteTransportError, match="remote request failed"):
            await orchestrate_request_with_ordered_static_remote_fallback(
                make_request(),
                NodeRegistry([make_node("local", "recording")]),
                AdapterRegistry([adapter]),
                RemoteNodeDeclarationRegistry([make_declaration("remote-a")]),
                transport,
                intervals,
            )

        assert adapter.requests == []
        assert transport.attempted_node_ids == ["remote-a"]
        assert intervals.value == 1
        await intervals.exit()
        assert intervals.value == 0

    asyncio.run(run())


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


def test_permission_refusal_advances_to_next_remote_in_declared_order() -> None:
    transport = ScriptedRemoteTransport(
        {
            "remote-a": RemoteExecutionPermissionDeniedError("denied"),
            "remote-b": ClusterResult(
                content="remote-b", adapter="remote", node_id="wrong"
            ),
        }
    )

    result = run_fallback(
        request=make_request(),
        adapter=None,
        transport=transport,
        declarations=[make_declaration("remote-a"), make_declaration("remote-b")],
    )

    assert transport.attempted_node_ids == ["remote-a", "remote-b"]
    assert result.node_id == "remote-b"


def test_two_permission_refusals_advance_to_third_remote_success() -> None:
    transport = ScriptedRemoteTransport(
        {
            "remote-a": RemoteExecutionPermissionDeniedError("denied"),
            "remote-b": RemoteExecutionPermissionDeniedError("denied"),
            "remote-c": ClusterResult(
                content="remote-c", adapter="remote", node_id="wrong"
            ),
        }
    )

    result = run_fallback(
        request=make_request(),
        adapter=None,
        transport=transport,
        declarations=[
            make_declaration("remote-a"),
            make_declaration("remote-b"),
            make_declaration("remote-c"),
        ],
    )

    assert transport.attempted_node_ids == ["remote-a", "remote-b", "remote-c"]
    assert transport.attempted_node_ids.count("remote-a") == 1
    assert transport.attempted_node_ids.count("remote-b") == 1
    assert transport.attempted_node_ids.count("remote-c") == 1
    assert result.content == "remote-c"
    assert result.node_id == "remote-c"


def test_permission_only_remote_exhaustion_has_permission_terminal_semantic() -> None:
    transport = ScriptedRemoteTransport(
        {
            "remote-a": RemoteExecutionPermissionDeniedError("denied"),
            "remote-b": RemoteExecutionPermissionDeniedError("denied"),
        }
    )

    with pytest.raises(ExecutionPermissionDeniedError):
        run_fallback(
            request=make_request(),
            adapter=None,
            transport=transport,
            declarations=[make_declaration("remote-a"), make_declaration("remote-b")],
        )

    assert transport.attempted_node_ids == ["remote-a", "remote-b"]


def test_three_permission_refusals_exhaust_with_permission_terminal_semantic() -> None:
    transport = ScriptedRemoteTransport(
        {
            "remote-a": RemoteExecutionPermissionDeniedError("denied"),
            "remote-b": RemoteExecutionPermissionDeniedError("denied"),
            "remote-c": RemoteExecutionPermissionDeniedError("denied"),
        }
    )

    with pytest.raises(ExecutionPermissionDeniedError) as raised:
        run_fallback(
            request=make_request(),
            adapter=None,
            transport=transport,
            declarations=[
                make_declaration("remote-a"),
                make_declaration("remote-b"),
                make_declaration("remote-c"),
            ],
        )

    assert raised.value.explanation is not None
    assert transport.attempted_node_ids == ["remote-a", "remote-b", "remote-c"]
    assert transport.attempted_node_ids.count("remote-a") == 1
    assert transport.attempted_node_ids.count("remote-b") == 1
    assert transport.attempted_node_ids.count("remote-c") == 1


def test_connection_unavailability_remains_authoritative_over_permission_refusal() -> (
    None
):
    unavailable = RuntimeConnectionUnavailableBeforeRequestError("unavailable")
    transport = ScriptedRemoteTransport(
        {
            "remote-a": unavailable,
            "remote-b": RemoteExecutionPermissionDeniedError("denied"),
        }
    )

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError) as raised:
        run_fallback(
            request=make_request(),
            adapter=None,
            transport=transport,
            declarations=[make_declaration("remote-a"), make_declaration("remote-b")],
        )

    assert raised.value is unavailable
    assert transport.attempted_node_ids == ["remote-a", "remote-b"]


def test_later_terminal_remote_failure_remains_authoritative() -> None:
    failure = RemoteTransportError("ambiguous failure")
    transport = ScriptedRemoteTransport(
        {
            "remote-a": RemoteExecutionPermissionDeniedError("denied"),
            "remote-b": failure,
        }
    )

    with pytest.raises(RemoteTransportError) as raised:
        run_fallback(
            request=make_request(),
            adapter=None,
            transport=transport,
            declarations=[make_declaration("remote-a"), make_declaration("remote-b")],
        )

    assert raised.value is failure
    assert transport.attempted_node_ids == ["remote-a", "remote-b"]


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


def test_summarize_falls_back_in_declared_order_with_caller_owned_attribution() -> None:
    request = SummarizeRequest(
        text="  Source text\n</source>  ",
        constraints=RequestConstraints(local_only=False),
    )
    transport = ScriptedRemoteTransport(
        {
            "remote-a": RuntimeConnectionUnavailableBeforeRequestError("unavailable"),
            "remote-b": ClusterResult(
                content="",
                adapter="remote-adapter",
                model="remote-model",
                node_id="malicious-receiver-id",
            ),
        }
    )

    result = run_summarize_fallback(
        request,
        transport,
        [
            make_summarize_declaration("remote-a"),
            make_summarize_declaration("remote-b"),
        ],
    )

    assert transport.attempted_node_ids == ["remote-a", "remote-b"]
    assert transport.requests == [request, request]
    assert result == ClusterResult(
        content="",
        adapter="remote-adapter",
        model="remote-model",
        node_id="remote-b",
    )
    assert result.node_id != "malicious-receiver-id"
    assert result.node_id != "http://remote-b.local:8000"


def test_summarize_prefers_eligible_local_adapter_over_declared_remote() -> None:
    request = SummarizeRequest(
        text="  Local source  ",
        constraints=RequestConstraints(local_only=False),
    )
    adapter = RecordingSummarizeAdapter()
    transport = ScriptedRemoteTransport(
        {"remote": ClusterResult(content="remote", adapter="remote", node_id="wrong")}
    )
    node = NodeDescription(
        id="selected-local",
        name="Selected local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="summarize")],
        adapters=[adapter.name],
    )

    result = asyncio.run(
        orchestrate_request_with_ordered_static_remote_fallback(
            request,
            NodeRegistry([node]),
            AdapterRegistry([adapter]),
            RemoteNodeDeclarationRegistry([make_summarize_declaration("remote")]),
            transport,
        )
    )

    assert adapter.requests == [request]
    assert transport.attempted_node_ids == []
    assert result.node_id == "selected-local"


def test_summarize_fallback_excludes_chat_only_declarations() -> None:
    request = SummarizeRequest(
        text="Source text",
        constraints=RequestConstraints(local_only=False),
    )
    transport = ScriptedRemoteTransport(
        {
            "remote-a": RuntimeConnectionUnavailableBeforeRequestError("unavailable"),
            "remote-b": ClusterResult(
                content="summary", adapter="remote", node_id="wrong"
            ),
        }
    )

    result = run_summarize_fallback(
        request,
        transport,
        [
            make_summarize_declaration("remote-a"),
            make_summarize_declaration("chat-only", "chat"),
            make_summarize_declaration("remote-b"),
        ],
    )

    assert result.node_id == "remote-b"
    assert transport.attempted_node_ids == ["remote-a", "remote-b"]


def test_summarize_does_not_fallback_after_remote_transport_failure() -> None:
    request = SummarizeRequest(
        text="private source",
        constraints=RequestConstraints(local_only=False),
    )
    transport = ScriptedRemoteTransport(
        {
            "remote-a": RemoteTransportError("private remote failure"),
            "remote-b": ClusterResult(
                content="summary", adapter="remote", node_id="wrong"
            ),
        }
    )

    with pytest.raises(RemoteTransportError) as raised:
        run_summarize_fallback(
            request,
            transport,
            [
                make_summarize_declaration("remote-a"),
                make_summarize_declaration("remote-b"),
            ],
        )

    assert transport.attempted_node_ids == ["remote-a"]
    assert "private source" not in str(raised.value)


def test_summarize_does_not_fallback_after_remote_runtime_unavailable() -> None:
    request = SummarizeRequest(
        text="private source",
        constraints=RequestConstraints(local_only=False),
    )
    transport = ScriptedRemoteTransport(
        {
            "remote-a": RuntimeAdapterUnavailableError("Runtime adapter unavailable"),
            "remote-b": ClusterResult(
                content="summary", adapter="remote", node_id="wrong"
            ),
        }
    )

    with pytest.raises(RuntimeAdapterUnavailableError):
        run_summarize_fallback(
            request,
            transport,
            [
                make_summarize_declaration("remote-a"),
                make_summarize_declaration("remote-b"),
            ],
        )

    assert transport.attempted_node_ids == ["remote-a"]
