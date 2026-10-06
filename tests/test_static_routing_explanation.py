"""RFC-0147 active, payload-free static routing carrier."""

import asyncio
from types import SimpleNamespace

import httpx
import pytest

from home_ai_cluster.api.wiring import build_static_remote_wiring
from home_ai_cluster.core.execution_intervals import ExecutionIntervalCardinality
from home_ai_cluster.core.local_capability_binding import (
    LocalCapabilityBinding,
    LocalCapabilityBindings,
)
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

ROUTE = "/diagnostics/static-routing-explanation"


class RecordingAdapter:
    name = "recording"

    def __init__(self) -> None:
        self.health_calls = 0
        self.execution_calls = 0

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat"), Capability(name="summarize")]

    def health(self) -> object:
        self.health_calls += 1
        raise AssertionError("health must not be called")

    async def chat(self, request: object) -> object:
        self.execution_calls += 1
        raise AssertionError("execution must not be called")

    async def summarize(self, request: object) -> object:
        self.execution_calls += 1
        raise AssertionError("execution must not be called")


def node(
    node_id: str, capabilities: list[str], *, available: bool = True
) -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=node_id,
        availability="available" if available else "unavailable",
        health=NodeHealth(healthy=False),
        capabilities=[Capability(name=name) for name in capabilities],
        adapters=["recording"],
    )


def app_for(
    *,
    local_capabilities: list[str],
    remote_capabilities: list[tuple[str, list[str]]] = (),
    bindings: LocalCapabilityBindings | None = None,
    available: bool = True,
) -> tuple[object, RecordingAdapter]:
    adapter = RecordingAdapter()
    local_nodes = NodeRegistry([node("local", local_capabilities, available=available)])
    adapters = AdapterRegistry([adapter], local_capability_bindings=bindings)
    composition = SimpleNamespace(
        node_registry=local_nodes,
        adapter_registry=adapters,
        execution_intervals=ExecutionIntervalCardinality(),
    )
    remotes = RemoteNodeDeclarationRegistry(
        [
            RemoteNodeDeclaration(
                node=node(node_id, capabilities),
                transport_address=f"http://{node_id}.invalid:8000",
            )
            for node_id, capabilities in remote_capabilities
        ]
    )
    wiring = (
        SimpleNamespace(
            node_registry=local_nodes,
            adapter_registry=adapters,
            remote_registry=remotes,
            remote_transport=SimpleNamespace(
                send=lambda *args: (_ for _ in ()).throw(
                    AssertionError("remote transport must not be called")
                )
            ),
        )
        if remote_capabilities
        else None
    )
    return (
        create_app(
            local_app_composition=composition,
            static_remote_wiring=wiring if len(remote_capabilities) == 1 else None,
            static_remote_collection_wiring=(
                wiring if len(remote_capabilities) > 1 else None
            ),
        ),
        adapter,
    )


def post(app: object, body: dict[str, object]) -> httpx.Response:
    async def call() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.post(ROUTE, json=body)

    return asyncio.run(call())


@pytest.mark.parametrize("local_only", [False, True])
def test_local_only_caller_reports_every_category(local_only: bool) -> None:
    app, adapter = app_for(local_capabilities=["chat"])
    response = post(app, {"capability": "chat", "local_only": local_only})
    assert response.status_code == 200
    assert response.json() == {
        "capability": "chat",
        "local_only": local_only,
        "local_eligible": True,
        "eligible_remote_node_ids": [],
        "remotes_excluded_by_local_only": False,
        "initial_selection": {"kind": "local"},
    }
    assert adapter.health_calls == adapter.execution_calls == 0


def test_no_candidate_and_unavailable_local_node() -> None:
    app, _ = app_for(local_capabilities=["chat"], available=False)
    response = post(app, {"capability": "chat", "local_only": False})
    assert response.json() == {
        "capability": "chat",
        "local_only": False,
        "local_eligible": False,
        "eligible_remote_node_ids": [],
        "remotes_excluded_by_local_only": False,
        "initial_selection": None,
    }


@pytest.mark.parametrize(
    ("local_capabilities", "local_only", "selected", "excluded"),
    [
        (["chat"], False, {"kind": "local"}, False),
        ([], False, {"kind": "declared_remote", "node_id": "second"}, False),
        (["chat"], True, {"kind": "local"}, True),
        ([], True, None, True),
    ],
)
def test_order_selection_and_local_only_exclusion(
    local_capabilities: list[str],
    local_only: bool,
    selected: dict[str, str] | None,
    excluded: bool,
) -> None:
    app, adapter = app_for(
        local_capabilities=local_capabilities or ["summarize"],
        remote_capabilities=[
            ("first", ["summarize"]),
            ("second", ["chat"]),
            ("third", ["chat"]),
        ],
    )
    response = post(app, {"capability": "chat", "local_only": local_only})
    assert response.status_code == 200
    assert response.json() == {
        "capability": "chat",
        "local_only": local_only,
        "local_eligible": bool(local_capabilities),
        "eligible_remote_node_ids": ["second", "third"],
        "remotes_excluded_by_local_only": excluded,
        "initial_selection": selected,
    }
    assert adapter.health_calls == adapter.execution_calls == 0


def test_single_remote_and_binding_restriction() -> None:
    adapter = RecordingAdapter()
    bindings = LocalCapabilityBindings(
        [LocalCapabilityBinding(frozenset({"summarize"}), adapter)]
    )
    app, _ = app_for(
        local_capabilities=["chat", "summarize"],
        remote_capabilities=[("remote", ["chat"])],
        bindings=bindings,
    )
    response = post(app, {"capability": "chat", "local_only": False})
    assert response.status_code == 200
    assert response.json()["local_eligible"] is False
    assert response.json()["initial_selection"] == {
        "kind": "declared_remote",
        "node_id": "remote",
    }


def test_caller_local_restriction_overrides_execution_composition() -> None:
    adapter = RecordingAdapter()
    execution_composition = SimpleNamespace(
        node_registry=NodeRegistry([node("local", ["chat", "summarize"])]),
        adapter_registry=AdapterRegistry([adapter]),
    )
    declaration = RemoteNodeDeclaration(
        node=node("remote", ["chat"]),
        transport_address="http://remote.invalid:8000",
    )
    wiring = build_static_remote_wiring(
        node_registry=NodeRegistry([node("local", ["summarize"])]),
        adapter_registry=execution_composition.adapter_registry,
        remote_declaration=declaration,
        remote_transport=SimpleNamespace(),
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )
    app = create_app(
        local_app_composition=execution_composition,
        static_remote_wiring=wiring,
    )
    response = post(app, {"capability": "chat", "local_only": False})
    assert response.status_code == 200
    assert response.json()["local_eligible"] is False
    assert response.json()["initial_selection"] == {
        "kind": "declared_remote",
        "node_id": "remote",
    }


@pytest.mark.parametrize(
    "body",
    [
        {"capability": "unknown", "local_only": False},
        {"capability": "chat", "local_only": "false"},
        {"capability": "chat", "local_only": False, "messages": []},
        {"capability": "chat"},
    ],
)
def test_invalid_input_fails_closed(body: dict[str, object]) -> None:
    app, _ = app_for(local_capabilities=["chat"])
    response = post(app, body)
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid diagnostic input"}


def test_unavailable_composition_fails_closed() -> None:
    response = post(create_app(), {"capability": "chat", "local_only": False})
    assert response.status_code == 503
    assert response.json() == {"detail": "Active routing explanation unavailable"}


def test_execution_permission_is_not_entered(monkeypatch: pytest.MonkeyPatch) -> None:
    async def forbidden_enter(self: object) -> bool:
        raise AssertionError("execution permission must not be entered")

    monkeypatch.setattr(ExecutionIntervalCardinality, "try_enter", forbidden_enter)
    app, _ = app_for(
        local_capabilities=["chat"], remote_capabilities=[("remote", ["chat"])]
    )
    assert post(app, {"capability": "chat", "local_only": False}).status_code == 200


def test_retained_configuration_is_never_loaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import home_ai_cluster.retained_configuration as retained

    monkeypatch.setattr(
        retained,
        "load_retained_configuration",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("retained load")),
    )
    app, _ = app_for(local_capabilities=["chat"])
    assert post(app, {"capability": "chat", "local_only": False}).status_code == 200


def test_route_is_absent_from_other_app_authorities() -> None:
    ordinary, _ = app_for(local_capabilities=["chat"])
    composition = ordinary.state.local_app_composition
    apps = [
        create_receiver_app(local_app_composition=composition),
        create_trusted_lan_browser_app(ordinary, host="127.0.0.1", port=8000),
        create_openai_compatibility_app(),
        create_static_cluster_openai_compatibility_app(
            [
                ParsedRemoteNodeDeclaration(
                    node_id="remote", base_url="http://remote.invalid"
                )
            ],
            local_app_composition=composition,
        ),
    ]
    for app in apps:
        assert ROUTE not in [getattr(route, "path", None) for route in app.routes]
