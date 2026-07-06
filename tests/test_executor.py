import asyncio

import pytest

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.core.executor import execute_routing_decision
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
)
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


def make_request() -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
    )


def make_node() -> NodeDescription:
    return NodeDescription(
        id="local",
        name="Local node",
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


def test_execute_routing_decision_passes_exact_request_to_selected_adapter() -> None:
    adapter = RecordingAdapter()
    request = make_request()

    asyncio.run(execute_routing_decision(request, make_decision(adapter)))

    assert adapter.chat_requests == [request]
    assert adapter.chat_requests[0] is request


def test_execute_routing_decision_returns_exact_adapter_result() -> None:
    result = ClusterResult(content="Hello", adapter="adapter")
    adapter = RecordingAdapter(result=result)

    actual = asyncio.run(
        execute_routing_decision(make_request(), make_decision(adapter))
    )

    assert actual is result


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


def test_execute_routing_decision_propagates_adapter_errors() -> None:
    error = RuntimeAdapterUnavailableError("adapter failed")
    adapter = RecordingAdapter(error=error)

    with pytest.raises(RuntimeAdapterUnavailableError) as raised:
        asyncio.run(execute_routing_decision(make_request(), make_decision(adapter)))

    assert raised.value is error
