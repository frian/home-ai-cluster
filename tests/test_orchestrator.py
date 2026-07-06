import asyncio
import inspect

import pytest

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.orchestrator import orchestrate_request
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.router import NoMatchingAdapterError


class RecordingAdapter:
    def __init__(
        self,
        name: str,
        capabilities: list[Capability],
        result: ClusterResult,
    ) -> None:
        self._name = name
        self._capabilities = capabilities
        self._result = result
        self.chat_requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return self._name

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return list(self._capabilities)

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        self.chat_requests.append(request)
        return self._result


def make_request(content: str = "Hello") -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content=content)],
        capability=Capability(name="chat"),
    )


def make_node(capabilities: list[Capability], adapters: list[str]) -> NodeDescription:
    return NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=capabilities,
        adapters=adapters,
    )


def test_orchestrate_request_returns_selected_adapter_result() -> None:
    result = ClusterResult(content="Hi", adapter="adapter", model="model")
    adapter = RecordingAdapter("adapter", [Capability(name="chat")], result)
    node_registry = NodeRegistry([make_node([Capability(name="chat")], ["adapter"])])
    adapter_registry = AdapterRegistry([adapter])

    actual = asyncio.run(
        orchestrate_request(make_request(), node_registry, adapter_registry)
    )

    assert actual is result


def test_orchestrate_request_passes_request_to_selected_adapter() -> None:
    result = ClusterResult(content="Hi", adapter="adapter")
    adapter = RecordingAdapter("adapter", [Capability(name="chat")], result)
    node_registry = NodeRegistry([make_node([Capability(name="chat")], ["adapter"])])
    adapter_registry = AdapterRegistry([adapter])
    request = make_request("Original prompt")

    asyncio.run(orchestrate_request(request, node_registry, adapter_registry))

    assert adapter.chat_requests == [request]


def test_orchestrate_request_remains_local_only_without_remote_execution_dependencies() -> None:
    result = ClusterResult(content="Hi from local", adapter="adapter")
    adapter = RecordingAdapter("adapter", [Capability(name="chat")], result)
    node_registry = NodeRegistry([make_node([Capability(name="chat")], ["adapter"])])
    adapter_registry = AdapterRegistry([adapter])
    request = make_request("Local-only prompt")

    actual = asyncio.run(orchestrate_request(request, node_registry, adapter_registry))

    signature = inspect.signature(orchestrate_request)
    assert list(signature.parameters) == [
        "request",
        "node_registry",
        "adapter_registry",
    ]
    assert actual is result
    assert adapter.chat_requests == [request]


def test_orchestrate_request_uses_first_matching_adapter() -> None:
    first = RecordingAdapter(
        "first",
        [Capability(name="chat")],
        ClusterResult(content="first", adapter="first"),
    )
    second = RecordingAdapter(
        "second",
        [Capability(name="chat")],
        ClusterResult(content="second", adapter="second"),
    )
    node_registry = NodeRegistry([make_node([Capability(name="chat")], ["first"])])
    adapter_registry = AdapterRegistry([first, second])

    result = asyncio.run(
        orchestrate_request(make_request(), node_registry, adapter_registry)
    )

    assert result.adapter == "first"
    assert len(first.chat_requests) == 1
    assert second.chat_requests == []


def test_orchestrate_request_propagates_no_matching_adapter_error() -> None:
    adapter = RecordingAdapter(
        "adapter",
        [Capability(name="summarization")],
        ClusterResult(content="", adapter="adapter"),
    )
    node_registry = NodeRegistry(
        [make_node([Capability(name="summarization")], ["adapter"])]
    )
    adapter_registry = AdapterRegistry([adapter])

    with pytest.raises(NoMatchingAdapterError):
        asyncio.run(
            orchestrate_request(make_request(), node_registry, adapter_registry)
        )

    assert adapter.chat_requests == []
