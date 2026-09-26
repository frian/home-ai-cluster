import asyncio
from pathlib import Path

import httpx
import pytest

from home_ai_cluster import local_runtime
from home_ai_cluster.adapters.ollama import OllamaAdapter
from home_ai_cluster.adapters.ollaya import OllayaAdapter
from home_ai_cluster.commands import config_command
from home_ai_cluster.core.models import Capability
from home_ai_cluster.local_runtime_composition import LocalRuntimeCompositionValues
from home_ai_cluster.main import create_app
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedLocalConfiguration,
    load_retained_configuration,
    save_retained_configuration,
)
from home_ai_cluster.web.loopback_browser import add_loopback_browser_routes


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local-app-data"))


def runtime_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "runtime.toml"
    path.write_text(content, encoding="utf-8")
    return path


def bindings() -> str:
    return """[[bindings]]
capabilities = ["chat", "summarize", "code"]
runtime = "ollama"
model = "text-model"

[[bindings]]
capabilities = ["classify"]
runtime = "ollaya"
base_url = "http://127.0.0.1:11435/"
model = "classify-model"
"""


def test_config_local_retains_semantic_multi_binding_facts_not_source_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = runtime_config(tmp_path, bindings())
    config_command.main(["local", "--runtime-config", str(path)])
    assert capsys.readouterr().out == "local configuration retained\n"

    retained = load_retained_configuration().local
    assert retained is not None
    assert "runtime_config" not in str(retained)
    assert retained.local_capabilities is None
    assert retained.execution_limit is None

    config_command.main(["show"])
    shown = capsys.readouterr().out
    assert "runtime composition: multi-binding" in shown
    assert "runtime: ollaya" in shown
    assert "model: classify-model" in shown

    path.unlink()
    app = local_runtime.create_local_runtime_app(local_runtime.parse_args([]))
    registry = app.state.local_app_composition.adapter_registry
    chat = registry.bound_adapter_for(Capability(name="chat"))
    classify = registry.bound_adapter_for(Capability(name="classify"))
    assert isinstance(chat, OllamaAdapter)
    assert isinstance(classify, OllayaAdapter)
    assert (classify.base_url, classify.model) == (
        "http://127.0.0.1:11435",
        "classify-model",
    )


def test_multi_binding_mutation_preserves_independent_local_facts(
    tmp_path: Path,
) -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                LocalRuntimeCompositionValues(runtime="ollama"),
                local_capabilities=("chat",),
                execution_limit=2,
            )
        )
    )
    config_command.main(
        ["local", "--runtime-config", str(runtime_config(tmp_path, bindings()))]
    )
    local = load_retained_configuration().local
    assert local is not None
    assert local.local_capabilities == ("chat",)
    assert local.execution_limit == 2


def test_retained_multi_binding_rejects_image_generation_without_mutation(
    tmp_path: Path,
) -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                LocalRuntimeCompositionValues(runtime="ollama", ollama_model="old")
            )
        )
    )
    path = runtime_config(
        tmp_path,
        """[[bindings]]
capabilities = ["image-generation"]
runtime = "stable-diffusion-cpp"
base_url = "http://127.0.0.1:7860"
""",
    )
    with pytest.raises(SystemExit):
        config_command.main(["local", "--runtime-config", str(path)])
    local = load_retained_configuration().local
    assert local is not None
    assert isinstance(local.runtime, LocalRuntimeCompositionValues)
    assert local.runtime.ollama_model == "old"


def test_legacy_flags_cannot_patch_retained_multi_binding(tmp_path: Path) -> None:
    config_command.main(
        ["local", "--runtime-config", str(runtime_config(tmp_path, bindings()))]
    )
    with pytest.raises(SystemExit):
        local_runtime.parse_args(["--ollama-model", "temporary"])


def test_browser_retained_local_mutation_fails_closed_for_multi_binding(
    tmp_path: Path,
) -> None:
    config_command.main(
        ["local", "--runtime-config", str(runtime_config(tmp_path, bindings()))]
    )
    app = add_loopback_browser_routes(create_app())

    async def get() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://127.0.0.1:25042",
        ) as client:
            return await client.get("/retained-local-configuration")

    assert asyncio.run(get()).status_code == 400
