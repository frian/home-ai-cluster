from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.api.wiring import (
    create_phase1_adapter_registry,
    create_phase1_node_registry,
)
from home_ai_cluster.core.models import Capability, NodeDescription


def test_create_phase1_adapter_registry_registers_ollama_adapter() -> None:
    registry = create_phase1_adapter_registry()

    adapters = registry.list_adapters()

    assert len(adapters) == 1
    assert isinstance(adapters[0], OllamaAdapter)
    assert adapters[0].name == "ollama"
    assert registry.adapters_for(Capability(name="chat")) == adapters


def test_create_phase1_node_registry_registers_static_local_node() -> None:
    registry = create_phase1_node_registry()

    nodes = registry.list_nodes()

    assert len(nodes) == 1
    assert nodes[0].model_dump() == {
        "id": "local",
        "name": "Local node",
        "availability": "available",
        "health": {"healthy": True, "reason": None},
        "capabilities": [{"name": "chat"}],
        "adapters": ["ollama"],
    }
    assert "models" not in NodeDescription.model_fields
