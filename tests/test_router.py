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
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.router import (
    NoMatchingAdapterError,
    RoutingDecision,
    route_request,
)

EXPECTED_ROUTING_REASON = (
    "Selected first available node with requested capability and matching adapter."
)


class StubAdapter:
    def __init__(self, name: str, capabilities: list[Capability]) -> None:
        self._name = name
        self._capabilities = capabilities
        self.chat_was_called = False
        self.health_was_called = False

    @property
    def name(self) -> str:
        return self._name

    def health(self) -> AdapterHealth:
        self.health_was_called = True
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return list(self._capabilities)

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        self.chat_was_called = True
        return ClusterResult(content="", adapter=self.name)


def make_request(capability: Capability) -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=capability,
    )


def make_node(
    node_id: str,
    capabilities: list[Capability],
    adapters: list[str],
    availability: str = "available",
    healthy: bool | None = None,
) -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability=availability,  # type: ignore[arg-type]
        health=NodeHealth(
            healthy=availability == "available" if healthy is None else healthy
        ),
        capabilities=capabilities,
        adapters=adapters,
    )


def test_route_request_selects_first_available_node_and_adapter() -> None:
    chat = Capability(name="chat")
    first = StubAdapter("first", [Capability(name="code")])
    second = StubAdapter("second", [chat])
    third = StubAdapter("third", [chat])
    node = make_node("local", [chat], ["second", "third"])
    node_registry = NodeRegistry([node])
    adapter_registry = AdapterRegistry([first, second, third])

    decision = route_request(make_request(chat), node_registry, adapter_registry)

    assert decision == RoutingDecision(
        node=node,
        adapter=second,
        capability=chat,
        reason=EXPECTED_ROUTING_REASON,
    )


def test_route_request_selects_available_static_node_with_requested_capability() -> None:
    chat = Capability(name="chat")
    adapter = StubAdapter("adapter", [chat])
    node = make_node("local", [chat], ["adapter"], availability="available")
    node_registry = NodeRegistry([node])
    adapter_registry = AdapterRegistry([adapter])

    decision = route_request(make_request(chat), node_registry, adapter_registry)

    assert decision.node is node
    assert decision.adapter is adapter
    assert decision.capability == chat


def test_route_request_ignores_unavailable_static_node() -> None:
    chat = Capability(name="chat")
    unavailable = StubAdapter("unavailable", [chat])
    available = StubAdapter("available", [chat])
    unavailable_node = make_node(
        "unavailable",
        [chat],
        ["unavailable"],
        availability="unavailable",
    )
    available_node = make_node("available", [chat], ["available"])
    node_registry = NodeRegistry([unavailable_node, available_node])
    adapter_registry = AdapterRegistry([unavailable, available])

    decision = route_request(make_request(chat), node_registry, adapter_registry)

    assert decision.node is available_node
    assert decision.adapter is available


def test_route_request_fails_when_only_unavailable_static_node_matches() -> None:
    chat = Capability(name="chat")
    node_registry = NodeRegistry(
        [
            make_node(
                "local",
                [chat],
                ["adapter"],
                availability="unavailable",
            )
        ]
    )
    adapter_registry = AdapterRegistry([StubAdapter("adapter", [chat])])

    with pytest.raises(
        NoMatchingAdapterError,
        match="No available node provides capability: chat",
    ):
        route_request(make_request(chat), node_registry, adapter_registry)


def test_route_request_explanation_preserves_availability_boundary() -> None:
    chat = Capability(name="chat")
    adapter = StubAdapter("adapter", [chat])
    unavailable_node = make_node(
        "unavailable",
        [chat],
        ["adapter"],
        availability="unavailable",
    )
    available_node = make_node("available", [chat], ["adapter"])
    node_registry = NodeRegistry([unavailable_node, available_node])
    adapter_registry = AdapterRegistry([adapter])

    decision = route_request(make_request(chat), node_registry, adapter_registry)

    assert decision.node is available_node
    assert decision.reason == EXPECTED_ROUTING_REASON


def test_route_request_explains_successful_selection() -> None:
    chat = Capability(name="chat")
    adapter = StubAdapter("adapter", [chat])
    node = make_node("local", [chat], ["adapter"])
    node_registry = NodeRegistry([node])
    adapter_registry = AdapterRegistry([adapter])

    decision = route_request(make_request(chat), node_registry, adapter_registry)

    assert decision.reason == EXPECTED_ROUTING_REASON


def test_route_request_explanation_stays_runtime_neutral() -> None:
    chat = Capability(name="chat")
    adapter = StubAdapter("ollama", [chat])
    node = make_node("local", [chat], ["ollama"])
    node_registry = NodeRegistry([node])
    adapter_registry = AdapterRegistry([adapter])

    decision = route_request(make_request(chat), node_registry, adapter_registry)

    assert decision.reason == EXPECTED_ROUTING_REASON
    assert "ollama" not in decision.reason
    assert "model" not in decision.reason
    assert "http" not in decision.reason


def test_route_request_uses_node_adapter_order_for_matches() -> None:
    chat = Capability(name="chat")
    first = StubAdapter("first", [chat])
    second = StubAdapter("second", [chat])
    node = make_node("local", [chat], ["second", "first"])
    node_registry = NodeRegistry([node])
    adapter_registry = AdapterRegistry([first, second])

    decision = route_request(make_request(chat), node_registry, adapter_registry)

    assert decision.adapter is second


def test_route_request_only_considers_adapters_declared_by_selected_node() -> None:
    chat = Capability(name="chat")
    undeclared = StubAdapter("undeclared", [chat])
    declared = StubAdapter("declared", [chat])
    node = make_node("local", [chat], ["declared"])
    node_registry = NodeRegistry([node])
    adapter_registry = AdapterRegistry([undeclared, declared])

    decision = route_request(make_request(chat), node_registry, adapter_registry)

    assert decision.node is node
    assert decision.adapter is declared


def test_route_request_does_not_select_undeclared_registry_adapter() -> None:
    chat = Capability(name="chat")
    undeclared = StubAdapter("undeclared", [chat])
    node = make_node("local", [chat], ["missing"])
    node_registry = NodeRegistry([node])
    adapter_registry = AdapterRegistry([undeclared])

    with pytest.raises(
        NoMatchingAdapterError,
        match="No adapter provides capability on available node: chat",
    ):
        route_request(make_request(chat), node_registry, adapter_registry)


def test_route_request_uses_node_registry_order_for_matches() -> None:
    chat = Capability(name="chat")
    first = StubAdapter("first", [chat])
    second = StubAdapter("second", [chat])
    first_node = make_node("first", [chat], ["first"])
    second_node = make_node("second", [chat], ["second"])
    node_registry = NodeRegistry([first_node, second_node])
    adapter_registry = AdapterRegistry([first, second])

    decision = route_request(make_request(chat), node_registry, adapter_registry)

    assert decision.node is first_node
    assert decision.adapter is first


def test_route_request_does_not_filter_by_node_health() -> None:
    chat = Capability(name="chat")
    adapter = StubAdapter("adapter", [chat])
    node = make_node("local", [chat], ["adapter"], healthy=False)
    node_registry = NodeRegistry([node])
    adapter_registry = AdapterRegistry([adapter])

    decision = route_request(make_request(chat), node_registry, adapter_registry)

    assert decision.node is node
    assert decision.adapter is adapter


def test_route_request_does_not_preflight_adapter_health() -> None:
    chat = Capability(name="chat")
    adapter = StubAdapter("adapter", [chat])
    node = make_node("local", [chat], ["adapter"])
    node_registry = NodeRegistry([node])
    adapter_registry = AdapterRegistry([adapter])

    route_request(make_request(chat), node_registry, adapter_registry)

    assert adapter.health_was_called is False


def test_route_request_returns_requested_capability() -> None:
    code = Capability(name="code")
    adapter = StubAdapter("adapter", [code])
    node = make_node("local", [code], ["adapter"])
    node_registry = NodeRegistry([node])
    adapter_registry = AdapterRegistry([adapter])

    decision = route_request(make_request(code), node_registry, adapter_registry)

    assert decision.capability == code


def test_route_request_does_not_call_adapter_chat() -> None:
    chat = Capability(name="chat")
    adapter = StubAdapter("adapter", [chat])
    node = make_node("local", [chat], ["adapter"])
    node_registry = NodeRegistry([node])
    adapter_registry = AdapterRegistry([adapter])

    route_request(make_request(chat), node_registry, adapter_registry)

    assert adapter.chat_was_called is False


def test_route_request_fails_when_no_available_node_matches() -> None:
    node_registry = NodeRegistry(
        [
            make_node(
                "local",
                [Capability(name="summarization")],
                ["adapter"],
            )
        ]
    )
    adapter_registry = AdapterRegistry(
        [StubAdapter("adapter", [Capability(name="summarization")])]
    )

    with pytest.raises(NoMatchingAdapterError, match="chat"):
        route_request(
            make_request(Capability(name="chat")),
            node_registry,
            adapter_registry,
        )


def test_route_request_fails_when_node_adapter_is_missing() -> None:
    chat = Capability(name="chat")
    node_registry = NodeRegistry([make_node("local", [chat], ["missing"])])
    adapter_registry = AdapterRegistry([StubAdapter("adapter", [chat])])

    with pytest.raises(
        NoMatchingAdapterError,
        match="No adapter provides capability on available node: chat",
    ):
        route_request(make_request(chat), node_registry, adapter_registry)


def test_route_request_fails_when_declared_adapter_lacks_requested_capability() -> None:
    chat = Capability(name="chat")
    node_registry = NodeRegistry([make_node("local", [chat], ["adapter"])])
    adapter_registry = AdapterRegistry(
        [StubAdapter("adapter", [Capability(name="code")])]
    )

    with pytest.raises(
        NoMatchingAdapterError,
        match="No adapter provides capability on available node: chat",
    ):
        route_request(make_request(chat), node_registry, adapter_registry)
