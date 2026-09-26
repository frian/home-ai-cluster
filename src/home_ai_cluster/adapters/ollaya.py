"""Private native Ollaya classification adapter."""

from collections.abc import Mapping

import httpx

from home_ai_cluster.adapters.base import (
    InvalidClassificationResultError,
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.core.models import AdapterHealth, Capability, ClassifyRequest
from home_ai_cluster.local_http import local_http_url

_QUESTION_ID = "classification"


class OllayaAdapter:
    """One explicitly supplied operator-managed local Ollaya origin."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = local_http_url(base_url)
        self.model = model
        self._transport = transport

    @property
    def name(self) -> str:
        return "ollaya"

    def capabilities(self) -> list[Capability]:
        return [Capability(name="classify")]

    def health(self) -> AdapterHealth:
        try:
            with httpx.Client(
                base_url=self.base_url,
                transport=self._transport,
                trust_env=False,
            ) as client:
                response = client.get("/api/version")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return AdapterHealth(available=False, reason=str(exc))
        return AdapterHealth(available=True)

    async def classify(self, request: ClassifyRequest) -> str:
        """Map one normalized Classify request to the native choice API."""
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                transport=self._transport,
                timeout=None,
                trust_env=False,
            ) as client:
                response = await client.post(
                    "/api/decide",
                    json={
                        "model": self.model,
                        "state": request.text,
                        "questions": {
                            _QUESTION_ID: {
                                "type": "choice",
                                "criteria": list(request.labels),
                            }
                        },
                    },
                )
                response.raise_for_status()
        except httpx.ConnectError as exc:
            raise RuntimeConnectionUnavailableBeforeRequestError(
                "Runtime connection unavailable before request transmission"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeAdapterUnavailableError("Runtime adapter unavailable") from exc

        try:
            answers = response.json()["answers"]
            if not isinstance(answers, Mapping):
                raise ValueError("Ollaya answers must be an object")
            answer = answers[_QUESTION_ID]
            if not isinstance(answer, Mapping):
                raise ValueError("Ollaya answer must be an object")
            choice = answer["choice"]
            if not isinstance(choice, str):
                raise ValueError("Ollaya choice must be a string")
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidClassificationResultError(
                "Invalid classification result"
            ) from exc

        return choice
