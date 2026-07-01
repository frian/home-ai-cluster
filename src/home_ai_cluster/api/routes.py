from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
)
from home_ai_cluster.core.orchestrator import orchestrate_request
from home_ai_cluster.core.registry import AdapterRegistry
from home_ai_cluster.core.router import NoMatchingAdapterError

router = APIRouter()


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    capability: str = Field(min_length=1)


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


@router.post("/v1/chat", response_model=ClusterResult)
async def chat(request: ChatRequest) -> ClusterResult:
    cluster_request = ClusterRequest(
        messages=request.messages,
        capability=Capability(name=request.capability),
    )
    registry = AdapterRegistry([InMemoryChatAdapter()])

    try:
        return await orchestrate_request(cluster_request, registry)
    except NoMatchingAdapterError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
