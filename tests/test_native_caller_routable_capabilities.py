"""RFC-0152's bounded native capability projection carrier."""

import asyncio
from types import SimpleNamespace

import httpx
import pytest

import home_ai_cluster.api.caller_routable_capabilities as carrier
from home_ai_cluster.api.wiring import LocalAppComposition, StaticRemoteWiring
from home_ai_cluster.core.models import Capability, NodeDescription, NodeHealth
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.main import create_app, create_receiver_app
from home_ai_cluster.openai_compatibility import (
    create_openai_compatibility_app,
    create_static_cluster_openai_compatibility_app,
)
from home_ai_cluster.static_cluster_declaration import (
    RemoteNodeDeclaration as ParsedRemoteNodeDeclaration,
)
from home_ai_cluster.web.trusted_lan_browser import create_trusted_lan_browser_app

ROUTE = "/diagnostics/caller-routable-capabilities"


class RecordingAdapter:
    name = "local"

    def __init__(self, capabilities: set[str]) -> None:
        self._capabilities = [Capability(name=name) for name in capabilities]
        self.health_calls = 0
        self.execution_calls = 0

    def capabilities(self) -> list[Capability]:
        return list(self._capabilities)

    def health(self) -> object:
        self.health_calls += 1
        raise AssertionError("projection must not inspect runtime health")

    async def chat(self, _: object) -> object:
        self.execution_calls += 1
        raise AssertionError("projection must not execute")


def node(*capabilities: str, available: bool = True) -> NodeDescription:
    return NodeDescription(
        id="local",
        name="local",
        availability="available" if available else "unavailable",
        health=NodeHealth(healthy=False),
        capabilities=[Capability(name=name) for name in capabilities],
        adapters=["local"],
    )


def remote(*capabilities: str) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=NodeDescription(
            id="remote",
            name="remote",
            availability="available",
            health=NodeHealth(healthy=False),
            capabilities=[Capability(name=name) for name in capabilities],
            adapters=["remote-http"],
        ),
        transport_address="http://remote.invalid:8000",
    )


def composition(
    nodes: list[NodeDescription], adapter: RecordingAdapter
) -> LocalAppComposition:
    return LocalAppComposition(
        node_registry=NodeRegistry(nodes), adapter_registry=AdapterRegistry([adapter])
    )


def get(app: object) -> httpx.Response:
    async def call() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://127.0.0.1:25042",
        ) as client:
            return await client.get(ROUTE)

    return asyncio.run(call())


def test_native_response_uses_local_eligibility_without_side_effects() -> None:
    adapter = RecordingAdapter({"chat", "code"})
    response = get(
        create_app(local_app_composition=composition([node("chat")], adapter))
    )

    assert response.status_code == 200
    assert response.json() == {"capabilities": ["chat"]}
    assert adapter.health_calls == adapter.execution_calls == 0


def test_adapter_support_without_active_local_path_does_not_create_membership() -> None:
    adapter = RecordingAdapter({"chat"})
    response = get(create_app(local_app_composition=composition([], adapter)))

    assert response.status_code == 200
    assert response.json() == {"capabilities": []}


def test_caller_local_routing_restriction_remains_authoritative() -> None:
    adapter = RecordingAdapter({"chat"})
    local = composition([node("chat")], adapter)
    wiring = StaticRemoteWiring(
        node_registry=NodeRegistry(),
        adapter_registry=local.adapter_registry,
        remote_registry=RemoteNodeDeclarationRegistry([remote("code")]),
        remote_transport=SimpleNamespace(),
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )

    response = get(create_app(local_app_composition=local, static_remote_wiring=wiring))

    assert response.status_code == 200
    assert response.json() == {"capabilities": ["code"]}


def test_active_static_remote_is_projected_without_contacting_it() -> None:
    adapter = RecordingAdapter({"chat"})
    wiring = StaticRemoteWiring(
        node_registry=NodeRegistry([node("chat")]),
        adapter_registry=AdapterRegistry([adapter]),
        remote_registry=RemoteNodeDeclarationRegistry([remote("chat", "code")]),
        remote_transport=SimpleNamespace(
            send=lambda *_: (_ for _ in ()).throw(AssertionError("must not probe"))
        ),
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )
    response = get(create_app(static_remote_wiring=wiring))

    assert response.status_code == 200
    assert response.json() == {"capabilities": ["chat", "code"]}
    assert adapter.health_calls == adapter.execution_calls == 0


def test_valid_no_path_composition_returns_a_successful_empty_set() -> None:
    adapter = RecordingAdapter({"chat"})
    response = get(create_app(local_app_composition=composition([], adapter)))

    assert response.status_code == 200
    assert response.json() == {"capabilities": []}


def test_projection_failure_fails_closed_without_substituting_empty_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        carrier,
        "project_caller_routable_capabilities",
        lambda *_: (_ for _ in ()).throw(ValueError("private failure")),
    )

    response = get(create_app())

    assert response.status_code == 503
    assert response.json() == {"detail": "Caller routable capabilities unavailable"}


def test_route_is_absent_from_every_other_constructible_authority() -> None:
    adapter = RecordingAdapter({"chat"})
    ordinary = create_app(local_app_composition=composition([node("chat")], adapter))
    local = ordinary.state.local_app_composition
    apps = [
        create_receiver_app(local_app_composition=local),
        create_trusted_lan_browser_app(ordinary, host="192.0.2.10", port=25042),
        create_openai_compatibility_app(),
        create_static_cluster_openai_compatibility_app(
            [
                ParsedRemoteNodeDeclaration(
                    node_id="remote", base_url="http://remote.invalid"
                )
            ],
            local_app_composition=local,
        ),
    ]

    for app in apps:
        assert ROUTE not in [getattr(route, "path", None) for route in app.routes]
