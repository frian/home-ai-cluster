import argparse
from pathlib import Path

import pytest

from home_ai_cluster import local_runtime_composition
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.adapters.ollaya import OllayaAdapter
from home_ai_cluster.core.local_capability_binding import LocalCapabilityBindingError
from home_ai_cluster.core.models import Capability


def _config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "runtime.toml"
    path.write_text(content)
    return path


def _ollaya_binding(capabilities: str = '"classify"', extra: str = "") -> str:
    return (
        "[[bindings]]\n"
        f"capabilities = [{capabilities}]\n"
        'runtime = "ollaya"\n'
        'base_url = "http://127.0.0.1:11435/"\n'
        'model = "laya"\n'
        f"{extra}"
    )


def test_ollaya_multi_binding_constructs_exact_classify_adapter(tmp_path: Path) -> None:
    values = local_runtime_composition.load_local_runtime_config(
        _config(tmp_path, _ollaya_binding())
    )
    assert isinstance(
        values, local_runtime_composition.MultiBindingRuntimeCompositionValues
    )
    assert values.bindings[0].capabilities == ("classify",)
    assert values.bindings[0].base_url == "http://127.0.0.1:11435"
    assert values.bindings[0].model == "laya"

    composition = local_runtime_composition.create_multi_binding_local_app_composition(
        values
    )
    adapter = composition.adapter_registry.list_adapters()[0]
    assert isinstance(adapter, OllayaAdapter)
    assert adapter.base_url == "http://127.0.0.1:11435"
    assert adapter.model == "laya"
    assert (
        composition.adapter_registry.bound_adapter_for(Capability(name="classify"))
        is adapter
    )


@pytest.mark.parametrize(
    "content",
    [
        _ollaya_binding().replace('base_url = "http://127.0.0.1:11435/"\n', ""),
        _ollaya_binding().replace(
            'base_url = "http://127.0.0.1:11435/"', 'base_url = ""'
        ),
        _ollaya_binding().replace("http://127.0.0.1:11435/", "https://127.0.0.1:11435"),
        _ollaya_binding().replace(
            "http://127.0.0.1:11435/", "http://example.test:11435"
        ),
        _ollaya_binding().replace('model = "laya"\n', ""),
        _ollaya_binding().replace('model = "laya"', 'model = " "'),
        _ollaya_binding(extra="temperature = 0\n"),
        _ollaya_binding(extra="disable_thinking = true\n"),
        _ollaya_binding(extra="unknown = true\n"),
    ],
)
def test_ollaya_binding_rejects_invalid_closed_shape(
    tmp_path: Path, content: str
) -> None:
    with pytest.raises(local_runtime_composition.LocalRuntimeCompositionError):
        local_runtime_composition.load_local_runtime_config(_config(tmp_path, content))


@pytest.mark.parametrize(
    "capability", ["chat", "summarize", "code", "image-generation"]
)
def test_ollaya_binding_rejects_unsupported_capability(
    tmp_path: Path, capability: str
) -> None:
    values = local_runtime_composition.load_local_runtime_config(
        _config(tmp_path, _ollaya_binding(f'"{capability}"'))
    )
    with pytest.raises(LocalCapabilityBindingError, match="unsupported capability"):
        local_runtime_composition.create_multi_binding_local_app_composition(values)


def test_ollaya_mixes_with_disjoint_textual_binding(tmp_path: Path) -> None:
    values = local_runtime_composition.load_local_runtime_config(
        _config(
            tmp_path,
            '[[bindings]]\ncapabilities = ["chat"]\nruntime = "ollama"\n\n'
            + _ollaya_binding(),
        )
    )
    composition = local_runtime_composition.create_multi_binding_local_app_composition(
        values
    )
    chat, classify = composition.adapter_registry.list_adapters()
    assert isinstance(chat, OllamaAdapter)
    assert isinstance(classify, OllayaAdapter)
    assert (
        composition.adapter_registry.bound_adapter_for(Capability(name="chat")) is chat
    )
    assert (
        composition.adapter_registry.bound_adapter_for(Capability(name="classify"))
        is classify
    )


def test_ollaya_preserves_binding_disjointness(tmp_path: Path) -> None:
    content = _ollaya_binding() + (
        '\n[[bindings]]\ncapabilities = ["classify"]\nruntime = "ollama"\n'
    )
    with pytest.raises(local_runtime_composition.LocalRuntimeCompositionError):
        local_runtime_composition.load_local_runtime_config(_config(tmp_path, content))


def test_ollaya_remains_invalid_for_single_runtime_forms(tmp_path: Path) -> None:
    with pytest.raises(local_runtime_composition.LocalRuntimeCompositionError):
        local_runtime_composition.load_local_runtime_config(
            _config(tmp_path, 'runtime = "ollaya"\n')
        )
    parser = argparse.ArgumentParser()
    local_runtime_composition.add_local_runtime_arguments(parser)
    with pytest.raises(SystemExit):
        parser.parse_args(["--runtime", "ollaya"])


@pytest.mark.parametrize("ollaya_first", [False, True])
def test_ollaya_binding_order_does_not_change_capability_ownership(
    tmp_path: Path, ollaya_first: bool
) -> None:
    textual = '[[bindings]]\ncapabilities = ["chat"]\nruntime = "ollama"\n'
    content = (
        _ollaya_binding() + "\n" + textual
        if ollaya_first
        else textual + "\n" + _ollaya_binding()
    )
    values = local_runtime_composition.load_local_runtime_config(
        _config(tmp_path, content)
    )
    composition = local_runtime_composition.create_multi_binding_local_app_composition(
        values
    )

    assert isinstance(
        composition.adapter_registry.bound_adapter_for(Capability(name="chat")),
        OllamaAdapter,
    )
    assert isinstance(
        composition.adapter_registry.bound_adapter_for(Capability(name="classify")),
        OllayaAdapter,
    )
