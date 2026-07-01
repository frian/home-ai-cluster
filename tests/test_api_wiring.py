from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.api.wiring import create_phase1_registry
from home_ai_cluster.core.models import Capability


def test_create_phase1_registry_registers_ollama_adapter() -> None:
    registry = create_phase1_registry()

    adapters = registry.list_adapters()

    assert len(adapters) == 1
    assert isinstance(adapters[0], OllamaAdapter)
    assert adapters[0].name == "ollama"
    assert registry.adapters_for(Capability(name="chat")) == adapters
