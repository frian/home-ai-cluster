import asyncio
import json

import httpx
import pytest

from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.core.executor import execute_local_routing_decision
from home_ai_cluster.core.local_capability_binding import (
    LocalCapabilityBinding,
    LocalCapabilityBindingError,
    LocalCapabilityBindings,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.router import NoMatchingAdapterError, route_request


class RecordingAdapter:
    def __init__(self, capabilities: set[str]) -> None:
        self._capabilities = capabilities
        self.requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return "recording"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name=name) for name in self._capabilities]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.requests.append(request)
        return RuntimeResult(content=self.name, adapter=self.name)


def request(capability: str) -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name=capability),
    )


def composed_registries(
    bindings: list[LocalCapabilityBinding],
    adapters: list[object],
) -> tuple[NodeRegistry, AdapterRegistry]:
    ownership = LocalCapabilityBindings(bindings)
    node = NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[
            Capability(name=name) for name in sorted(ownership.capability_names)
        ],
        adapters=["unchanged-declaration"],
    )
    return NodeRegistry([node]), AdapterRegistry(
        adapters, local_capability_bindings=ownership
    )


def test_binding_requires_non_empty_supported_capabilities_before_execution() -> None:
    adapter = RecordingAdapter({"chat"})

    with pytest.raises(LocalCapabilityBindingError):
        LocalCapabilityBinding(capabilities=frozenset(), adapter=adapter)
    with pytest.raises(LocalCapabilityBindingError):
        LocalCapabilityBinding(capabilities=frozenset({"code"}), adapter=adapter)

    assert adapter.requests == []


def test_bindings_are_disjoint_and_exactly_define_execution_capabilities() -> None:
    chat = RecordingAdapter({"chat", "code"})
    code = RecordingAdapter({"code"})
    chat_binding = LocalCapabilityBinding(frozenset({"chat"}), chat)
    code_binding = LocalCapabilityBinding(frozenset({"code"}), code)

    ownership = LocalCapabilityBindings([chat_binding, code_binding])
    assert ownership.capability_names == frozenset({"chat", "code"})
    with pytest.raises(LocalCapabilityBindingError):
        LocalCapabilityBindings(
            [chat_binding, LocalCapabilityBinding(frozenset({"chat"}), chat)]
        )

    nodes, adapters = composed_registries([chat_binding, code_binding], [chat, code])
    with pytest.raises(NoMatchingAdapterError):
        route_request(request("summarize"), nodes, adapters)
    assert chat.requests == []
    assert code.requests == []


def test_multiple_capabilities_in_one_binding_reach_its_exact_adapter() -> None:
    adapter = RecordingAdapter({"chat", "code"})
    nodes, adapters = composed_registries(
        [LocalCapabilityBinding(frozenset({"chat", "code"}), adapter)], [adapter]
    )

    chat_decision = route_request(request("chat"), nodes, adapters)
    code_decision = route_request(request("code"), nodes, adapters)

    assert len(nodes.list_nodes()) == 1
    assert chat_decision.adapter is adapter
    assert code_decision.adapter is adapter
    asyncio.run(execute_local_routing_decision(request("chat"), chat_decision))
    asyncio.run(execute_local_routing_decision(request("code"), code_decision))
    assert [value.capability.name for value in adapter.requests] == ["chat", "code"]


def test_distinct_same_name_ollama_instances_receive_their_bound_capabilities() -> None:
    first_payloads: list[dict[str, object]] = []
    second_payloads: list[dict[str, object]] = []

    def transport_for(
        payloads: list[dict[str, object]], response: str
    ) -> httpx.MockTransport:
        def handler(http_request: httpx.Request) -> httpx.Response:
            payloads.append(json.loads(http_request.content))
            return httpx.Response(200, json={"message": {"content": response}})

        return httpx.MockTransport(handler)

    first = OllamaAdapter(
        model="first", transport=transport_for(first_payloads, "first result")
    )
    second = OllamaAdapter(
        model="second", transport=transport_for(second_payloads, "second result")
    )
    assert first is not second
    assert first.name == second.name == "ollama"

    first_binding = LocalCapabilityBinding(frozenset({"chat"}), first)
    second_binding = LocalCapabilityBinding(frozenset({"code"}), second)
    nodes, adapters = composed_registries(
        [second_binding, first_binding], [second, first]
    )

    chat = route_request(request("chat"), nodes, adapters)
    code = route_request(request("code"), nodes, adapters)
    assert chat.adapter is first
    assert code.adapter is second

    reversed_nodes, reversed_adapters = composed_registries(
        [first_binding, second_binding], [first, second]
    )
    assert (
        route_request(request("chat"), reversed_nodes, reversed_adapters).adapter
        is first
    )
    assert (
        route_request(request("code"), reversed_nodes, reversed_adapters).adapter
        is second
    )

    asyncio.run(execute_local_routing_decision(request("chat"), chat))
    asyncio.run(execute_local_routing_decision(request("code"), code))
    assert first_payloads[0]["model"] == "first"
    assert second_payloads[0]["model"] == "second"
