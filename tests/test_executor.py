import asyncio

import pytest

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.core.executor import (
    execute_declared_routing_decision,
    execute_local_routing_decision,
    execute_remote_routing_decision,
    execute_routing_decision,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.remote_transport import RemoteTransportError
from home_ai_cluster.core.router import RoutingDecision


class RecordingAdapter:
    def __init__(
        self,
        result: ClusterResult | None = None,
        error: RuntimeAdapterUnavailableError | None = None,
    ) -> None:
        self._result = result or ClusterResult(content="result", adapter="adapter")
        self._error = error
        self.chat_requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return "adapter"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        self.chat_requests.append(request)

        if self._error is not None:
            raise self._error

        return self._result


class FakeRemoteTransport:
    def __init__(
        self,
        result: ClusterResult | None = None,
        error: RemoteTransportError | None = None,
    ) -> None:
        self._result = result or ClusterResult(
            content="remote result",
            adapter="remote-adapter",
        )
        self._error = error
        self.requests: list[ClusterRequest] = []
        self.declarations: list[RemoteNodeDeclaration] = []

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        self.requests.append(request)
        self.declarations.append(declaration)

        if self._error is not None:
            raise self._error

        return self._result


def make_request() -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
    )


def make_node(node_id: str = "local") -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["adapter"],
    )


def make_decision(adapter: RecordingAdapter) -> RoutingDecision:
    return RoutingDecision(
        node=make_node(),
        adapter=adapter,
        capability=Capability(name="chat"),
        reason="test decision",
    )


def make_declaration(node_id: str = "local") -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node(node_id),
        transport_address=f"http://{node_id}.local:8000",
    )


def test_execute_local_routing_decision_passes_exact_request_to_selected_adapter() -> None:
    adapter = RecordingAdapter()
    request = make_request()

    asyncio.run(execute_local_routing_decision(request, make_decision(adapter)))

    assert adapter.chat_requests == [request]
    assert adapter.chat_requests[0] is request


def test_execute_local_routing_decision_returns_exact_adapter_result() -> None:
    result = ClusterResult(content="Hello", adapter="adapter")
    adapter = RecordingAdapter(result=result)

    actual = asyncio.run(
        execute_local_routing_decision(make_request(), make_decision(adapter))
    )

    assert actual is result


def test_execute_routing_decision_delegates_to_local_execution_path() -> None:
    adapter = RecordingAdapter()
    request = make_request()

    asyncio.run(execute_routing_decision(request, make_decision(adapter)))

    assert adapter.chat_requests == [request]
    assert adapter.chat_requests[0] is request


def test_execute_routing_decision_does_not_inspect_remote_declarations() -> None:
    adapter = RecordingAdapter()
    decision = make_decision(adapter)

    asyncio.run(execute_routing_decision(make_request(), decision))

    assert not hasattr(decision, "remote_declarations")
    assert not hasattr(decision, "remote_node_declarations")
    assert not hasattr(decision, "declaration_registry")


def test_execute_routing_decision_does_not_require_remote_transport() -> None:
    adapter = RecordingAdapter()
    request = make_request()

    result = asyncio.run(execute_routing_decision(request, make_decision(adapter)))

    assert result.adapter == "adapter"
    assert not hasattr(adapter, "send")


def test_execute_remote_routing_decision_passes_exact_request_to_transport() -> None:
    transport = FakeRemoteTransport()
    request = make_request()

    asyncio.run(
        execute_remote_routing_decision(
            request,
            make_decision(RecordingAdapter()),
            make_declaration(),
            transport,
        )
    )

    assert transport.requests == [request]
    assert transport.requests[0] is request


def test_execute_remote_routing_decision_passes_exact_declaration_to_transport() -> None:
    transport = FakeRemoteTransport()
    declaration = make_declaration()

    asyncio.run(
        execute_remote_routing_decision(
            make_request(),
            make_decision(RecordingAdapter()),
            declaration,
            transport,
        )
    )

    assert transport.declarations == [declaration]
    assert transport.declarations[0] is declaration


def test_execute_remote_routing_decision_returns_exact_transport_result() -> None:
    result = ClusterResult(content="Hello from remote", adapter="remote-adapter")
    transport = FakeRemoteTransport(result=result)

    actual = asyncio.run(
        execute_remote_routing_decision(
            make_request(),
            make_decision(RecordingAdapter()),
            make_declaration(),
            transport,
        )
    )

    assert actual is result


def test_execute_remote_routing_decision_propagates_transport_errors() -> None:
    error = RemoteTransportError("remote transport failed")
    transport = FakeRemoteTransport(error=error)

    with pytest.raises(RemoteTransportError) as raised:
        asyncio.run(
            execute_remote_routing_decision(
                make_request(),
                make_decision(RecordingAdapter()),
                make_declaration(),
                transport,
            )
        )

    assert raised.value is error


def test_execute_remote_routing_decision_does_not_call_selected_local_adapter() -> None:
    adapter = RecordingAdapter()
    transport = FakeRemoteTransport()

    asyncio.run(
        execute_remote_routing_decision(
            make_request(),
            make_decision(adapter),
            make_declaration(),
            transport,
        )
    )

    assert adapter.chat_requests == []


def test_execute_declared_routing_decision_uses_local_execution_without_matching_declaration() -> None:
    adapter = RecordingAdapter()
    transport = FakeRemoteTransport()
    request = make_request()
    registry = RemoteNodeDeclarationRegistry([make_declaration("other")])

    result = asyncio.run(
        execute_declared_routing_decision(
            request,
            make_decision(adapter),
            registry,
            transport,
        )
    )

    assert result.adapter == "adapter"
    assert adapter.chat_requests == [request]
    assert adapter.chat_requests[0] is request
    assert transport.requests == []


def test_execute_declared_routing_decision_uses_remote_transport_for_matching_declaration() -> None:
    adapter = RecordingAdapter()
    transport_result = ClusterResult(
        content="Hello from declared remote",
        adapter="remote-adapter",
    )
    transport = FakeRemoteTransport(result=transport_result)
    request = make_request()
    declaration = make_declaration("local")
    registry = RemoteNodeDeclarationRegistry([declaration])

    result = asyncio.run(
        execute_declared_routing_decision(
            request,
            make_decision(adapter),
            registry,
            transport,
        )
    )

    assert result is transport_result
    assert transport.requests == [request]
    assert transport.requests[0] is request
    assert transport.declarations == [declaration]
    assert transport.declarations[0] is declaration
    assert adapter.chat_requests == []


def test_execute_local_routing_decision_propagates_adapter_errors() -> None:
    error = RuntimeAdapterUnavailableError("adapter failed")
    adapter = RecordingAdapter(error=error)

    with pytest.raises(RuntimeAdapterUnavailableError) as raised:
        asyncio.run(
            execute_local_routing_decision(make_request(), make_decision(adapter))
        )

    assert raised.value is error


def test_execute_routing_decision_propagates_adapter_errors() -> None:
    error = RuntimeAdapterUnavailableError("adapter failed")
    adapter = RecordingAdapter(error=error)

    with pytest.raises(RuntimeAdapterUnavailableError) as raised:
        asyncio.run(execute_routing_decision(make_request(), make_decision(adapter)))

    assert raised.value is error
