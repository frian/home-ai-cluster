"""Explicit in-memory ownership of local capabilities by adapter instances."""

from collections.abc import Iterable
from dataclasses import dataclass

from home_ai_cluster.adapters.base import RuntimeAdapter
from home_ai_cluster.core.models import Capability


class LocalCapabilityBindingError(ValueError):
    """Raised when one local capability binding composition is invalid."""


@dataclass(frozen=True)
class LocalCapabilityBinding:
    """Assign a non-empty capability set to one concrete adapter instance."""

    capabilities: frozenset[str]
    adapter: RuntimeAdapter

    def __post_init__(self) -> None:
        if not self.capabilities:
            raise LocalCapabilityBindingError(
                "Local capability binding requires at least one capability"
            )
        supported = {capability.name for capability in self.adapter.capabilities()}
        if not self.capabilities <= supported:
            raise LocalCapabilityBindingError(
                "Local capability binding assigns an unsupported capability"
            )


class LocalCapabilityBindings:
    """Validated local capability ownership for one composed process."""

    def __init__(self, bindings: Iterable[LocalCapabilityBinding]) -> None:
        self._bindings = tuple(bindings)
        claimed: set[str] = set()
        for binding in self._bindings:
            if claimed & binding.capabilities:
                raise LocalCapabilityBindingError(
                    "Local capability bindings must not overlap"
                )
            claimed.update(binding.capabilities)
        self._capability_names = frozenset(claimed)

    @property
    def capability_names(self) -> frozenset[str]:
        """Return exactly the capabilities owned by this composition."""
        return self._capability_names

    def adapter_for(self, capability: Capability) -> RuntimeAdapter | None:
        """Return the concrete adapter instance bound to one capability."""
        for binding in self._bindings:
            if capability.name in binding.capabilities:
                return binding.adapter
        return None
