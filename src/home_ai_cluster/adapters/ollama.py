"""Ollama runtime adapter."""

import httpx

from home_ai_cluster.adapters.base import (
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    RuntimeResult,
)


class OllamaAdapter:
    """Minimal Ollama runtime adapter for local chat requests."""

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

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        messages = [
            {"role": message.role, "content": message.content}
            for message in request.messages
        ]

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                transport=self._transport,
                timeout=None,
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
        except httpx.ConnectError as exc:
            raise RuntimeConnectionUnavailableBeforeRequestError(
                "Runtime connection unavailable before request transmission",
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeAdapterUnavailableError(
                "Runtime adapter unavailable",
            ) from exc

        body = response.json()
        content = body.get("message", {}).get("content", "")

        return RuntimeResult(
            content=content,
            adapter=self.name,
            model=self.model,
        )
