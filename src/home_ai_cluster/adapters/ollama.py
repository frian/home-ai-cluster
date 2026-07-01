"""Ollama runtime adapter."""

import httpx

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    ClusterResult,
)


class OllamaAdapter:
    """Minimal Ollama adapter for Phase 1 chat requests."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self._transport = transport

    @property
    def name(self) -> str:
        return "ollama"

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    def health(self) -> AdapterHealth:
        try:
            with httpx.Client(
                base_url=self.base_url,
                transport=self._transport,
            ) as client:
                response = client.get("/api/version")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return AdapterHealth(available=False, reason=str(exc))

        return AdapterHealth(available=True)

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        messages = [
            {"role": message.role, "content": message.content}
            for message in request.messages
        ]

        async with httpx.AsyncClient(
            base_url=self.base_url,
            transport=self._transport,
        ) as client:
            response = await client.post(
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                },
            )
            response.raise_for_status()

        body = response.json()
        content = body.get("message", {}).get("content", "")

        return ClusterResult(content=content, adapter=self.name, model=self.model)
