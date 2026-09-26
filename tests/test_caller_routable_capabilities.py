import asyncio
from importlib.resources import files

import httpx
import pytest

import home_ai_cluster.web.loopback_browser as loopback_browser
from home_ai_cluster.api.wiring import StaticRemoteWiring
from home_ai_cluster.core.caller_routable_capabilities import (
    project_caller_routable_capabilities,
)
from home_ai_cluster.core.local_capability_binding import (
    LocalCapabilityBinding,
    LocalCapabilityBindings,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.main import create_app, create_receiver_app
from home_ai_cluster.openai_compatibility import create_openai_compatibility_app
from home_ai_cluster.web.loopback_browser import add_loopback_browser_routes
from home_ai_cluster.web.trusted_lan_browser import create_trusted_lan_browser_app


class RecordingAdapter:
    def __init__(self, name: str, capability_names: set[str]) -> None:
        self._name = name
        self._capabilities = [Capability(name=name) for name in capability_names]
        self.health_calls = 0
        self.execution_calls = 0

    @property
    def name(self) -> str:
        return self._name

    def capabilities(self) -> list[Capability]:
        return list(self._capabilities)

    def health(self) -> AdapterHealth:
        self.health_calls += 1
        return AdapterHealth(available=True)

    async def chat(self, request: object) -> object:
        self.execution_calls += 1
        return object()


def node(
    capability_names: list[str],
    adapter_names: list[str],
    *,
    availability: str = "available",
) -> NodeDescription:
    return NodeDescription(
        id="local",
        name="Local node",
        availability=availability,  # type: ignore[arg-type]
        health=NodeHealth(healthy=False),
        capabilities=[Capability(name=name) for name in capability_names],
        adapters=adapter_names,
    )


def composition(
    nodes: list[NodeDescription], adapters: list[RecordingAdapter]
) -> object:
    return type(
        "Composition",
        (),
        {
            "node_registry": NodeRegistry(nodes),
            "adapter_registry": AdapterRegistry(adapters),
        },
    )()


def project(
    nodes: list[NodeDescription],
    adapters: list[RecordingAdapter],
    *,
    bindings: LocalCapabilityBindings | None = None,
    remotes: list[RemoteNodeDeclaration] | None = None,
) -> tuple[str, ...]:
    return project_caller_routable_capabilities(
        NodeRegistry(nodes),
        AdapterRegistry(adapters, local_capability_bindings=bindings),
        None if remotes is None else RemoteNodeDeclarationRegistry(remotes),
    )


def remote(capability_name: str) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id="remote",
            name="Remote node",
            availability="available",
            health=NodeHealth(healthy=False),
            capabilities=[Capability(name=capability_name)],
            adapters=["remote-adapter"],
        ),
        transport_address="http://192.0.2.9:8000",
    )


def test_projection_uses_existing_legacy_local_candidate_eligibility() -> None:
    adapter = RecordingAdapter("local", {"chat", "summarize"})

    assert project([node(["chat"], ["local"])], [adapter]) == ("chat",)


def test_projection_requires_binding_when_explicit_bindings_exist() -> None:
    adapter = RecordingAdapter("local", {"chat", "summarize"})
    bindings = LocalCapabilityBindings(
        [LocalCapabilityBinding(frozenset({"chat"}), adapter)]
    )

    assert project(
        [node(["chat", "summarize"], ["local"])], [adapter], bindings=bindings
    ) == ("chat",)


def test_projection_respects_active_node_registry_and_static_availability() -> None:
    adapter = RecordingAdapter("local", {"chat"})

    assert (
        project([node(["chat"], ["local"], availability="unavailable")], [adapter])
        == ()
    )
    assert project([], [adapter]) == ()


def test_projection_unions_declared_remote_without_transport_or_health_work() -> None:
    adapter = RecordingAdapter("local", {"chat"})

    assert project(
        [node(["chat"], ["local"])],
        [adapter],
        remotes=[remote("chat"), remote("code")],
    ) == ("chat", "code")
    assert adapter.health_calls == 0
    assert adapter.execution_calls == 0


def test_projection_supports_image_generation_without_special_case() -> None:
    adapter = RecordingAdapter("image", {"image-generation"})
    bindings = LocalCapabilityBindings(
        [LocalCapabilityBinding(frozenset({"image-generation"}), adapter)]
    )

    assert project(
        [node(["image-generation"], ["image"])], [adapter], bindings=bindings
    ) == ("image-generation",)


def native_get(app, path: str, *, host: str) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url=f"http://{host}",
        ) as client:
            return await client.get(path, headers={"host": host})

    return asyncio.run(send())


def test_loopback_endpoint_returns_only_capability_names_and_requires_native_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = RecordingAdapter("local", {"chat"})
    app = add_loopback_browser_routes(
        create_app(
            local_app_composition=composition([node(["chat"], ["local"])], [adapter])
        )
    )
    monkeypatch.setattr(
        loopback_browser,
        "load_retained_configuration",
        lambda: (_ for _ in ()).throw(AssertionError("must not load retained state")),
    )

    response = native_get(app, "/caller-routable-capabilities", host="127.0.0.1:8123")

    assert response.status_code == 200
    assert response.json() == {"capabilities": ["chat"]}
    assert "/caller-routable-capabilities" not in app.openapi()["paths"]
    assert (
        native_get(
            app, "/caller-routable-capabilities", host="example.invalid"
        ).status_code
        == 400
    )
    assert adapter.health_calls == 0
    assert adapter.execution_calls == 0


def test_non_loopback_compositions_do_not_gain_projection_endpoint() -> None:
    adapter = RecordingAdapter("local", {"chat"})
    owner = create_app(
        local_app_composition=composition([node(["chat"], ["local"])], [adapter])
    )
    receiver = create_receiver_app(
        local_app_composition=owner.state.local_app_composition
    )
    trusted_lan = create_trusted_lan_browser_app(owner, host="192.0.2.10", port=25042)

    assert (
        native_get(
            receiver, "/caller-routable-capabilities", host="127.0.0.1:8123"
        ).status_code
        == 404
    )
    assert (
        native_get(
            trusted_lan,
            "/caller-routable-capabilities",
            host="192.0.2.10:25042",
        ).status_code
        == 404
    )


def test_loopback_projection_uses_static_caller_routing_registry() -> None:
    adapter = RecordingAdapter("local", {"chat"})
    wiring = StaticRemoteWiring(
        node_registry=NodeRegistry(),
        adapter_registry=AdapterRegistry([adapter]),
        remote_registry=RemoteNodeDeclarationRegistry([remote("code")]),
        remote_transport=object(),
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )
    app = add_loopback_browser_routes(create_app(static_remote_wiring=wiring))

    response = native_get(app, "/caller-routable-capabilities", host="127.0.0.1:8123")

    assert response.status_code == 200
    assert response.json() == {"capabilities": ["code"]}


def test_compatibility_surface_does_not_gain_projection_endpoint() -> None:
    app = create_openai_compatibility_app()

    assert (
        native_get(
            app, "/caller-routable-capabilities", host="127.0.0.1:8123"
        ).status_code
        == 404
    )


def test_browser_capability_tabs_follow_the_projection_and_fail_closed() -> None:
    script = (
        files("home_ai_cluster")
        .joinpath("web", "assets", "app.js")
        .read_text(encoding="utf-8")
    )

    assert 'fetch("/caller-routable-capabilities")' in script
    assert "function setCapabilityOperationAvailability(capabilities)" in script
    for capability, tab in (
        ("chat", "#chat-tab"),
        ("code", "#code-tab"),
        ("image-generation", "#image-generation-tab"),
        ("summarize", "#summarize-tab"),
        ("classify", "#classify-tab"),
    ):
        assert f'["{capability}", document.querySelector("{tab}")]' in script
    assert "setCapabilityOperationAvailability(new Set());" in script
    assert "if (!response.ok) return;" in script
    assert (
        "configuration-tab"
        not in script.split("const capabilityTabs", 1)[1].split(
            "function activateTab", 1
        )[0]
    )
    assert "setInterval" not in script
    assert "setTimeout" not in script
