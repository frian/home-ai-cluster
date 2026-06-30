from home_ai_cluster.adapters.base import RuntimeAdapter
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
)


class InMemoryAdapter:
    @property
    def name(self) -> str:
        return "in-memory"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        return ClusterResult(
            content=request.messages[-1].content,
            adapter=self.name,
            model="test-model",
        )


async def _send_chat(adapter: RuntimeAdapter) -> ClusterResult:
    request = ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
    )

    return await adapter.chat(request)


def test_runtime_adapter_protocol_accepts_minimal_adapter() -> None:
    adapter: RuntimeAdapter = InMemoryAdapter()

    assert adapter.name == "in-memory"
    assert adapter.health() == AdapterHealth(available=True)
    assert adapter.capabilities() == [Capability(name="chat")]


def test_runtime_adapter_chat_returns_normalized_result() -> None:
    adapter = InMemoryAdapter()

    import asyncio

    result = asyncio.run(_send_chat(adapter))

    assert result == ClusterResult(
        content="Hello",
        adapter="in-memory",
        model="test-model",
    )
