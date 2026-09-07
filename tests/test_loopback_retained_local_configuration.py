import asyncio
from dataclasses import make_dataclass
from pathlib import Path

import httpx
import pytest

from home_ai_cluster.local_runtime_composition import LocalRuntimeCompositionValues
from home_ai_cluster.main import create_app, create_receiver_app
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedLocalConfiguration,
    browser_retained_local_shape_is_supported,
    load_retained_configuration,
    save_retained_configuration,
)
from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration
from home_ai_cluster.web.loopback_browser import add_loopback_browser_routes


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))


def local_document(**overrides: object) -> dict[str, object]:
    document: dict[str, object] = {
        "runtime": "ollama",
        "ollama_model": None,
        "ollama_disable_thinking": False,
        "llama_server_base_url": None,
        "llama_server_model": None,
        "vllm_base_url": None,
        "vllm_model": None,
        "local_capabilities": None,
        "execution_limit": None,
    }
    document.update(overrides)
    return document


def request(
    app,
    method: str,
    path: str,
    *,
    port: int = 25042,
    headers: dict[str, str] | None = None,
    json: object | None = None,
) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url=f"http://127.0.0.1:{port}",
        ) as client:
            return await client.request(method, path, headers=headers, json=json)

    return asyncio.run(send())


def native_app(*, port: int = 25042, composition: object | None = None):
    return add_loopback_browser_routes(
        create_app(local_app_composition=composition), native_port=port
    )


def native_mutation_headers(port: int = 25042) -> dict[str, str]:
    return {"Origin": f"http://127.0.0.1:{port}"}


def test_read_represents_absent_retained_local_configuration_without_runtime() -> None:
    response = request(native_app(), "GET", "/retained-local-configuration")

    assert response.status_code == 200
    assert response.json() == {"local": None}


def test_read_preserves_retained_none_and_excludes_other_domains() -> None:
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(
                    runtime="ollama",
                    ollama_model=None,
                    ollama_disable_thinking=False,
                    llama_server_base_url=None,
                    llama_server_model=None,
                    vllm_base_url=None,
                    vllm_model=None,
                ),
                local_capabilities=None,
                execution_limit=None,
            ),
            remote_nodes=(
                RemoteNodeDeclaration(
                    node_id="remote", base_url="http://192.0.2.10:25042"
                ),
            ),
            external_information_plugin="tavily",
            chat_external_information_fallback=True,
        )
    )

    response = request(native_app(), "GET", "/retained-local-configuration")

    assert response.status_code == 200
    assert response.json() == {"local": local_document()}


def test_complete_mutation_preserves_other_retained_domains_and_composition() -> None:
    save_retained_configuration(
        RetainedConfiguration(
            remote_nodes=(
                RemoteNodeDeclaration(
                    node_id="remote", base_url="http://192.0.2.10:25042"
                ),
            ),
            external_information_plugin="tavily",
            chat_external_information_fallback=True,
        )
    )
    composition = object()
    app = native_app(composition=composition)
    document = local_document(local_capabilities=["chat"], execution_limit=1)

    response = request(
        app,
        "PUT",
        "/retained-local-configuration",
        headers=native_mutation_headers(),
        json=document,
    )

    assert response.status_code == 200
    assert response.json() == {"local": document}
    retained = load_retained_configuration()
    assert retained.local is not None
    assert retained.local.local_capabilities == ("chat",)
    assert retained.local.execution_limit == 1
    assert retained.remote_nodes[0].node_id == "remote"
    assert retained.external_information_plugin == "tavily"
    assert retained.chat_external_information_fallback is True
    assert app.state.local_app_composition is composition


def test_invalid_mutation_does_not_change_retained_configuration() -> None:
    original = local_document(ollama_model="retained")
    valid = request(
        native_app(),
        "PUT",
        "/retained-local-configuration",
        headers=native_mutation_headers(),
        json=original,
    )
    assert valid.status_code == 200

    response = request(
        native_app(),
        "PUT",
        "/retained-local-configuration",
        headers=native_mutation_headers(),
        json=local_document(runtime="llama-server"),
    )

    assert response.status_code == 400
    assert request(native_app(), "GET", "/retained-local-configuration").json() == {
        "local": original
    }


@pytest.mark.parametrize(
    ("headers", "port"),
    [
        ({}, 25042),
        ({"Origin": "null"}, 25042),
        ({"Origin": "http://foreign.example"}, 25042),
        ({"Host": "foreign.example", "Origin": "http://foreign.example"}, 25042),
        ({"Origin": "http://127.0.0.1:25042"}, 25043),
    ],
)
def test_mutation_refuses_unaccepted_authority_before_persistence(
    headers: dict[str, str], port: int
) -> None:
    response = request(
        native_app(port=port),
        "PUT",
        "/retained-local-configuration",
        port=port,
        headers=headers,
        json=local_document(),
    )

    assert response.status_code in {400, 403}
    assert load_retained_configuration().local is None


def test_nondefault_effective_native_port_allows_exact_same_origin_mutation() -> None:
    port = 25123
    response = request(
        native_app(port=port),
        "PUT",
        "/retained-local-configuration",
        port=port,
        headers=native_mutation_headers(port),
        json=local_document(execution_limit=1),
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_browser_compatibility_guard_rejects_future_local_shape() -> None:
    FutureLocalConfiguration = make_dataclass(
        "FutureLocalConfiguration",
        [
            ("runtime", object),
            ("local_capabilities", object),
            ("execution_limit", object),
            ("future", object),
        ],
        frozen=True,
    )

    assert not browser_retained_local_shape_is_supported(
        FutureLocalConfiguration(None, None, None, "unsupported")
    )


def test_receiver_does_not_expose_or_mutate_retained_local_configuration() -> None:
    receiver = create_receiver_app(local_app_composition=object())

    response = request(receiver, "GET", "/retained-local-configuration")
    mutation = request(
        receiver,
        "PUT",
        "/retained-local-configuration",
        headers=native_mutation_headers(),
        json=local_document(),
    )

    assert response.status_code == 404
    assert mutation.status_code == 404
    assert load_retained_configuration().local is None
