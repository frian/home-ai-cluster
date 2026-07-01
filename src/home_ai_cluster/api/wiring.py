"""Temporary Phase 1 API wiring."""

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    ClusterResult,
)
from home_ai_cluster.core.registry import AdapterRegistry


class InMemoryChatAdapter:
    @property
    def name(self) -> str:
        return "in-memory"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        user_messages = [
            message.content
            for message in request.messages
            if message.role == "user"
        ]
        content = user_messages[-1] if user_messages else request.messages[-1].content

        return ClusterResult(content=content, adapter=self.name)


def create_phase1_registry() -> AdapterRegistry:
    """Create the temporary single-adapter registry for Phase 1."""
    return AdapterRegistry([InMemoryChatAdapter()])
