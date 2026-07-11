"""Runtime adapter interface for Home AI Cluster runtimes."""

from typing import Protocol

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    RuntimeResult,
)


class RuntimeAdapterUnavailableError(Exception):
    """Raised when a runtime adapter cannot complete a request."""


class RuntimeAdapter(Protocol):
    """Small boundary between the core and a specific AI runtime."""

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

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        """Execute a normalized chat request."""
        ...
