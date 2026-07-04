"""Static in-memory registries for the current Phase 2 prototype."""

from collections.abc import Iterable

from home_ai_cluster.adapters.base import RuntimeAdapter
from home_ai_cluster.core.models import Capability, NodeDescription
from home_ai_cluster.core.node import node_supports_capability


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

    def adapter_named(self, name: str) -> RuntimeAdapter | None:
        """Return the first registered adapter with the requested name."""
        for adapter in self._adapters:
            if adapter.name == name:
                return adapter

        return None


class NodeRegistry:
    """In-memory registry for static node descriptions."""

    def __init__(self, nodes: Iterable[NodeDescription] | None = None) -> None:
        self._nodes: list[NodeDescription] = list(nodes or ())

    def list_nodes(self) -> list[NodeDescription]:
        """Return known nodes in registration order."""
        return list(self._nodes)

    def nodes_for(self, capability: Capability) -> list[NodeDescription]:
        """Return available nodes that provide the requested capability."""
        return [
            node
            for node in self._nodes
            if node_supports_capability(node, capability)
        ]
