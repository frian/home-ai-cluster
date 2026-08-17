import asyncio

import httpx
import pytest

from home_ai_cluster.adapters.base import (
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.api.wiring import (
    build_static_remote_collection_wiring,
    build_static_remote_wiring,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.main import create_app


class RecordingRemoteTransport:
    def __init__(self, outcomes: dict[str, ClusterResult | Exception]) -> None:
        self.outcomes = outcomes
        self.requests: list[ClusterRequest] = []
        self.attempted_node_ids: list[str] = []

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        node_id = declaration.node.id
        self.requests.append(request)
        self.attempted_node_ids.append(node_id)
        outcome = self.outcomes[node_id]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class RecordingLocalAdapter:
    def __init__(self, outcome: RuntimeResult | Exception) -> None:
        self.outcome = outcome
        self.requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return "local"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.requests.append(request)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def make_node(node_id: str, adapter_name: str = "remote") -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=[adapter_name],
    )


def make_remote(node_id: str, address: str) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node(node_id),
        transport_address=address,
    )


def make_result(node_id: str) -> ClusterResult:
    return ClusterResult(
        content=f"result from {node_id}",
        adapter="remote",
        node_id=node_id,
    )


def collection_wiring(
    transport: RecordingRemoteTransport,
    remote_node_ids: list[str],
    local_adapter: RecordingLocalAdapter | None = None,
):
    node_registry = (
        NodeRegistry([make_node("local", "local")])
        if local_adapter is not None
        else NodeRegistry()
    )
    adapter_registry = (
        AdapterRegistry([local_adapter])
        if local_adapter is not None
        else AdapterRegistry()
    )
    return build_static_remote_collection_wiring(
        node_registry=node_registry,
        adapter_registry=adapter_registry,
        remote_declarations=[
            make_remote(node_id, f"http://{node_id}.local:8000")
            for node_id in remote_node_ids
        ],
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )


def chat_payload() -> dict[str, object]:
    return {
        "messages": [{"role": "user", "content": "Hello"}],
        "capability": "chat",
    }


def post_chat(app, *, raise_app_exceptions: bool = True) -> httpx.Response:
    async def post() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(
                app=app,
                raise_app_exceptions=raise_app_exceptions,
            ),
            base_url="http://testserver",
        ) as client:
            return await client.post("/v1/chat", json=chat_payload())

    return asyncio.run(post())


def test_create_app_stores_ordered_static_remote_collection_wiring() -> None:
    first = make_remote("remote-a", "http://remote-a.local:8000")
    second = make_remote("remote-b", "http://remote-b.local:8000")
    transport = RecordingRemoteTransport(
        {"remote-a": make_result("remote-a"), "remote-b": make_result("remote-b")}
    )
    wiring = build_static_remote_collection_wiring(
        node_registry=NodeRegistry([make_node("local")]),
        adapter_registry=AdapterRegistry(),
        remote_declarations=[first, second],
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )

    app = create_app(static_remote_collection_wiring=wiring)

    assert app.state.static_remote_collection_wiring is wiring
    assert wiring.remote_registry.list_declarations() == [first, second]
    assert app.state.static_remote_wiring is None
    assert transport.requests == []


def test_collection_wiring_uses_ordered_fallback_after_local_connection_failure() -> (
    None
):
    local = RecordingLocalAdapter(
        RuntimeConnectionUnavailableBeforeRequestError("local unavailable")
    )
    transport = RecordingRemoteTransport({"remote-a": make_result("remote-a")})
    wiring = collection_wiring(transport, ["remote-a"], local)

    response = post_chat(create_app(static_remote_collection_wiring=wiring))

    assert response.status_code == 200
    assert response.json()["node_id"] == "remote-a"
    assert len(local.requests) == 1
    assert transport.attempted_node_ids == ["remote-a"]
    assert transport.requests[0].constraints.local_only is False


def test_collection_wiring_advances_to_second_remote_after_first_is_unavailable() -> (
    None
):
    transport = RecordingRemoteTransport(
        {
            "remote-a": RuntimeConnectionUnavailableBeforeRequestError("unavailable"),
            "remote-b": make_result("remote-b"),
        }
    )
    wiring = collection_wiring(transport, ["remote-a", "remote-b"])

    response = post_chat(create_app(static_remote_collection_wiring=wiring))

    assert response.status_code == 200
    assert response.json()["node_id"] == "remote-b"
    assert transport.attempted_node_ids == ["remote-a", "remote-b"]


def test_collection_wiring_normalizes_exhausted_connection_failures() -> None:
    local = RecordingLocalAdapter(
        RuntimeConnectionUnavailableBeforeRequestError(
            "httpx ConnectError http://127.0.0.1:11434 local-model"
        )
    )
    transport = RecordingRemoteTransport(
        {
            "remote-a": RuntimeConnectionUnavailableBeforeRequestError(
                "httpx ConnectError https://remote-a.local:8000 remote-a-model"
            ),
            "remote-b": RuntimeConnectionUnavailableBeforeRequestError(
                "httpx ConnectError https://remote-b.local:8000 remote-b-model"
            ),
        }
    )
    wiring = collection_wiring(transport, ["remote-a", "remote-b"], local)

    response = post_chat(create_app(static_remote_collection_wiring=wiring))

    assert response.status_code == 503
    assert response.json() == {"detail": "Runtime adapter unavailable"}
    for value in (
        "httpx",
        "ConnectError",
        "RuntimeConnectionUnavailableBeforeRequestError",
        "http://",
        "https://",
        "traceback",
        "remote-a-model",
        "remote-b-model",
    ):
        assert value not in response.text
    assert len(local.requests) == 1
    assert transport.attempted_node_ids == ["remote-a", "remote-b"]


def test_collection_wiring_does_not_call_second_remote_after_first_succeeds() -> None:
    transport = RecordingRemoteTransport(
        {"remote-a": make_result("remote-a"), "remote-b": make_result("remote-b")}
    )
    wiring = collection_wiring(transport, ["remote-a", "remote-b"])

    response = post_chat(create_app(static_remote_collection_wiring=wiring))

    assert response.status_code == 200
    assert response.json()["node_id"] == "remote-a"
    assert transport.attempted_node_ids == ["remote-a"]


def test_collection_wiring_does_not_advance_after_non_accepted_remote_error() -> None:
    transport = RecordingRemoteTransport(
        {"remote-a": ValueError("request failed"), "remote-b": make_result("remote-b")}
    )
    wiring = collection_wiring(transport, ["remote-a", "remote-b"])

    response = post_chat(
        create_app(static_remote_collection_wiring=wiring),
        raise_app_exceptions=False,
    )

    assert response.status_code == 500
    assert transport.attempted_node_ids == ["remote-a"]


def test_single_remote_wiring_path_remains_unchanged() -> None:
    transport = RecordingRemoteTransport({"remote-a": make_result("remote-a")})
    wiring = build_static_remote_wiring(
        node_registry=NodeRegistry(),
        adapter_registry=AdapterRegistry(),
        remote_declaration=make_remote("remote-a", "http://remote-a.local:8000"),
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )

    response = post_chat(create_app(static_remote_wiring=wiring))

    assert response.status_code == 200
    assert response.json()["node_id"] == "remote-a"
    assert transport.attempted_node_ids == ["remote-a"]


def test_local_only_path_remains_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    from home_ai_cluster.api import routes

    local = RecordingLocalAdapter(
        RuntimeResult(content="local result", adapter="local")
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        lambda: NodeRegistry([make_node("local", "local")]),
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([local]),
    )

    response = post_chat(create_app())

    assert response.status_code == 200
    assert response.json()["node_id"] == "local"
    assert local.requests[0].constraints.local_only is True


def test_create_app_without_collection_wiring_stores_none() -> None:
    app = create_app()

    assert app.state.static_remote_collection_wiring is None
