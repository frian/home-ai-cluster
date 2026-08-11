"""Ollama runtime adapter."""

import json

import httpx

from home_ai_cluster.adapters.base import (
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClassifyRequest,
    ClusterRequest,
    RuntimeResult,
    SummarizeRequest,
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
        return [
            Capability(name="chat"),
            Capability(name="summarize"),
            Capability(name="classify"),
            Capability(name="code"),
        ]

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

    async def summarize(self, request: SummarizeRequest) -> RuntimeResult:
        """Map bounded source text to Ollama's existing chat transport."""
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
                        "messages": [
                            {
                                "role": "user",
                                "content": (
                                    "Summarize the following source text concisely.\n\n"
                                    f"<source>\n{request.text}\n</source>"
                                ),
                            }
                        ],
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

        content = response.json().get("message", {}).get("content", "")

        return RuntimeResult(
            content=content,
            adapter=self.name,
            model=self.model,
        )

    async def classify(self, request: ClassifyRequest) -> str:
        """Map bounded source text and labels to Ollama's chat transport."""
        prompt = (
            "Choose the single best matching label for the source text.\n\n"
            f"Source text:\n{request.text}"
        )

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
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "format": {
                            "type": "string",
                            "enum": list(request.labels),
                        },
                        "options": {"temperature": 0},
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

        try:
            content = response.json()["message"]["content"]
            proposal = json.loads(content)
            if not isinstance(proposal, str):
                raise ValueError("Ollama classification output must be a JSON string")
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeAdapterUnavailableError(
                "Runtime adapter unavailable",
            ) from exc

        return proposal
