"""Temporary Phase 1 API wiring."""

from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry


def create_phase1_node_registry() -> NodeRegistry:
    """Create the temporary single-node registry for Phase 1."""
    local_node = NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["ollama"],
    )

    return NodeRegistry([local_node])


def create_phase1_adapter_registry() -> AdapterRegistry:
    """Create the temporary single-adapter registry for Phase 1."""
    return AdapterRegistry([OllamaAdapter()])
