"""Temporary Phase 1 API wiring."""

from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry


def create_static_local_node_announcement() -> NodeDescription:
    """Create the explicit static local node announcement for Phase 2."""
    return NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["ollama"],
    )


def create_phase1_node_registry() -> NodeRegistry:
    """Create the temporary single-node registry for Phase 1."""
    return NodeRegistry([create_static_local_node_announcement()])


def create_phase1_adapter_registry() -> AdapterRegistry:
    """Create the temporary single-adapter registry for Phase 1."""
    return AdapterRegistry([OllamaAdapter()])
