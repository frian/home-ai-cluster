"""Runtime adapter interface for Home AI Cluster runtimes."""

from typing import Protocol, runtime_checkable

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClassifyRequest,
    ClusterRequest,
    RuntimeResult,
    SummarizeRequest,
)


class RuntimeAdapterUnavailableError(Exception):
    """Raised when a runtime adapter cannot complete a request."""


class RuntimeConnectionUnavailableBeforeRequestError(RuntimeAdapterUnavailableError):
    """Raised when a runtime connection cannot be established before sending."""


class RuntimeAdapter(Protocol):
    """Common boundary shared by every HAC runtime adapter."""

    @property
    def name(self) -> str:
        """Return the stable internal adapter name."""
        ...

    def health(self) -> AdapterHealth:
        """Return basic adapter availability."""
        ...

    def capabilities(self) -> list[Capability]:
        """Return capabilities currently provided by the adapter."""
        ...


@runtime_checkable
class ChatExecutionAdapter(Protocol):
    """Explicit adapter contract for Chat-shaped execution."""

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        """Execute a normalized chat request."""
        ...


@runtime_checkable
class SummarizeExecutionAdapter(Protocol):
    """Explicit adapter contract for text summarization execution."""

    async def summarize(self, request: SummarizeRequest) -> RuntimeResult:
        """Execute a normalized text summarization request."""
        ...


@runtime_checkable
class ClassifyExecutionAdapter(Protocol):
    """Explicit adapter contract for bounded classification execution."""

    async def classify(self, request: ClassifyRequest) -> str:
        """Propose one label for a normalized bounded classification request."""
        ...
