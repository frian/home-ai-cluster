from home_ai_cluster.adapters.base import RuntimeAdapter
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    ClusterResult,
)
from home_ai_cluster.core.registry import AdapterRegistry


class StubAdapter:
    def __init__(self, name: str, capabilities: list[Capability]) -> None:
        self._name = name
        self._capabilities = capabilities

    @property
    def name(self) -> str:
        return self._name

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return list(self._capabilities)

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        return ClusterResult(content="", adapter=self.name)


def test_registry_starts_empty() -> None:
    registry = AdapterRegistry()

    assert registry.list_adapters() == []
    assert registry.adapters_for(Capability(name="chat")) == []


def test_registry_lists_registered_adapters_in_order() -> None:
    first = StubAdapter("first", [Capability(name="chat")])
    second = StubAdapter("second", [Capability(name="code")])
    registry = AdapterRegistry()

    registry.register(first)
    registry.register(second)

    assert registry.list_adapters() == [first, second]


def test_registry_accepts_initial_adapters_in_order() -> None:
    first = StubAdapter("first", [Capability(name="chat")])
    second = StubAdapter("second", [Capability(name="code")])

    registry = AdapterRegistry([first, second])

    assert registry.list_adapters() == [first, second]


def test_list_adapters_returns_copy() -> None:
    adapter = StubAdapter("adapter", [Capability(name="chat")])
    registry = AdapterRegistry([adapter])

    listed = registry.list_adapters()
    listed.clear()

    assert registry.list_adapters() == [adapter]


def test_registry_filters_adapters_by_capability_in_order() -> None:
    chat = Capability(name="chat")
    code = Capability(name="code")
    first = StubAdapter("first", [chat])
    second = StubAdapter("second", [code])
    third = StubAdapter("third", [chat, code])
    registry = AdapterRegistry([first, second, third])

    assert registry.adapters_for(chat) == [first, third]
    assert registry.adapters_for(code) == [second, third]


def test_stub_adapter_satisfies_runtime_adapter_protocol() -> None:
    adapter: RuntimeAdapter = StubAdapter("adapter", [Capability(name="chat")])

    assert adapter.name == "adapter"
