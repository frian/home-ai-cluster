"""Temporary Phase 1 API wiring."""

from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.core.registry import AdapterRegistry


def create_phase1_registry() -> AdapterRegistry:
    """Create the temporary single-adapter registry for Phase 1."""
    return AdapterRegistry([OllamaAdapter()])
