"""vLLM runtime adapter transport proof."""

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


class VllmAdapter:
    """Minimal adapter for one explicitly configured vLLM instance."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self._transport = transport

    @property
    def name(self) -> str:
        return "vllm"

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
                trust_env=False,
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

        return await self._post_chat_completion({"messages": messages})

    async def summarize(self, request: SummarizeRequest) -> RuntimeResult:
        """Map bounded source text to vLLM's chat transport."""
        return await self._post_chat_completion(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Summarize the following source text concisely.\n\n"
                            f"<source>\n{request.text}\n</source>"
                        ),
                    }
                ]
            }
        )

    async def classify(self, request: ClassifyRequest) -> str:
        """Propose one label through vLLM's private structured output form."""
        result = await self._post_chat_completion(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Choose the single best matching label for the source "
                            "text.\n\n"
                            f"Source text:\n{request.text}"
                        ),
                    }
                ],
                "structured_outputs": {"choice": list(request.labels)},
            }
        )

        return result.content

    async def _post_chat_completion(self, payload: dict[str, object]) -> RuntimeResult:
        payload = {
            "model": self.model,
            **payload,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                transport=self._transport,
                timeout=None,
                trust_env=False,
            ) as client:
                response = await client.post(
                    "/v1/chat/completions",
                    json=payload,
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

    def _normalize_response(self, body: Any) -> tuple[str, str]:
        content = body["choices"][0]["message"]["content"]
        model = body.get("model", self.model)

        if not isinstance(content, str) or not isinstance(model, str):
            raise ValueError("vLLM response has invalid content or model")

        return content, model
