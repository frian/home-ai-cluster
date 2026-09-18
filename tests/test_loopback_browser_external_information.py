import asyncio
from pathlib import Path

import httpx
import pytest

from home_ai_cluster.commands import external_information_command
from home_ai_cluster.core.models import SourceGroundedChatResult
from home_ai_cluster.main import create_app, create_receiver_app
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    save_retained_configuration,
)
from home_ai_cluster.web.loopback_browser import add_loopback_browser_routes
from home_ai_cluster.web.trusted_lan_browser import create_trusted_lan_browser_app


class EntryPoints:
    def __init__(self, entries: list[object]) -> None:
        self.entries = entries
        self.groups: list[str] = []

    def select(self, *, group: str) -> list[object]:
        self.groups.append(group)
        return self.entries


class EntryPoint:
    def __init__(self, name: str, acquisition: object) -> None:
        self.name = name
        self.acquisition = acquisition
        self.loads = 0

    def load(self) -> object:
        self.loads += 1
        return self.acquisition


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local-app-data"))


def native_app():
    return add_loopback_browser_routes(create_app())


def request(
    app, *, headers: dict[str, str] | None = None, json: object
) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://127.0.0.1:25042",
        ) as client:
            return await client.post(
                "/external-information", headers=headers, json=json
            )

    return asyncio.run(send())


def headers() -> dict[str, str]:
    return {"Origin": "http://127.0.0.1:25042"}


def document(
    *,
    plugin: str = "",
    query: str = "acquisition query",
    question: str = "source question",
) -> dict[str, str]:
    return {"plugin": plugin, "query": query, "question": question}


def candidate() -> dict[str, str]:
    return {
        "title": "Supplied title",
        "url": "https://example.test/source",
        "content": "Supplied source content",
    }


def test_operation_uses_exact_override_once_without_retained_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: list[str] = []

    async def acquire(query: str) -> list[dict[str, str]]:
        received.append(query)
        return [candidate()]

    entry = EntryPoint("override", acquire)
    entry_points = EntryPoints([entry])
    monkeypatch.setattr(
        external_information_command.importlib.metadata,
        "entry_points",
        lambda: entry_points,
    )
    monkeypatch.setattr(
        "home_ai_cluster.web.loopback_browser.load_retained_configuration",
        lambda: (_ for _ in ()).throw(AssertionError("must not load retained state")),
    )

    async def route(request, *_):
        assert request.question == "source question"
        assert [source.model_dump() for source in request.sources] == [candidate()]
        return SourceGroundedChatResult(
            content="generated content",
            sources=request.sources,
            node_id="local",
            adapter="test",
        )

    monkeypatch.setattr(
        "home_ai_cluster.web.loopback_browser.handle_chat_cluster_request", route
    )
    response = request(
        native_app(), headers=headers(), json=document(plugin="override")
    )

    assert response.status_code == 200
    assert response.json()["content"] == "generated content"
    assert entry_points.groups == [external_information_command._ENTRY_POINT_GROUP]
    assert entry.loads == 1
    assert received == ["acquisition query"]


def test_blank_override_uses_retained_plugin_and_invalid_input_never_discovers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    save_retained_configuration(
        RetainedConfiguration(external_information_plugin="retained")
    )
    discovered = False

    def entry_points() -> object:
        nonlocal discovered
        discovered = True
        raise AssertionError("invalid input must not discover plugins")

    monkeypatch.setattr(
        external_information_command.importlib.metadata, "entry_points", entry_points
    )
    response = request(native_app(), headers=headers(), json=document(query=" "))

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid External Information request"
    assert not discovered


def test_malformed_acquisition_output_never_reaches_routing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def acquire(_: str) -> list[dict[str, str]]:
        return [{"title": "missing closed fields"}]

    entry = EntryPoint("selected", acquire)
    monkeypatch.setattr(
        external_information_command.importlib.metadata,
        "entry_points",
        lambda: EntryPoints([entry]),
    )

    async def must_not_route(*_) -> object:
        raise AssertionError("must not route")

    monkeypatch.setattr(
        "home_ai_cluster.web.loopback_browser.handle_chat_cluster_request",
        must_not_route,
    )

    response = request(
        native_app(), headers=headers(), json=document(plugin="selected")
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "external-information-acquisition-failed"}
    assert entry.loads == 1


def test_missing_retained_selection_fails_before_plugin_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    discovered = False

    def entry_points() -> object:
        nonlocal discovered
        discovered = True
        raise AssertionError("missing selection must not discover plugins")

    monkeypatch.setattr(
        external_information_command.importlib.metadata, "entry_points", entry_points
    )
    response = request(native_app(), headers=headers(), json=document())

    assert response.status_code == 400
    assert not discovered


def test_authority_and_other_application_boundaries_do_not_expose_operation() -> None:
    app = native_app()
    assert request(app, json=document()).status_code == 403
    assert (
        request(
            app, headers={"Origin": "http://foreign.test"}, json=document()
        ).status_code
        == 403
    )

    owner = create_app()
    lan = create_trusted_lan_browser_app(owner, host="192.0.2.10", port=25042)

    async def post_path(app) -> int:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://192.0.2.10:25042",
        ) as client:
            return (
                await client.post("/external-information", json=document())
            ).status_code

    assert asyncio.run(post_path(lan)) == 404
    assert (
        asyncio.run(post_path(create_receiver_app(local_app_composition=object())))
        == 404
    )
