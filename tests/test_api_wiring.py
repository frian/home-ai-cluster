from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.api.wiring import (
    create_static_local_node_announcement,
    create_static_local_node_registry,
    create_static_runtime_adapter_registry,
)
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth


def test_create_static_runtime_adapter_registry_contains_ollama_adapter() -> None:
    registry = create_static_runtime_adapter_registry()

    adapters = registry.list_adapters()

    assert len(adapters) == 1
    assert isinstance(adapters[0], OllamaAdapter)
    assert adapters[0].name == "ollama"
    assert registry.adapters_for(Capability(name="chat")) == adapters


def test_create_static_local_node_announcement_returns_explicit_declaration() -> None:
    announcement = create_static_local_node_announcement()

    assert announcement.id == "local"
    assert announcement.name == "Local node"
    assert announcement.availability == "available"
    assert announcement.health == NodeHealth(healthy=True)
    assert announcement.capabilities == [Capability(name="chat")]
    assert announcement.adapters == ["ollama"]
    assert "models" not in NodeDescription.model_fields


def test_create_static_local_node_registry_contains_static_local_node() -> None:
    registry = create_static_local_node_registry()
    announcement = create_static_local_node_announcement()

    nodes = registry.list_nodes()

    assert len(nodes) == 1
    assert nodes[0] == announcement
    assert nodes[0].model_dump() == {
        "id": "local",
        "name": "Local node",
        "availability": "available",
        "health": {"healthy": True, "reason": None},
        "capabilities": [{"name": "chat"}],
        "adapters": ["ollama"],
    }
    assert "models" not in NodeDescription.model_fields
