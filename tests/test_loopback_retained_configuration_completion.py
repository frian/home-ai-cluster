"""RFC-0132 loopback retained-configuration completion tests."""

import asyncio
from pathlib import Path

import httpx
import pytest

from home_ai_cluster.local_runtime_composition import create_local_runtime_composition
from home_ai_cluster.main import create_app, create_receiver_app
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedImageGenerationConfiguration,
    build_retained_local_configuration,
    load_retained_configuration,
    save_retained_configuration,
)
from home_ai_cluster.web.loopback_browser import add_loopback_browser_routes


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local-app-data"))


def request(
    app, method: str, path: str, *, headers: dict[str, str] | None = None, json=None
) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://127.0.0.1:25042",
        ) as client:
            return await client.request(method, path, headers=headers, json=json)

    return asyncio.run(send())


def native_app():
    return add_loopback_browser_routes(create_app())


def headers() -> dict[str, str]:
    return {
        "Origin": "http://127.0.0.1:25042",
        "Content-Type": "application/json",
    }


def test_completed_facades_read_absence_and_require_native_host() -> None:
    app = native_app()
    expectations = {
        "/retained-image-generation-configuration": {"image_generation": None},
        "/retained-external-information-configuration": {"plugin": None},
        "/retained-chat-external-information-configuration": {"authorized": False},
    }

    for path, expected in expectations.items():
        assert request(app, "GET", path).json() == expected
        assert (
            request(app, "GET", path, headers={"Host": "foreign.example"}).status_code
            == 400
        )


def test_completed_facades_mutate_only_their_owned_domains() -> None:
    app = native_app()
    image = request(
        app,
        "PUT",
        "/retained-image-generation-configuration",
        headers=headers(),
        json={"base_url": "http://127.0.0.1:7860"},
    )
    plugin = request(
        app,
        "PUT",
        "/retained-external-information-configuration",
        headers=headers(),
        json={"plugin": "searxng"},
    )
    chat = request(
        app,
        "PUT",
        "/retained-chat-external-information-configuration",
        headers=headers(),
        json={"authorized": True},
    )

    assert image.json() == {
        "image_generation": {
            "runtime": "stable-diffusion-cpp",
            "base_url": "http://127.0.0.1:7860",
        }
    }
    assert plugin.json() == {"plugin": "searxng"}
    assert chat.json() == {"authorized": True}
    retained = load_retained_configuration()
    assert retained.image_generation == RetainedImageGenerationConfiguration(
        base_url="http://127.0.0.1:7860"
    )
    assert retained.external_information_plugin == "searxng"
    assert retained.chat_external_information_fallback is True

    assert (
        request(
            app,
            "DELETE",
            "/retained-image-generation-configuration",
            headers=headers(),
        ).status_code
        == 200
    )
    retained = load_retained_configuration()
    assert retained.image_generation is None
    assert retained.external_information_plugin == "searxng"
    assert retained.chat_external_information_fallback is True


@pytest.mark.parametrize(
    ("path", "document"),
    [
        ("/retained-image-generation-configuration", {"base_url": "http://192.0.2.1"}),
        ("/retained-external-information-configuration", {"plugin": ""}),
        ("/retained-chat-external-information-configuration", {"authorized": "true"}),
    ],
)
def test_completed_facades_reject_invalid_documents_without_persistence(
    path: str, document: dict[str, object]
) -> None:
    response = request(native_app(), "PUT", path, headers=headers(), json=document)

    assert response.status_code == 400
    assert load_retained_configuration() == RetainedConfiguration()


@pytest.mark.parametrize(
    ("method", "path", "document"),
    [
        (
            "PUT",
            "/retained-image-generation-configuration",
            {"base_url": "http://127.0.0.1:7860"},
        ),
        ("PUT", "/retained-external-information-configuration", {"plugin": "searxng"}),
        (
            "PUT",
            "/retained-chat-external-information-configuration",
            {"authorized": True},
        ),
        ("DELETE", "/retained-local-configuration", None),
    ],
)
def test_new_mutations_require_native_host_and_same_origin(
    method: str, path: str, document: dict[str, object] | None
) -> None:
    assert request(native_app(), method, path, json=document).status_code == 403
    assert (
        request(
            native_app(),
            method,
            path,
            headers={"Origin": "http://foreign.example"},
            json=document,
        ).status_code
        == 403
    )
    assert (
        request(
            native_app(),
            method,
            path,
            headers={"Host": "foreign.example", **headers()},
            json=document,
        ).status_code
        == 400
    )


def test_local_reset_preserves_new_domains_and_receiver_has_no_completed_routes() -> (
    None
):
    save_retained_configuration(
        RetainedConfiguration(
            local=build_retained_local_configuration(
                runtime="ollama",
                ollama_model="retained-model",
                ollama_disable_thinking=False,
                llama_server_base_url=None,
                llama_server_model=None,
                vllm_base_url=None,
                vllm_model=None,
                local_capabilities=None,
                execution_limit=None,
            ),
            image_generation=RetainedImageGenerationConfiguration(
                base_url="http://127.0.0.1:7860"
            ),
            external_information_plugin="searxng",
            chat_external_information_fallback=True,
        )
    )
    assert (
        request(
            native_app(), "DELETE", "/retained-local-configuration", headers=headers()
        ).status_code
        == 200
    )
    retained = load_retained_configuration()
    assert retained.local is None
    assert retained.image_generation is not None
    assert retained.external_information_plugin == "searxng"
    assert retained.chat_external_information_fallback is True

    receiver = create_receiver_app(
        local_app_composition=create_local_runtime_composition(runtime="ollama")
    )
    for path in (
        "/retained-image-generation-configuration",
        "/retained-external-information-configuration",
        "/retained-chat-external-information-configuration",
        "/retained-local-configuration",
    ):
        assert request(receiver, "GET", path).status_code == 404


def test_image_generation_browser_shape_guard_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import home_ai_cluster.web.loopback_browser as loopback_browser

    monkeypatch.setattr(
        loopback_browser,
        "browser_retained_image_generation_shape_is_supported",
        lambda _: False,
    )

    response = request(
        native_app(),
        "PUT",
        "/retained-image-generation-configuration",
        headers=headers(),
        json={"base_url": "http://127.0.0.1:7860"},
    )

    assert response.status_code == 400
    assert load_retained_configuration().image_generation is None
