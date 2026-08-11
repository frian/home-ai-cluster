"""llama.cpp server runtime adapter."""

import json
from typing import Any

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


class LlamaServerAdapter:
    """Minimal adapter for one explicitly configured llama-server instance."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:8080",
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self._transport = transport

    @property
    def name(self) -> str:
        return "llama-server"

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
                response = client.get("/health")
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
                    "/v1/chat/completions",
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

        try:
            content, model = self._normalize_response(response.json())
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeAdapterUnavailableError(
                "Runtime adapter unavailable",
            ) from exc

        return RuntimeResult(content=content, adapter=self.name, model=model)

    async def summarize(self, request: SummarizeRequest) -> RuntimeResult:
        """Map bounded source text to llama-server's chat transport."""
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                transport=self._transport,
                timeout=None,
            ) as client:
                response = await client.post(
                    "/v1/chat/completions",
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

        try:
            content, model = self._normalize_response(response.json())
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeAdapterUnavailableError(
                "Runtime adapter unavailable",
            ) from exc

        return RuntimeResult(content=content, adapter=self.name, model=model)

    async def classify(self, request: ClassifyRequest) -> str:
        """Map bounded source text and labels to llama-server's chat transport."""
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
                    "/v1/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "response_format": {
                            "type": "json_object",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                        "enum": list(request.labels),
                                    }
                                },
                                "required": ["label"],
                                "additionalProperties": False,
                            },
                        },
                        "temperature": 0,
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
            return self._classification_content(response.json())
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeAdapterUnavailableError(
                "Runtime adapter unavailable",
            ) from exc

    def _normalize_response(self, body: Any) -> tuple[str, str]:
        content = body["choices"][0]["message"]["content"]
        model = body.get("model", self.model)

        if not isinstance(content, str) or not isinstance(model, str):
            raise ValueError("llama-server response has invalid content or model")

        return content, model

    def _classification_content(self, body: Any) -> str:
        """Extract one JSON-structured classification proposal from llama-server."""
        content = body["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("llama-server response has invalid classification content")
        proposal = json.loads(content)
        if not isinstance(proposal, dict) or set(proposal) != {"label"}:
            raise ValueError("llama-server response has invalid classification shape")
        label = proposal["label"]
        if not isinstance(label, str):
            raise ValueError("llama-server response has invalid classification label")
        return label
