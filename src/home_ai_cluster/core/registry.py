"""Static registries for Phase 1 orchestration."""

from collections.abc import Iterable

from home_ai_cluster.adapters.base import RuntimeAdapter
from home_ai_cluster.core.models import Capability


class AdapterRegistry:
    """In-memory registry for already-created runtime adapters."""

    def __init__(self, adapters: Iterable[RuntimeAdapter] | None = None) -> None:
        self._adapters: list[RuntimeAdapter] = []

        for adapter in adapters or ():
            self.register(adapter)

    def register(self, adapter: RuntimeAdapter) -> None:
        """Register an adapter instance."""
        self._adapters.append(adapter)

    def list_adapters(self) -> list[RuntimeAdapter]:
        """Return registered adapters in registration order."""
        return list(self._adapters)

    def adapters_for(self, capability: Capability) -> list[RuntimeAdapter]:
        """Return registered adapters that provide the requested capability."""
        return [
            adapter
            for adapter in self._adapters
            if capability in adapter.capabilities()
        ]
