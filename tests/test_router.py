import pytest

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
)
from home_ai_cluster.core.registry import AdapterRegistry
from home_ai_cluster.core.router import (
    NoMatchingAdapterError,
    RoutingDecision,
    route_request,
)


class StubAdapter:
    def __init__(self, name: str, capabilities: list[Capability]) -> None:
        self._name = name
        self._capabilities = capabilities
        self.chat_was_called = False

    @property
    def name(self) -> str:
        return self._name

    def health(self) -> AdapterHealth:
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


def test_route_request_selects_first_adapter_with_requested_capability() -> None:
    chat = Capability(name="chat")
    first = StubAdapter("first", [Capability(name="code")])
    second = StubAdapter("second", [chat])
    third = StubAdapter("third", [chat])
    registry = AdapterRegistry([first, second, third])

    decision = route_request(make_request(chat), registry)

    assert decision == RoutingDecision(adapter=second, capability=chat)


def test_route_request_uses_registry_order_for_matches() -> None:
    chat = Capability(name="chat")
    first = StubAdapter("first", [chat])
    second = StubAdapter("second", [chat])
    registry = AdapterRegistry([first, second])

    decision = route_request(make_request(chat), registry)

    assert decision.adapter is first


def test_route_request_returns_requested_capability() -> None:
    code = Capability(name="code")
    adapter = StubAdapter("adapter", [code])
    registry = AdapterRegistry([adapter])

    decision = route_request(make_request(code), registry)

    assert decision.capability == code


def test_route_request_does_not_call_adapter_chat() -> None:
    chat = Capability(name="chat")
    adapter = StubAdapter("adapter", [chat])
    registry = AdapterRegistry([adapter])

    route_request(make_request(chat), registry)

    assert adapter.chat_was_called is False


def test_route_request_fails_when_no_adapter_matches() -> None:
    registry = AdapterRegistry(
        [StubAdapter("adapter", [Capability(name="summarization")])]
    )

    with pytest.raises(NoMatchingAdapterError, match="chat"):
        route_request(make_request(Capability(name="chat")), registry)
