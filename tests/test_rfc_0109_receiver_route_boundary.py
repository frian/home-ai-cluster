import asyncio

import httpx
from fastapi.routing import APIRoute

from home_ai_cluster.api.wiring import LocalAppComposition
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.main import create_app, create_receiver_app


class RecordingAdapter:
    def __init__(self, name: str = "recording") -> None:
        self._name = name
        self.requests: list[ClusterRequest] = []
        self.health_calls = 0

    @property
    def name(self) -> str:
        return self._name

    def health(self) -> AdapterHealth:
        self.health_calls += 1
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.requests.append(request)
        return RuntimeResult(content="receiver result", adapter=self.name)


class FailingHealthAdapter(RecordingAdapter):
    def health(self) -> AdapterHealth:
        raise AssertionError("multi-adapter receiver status must not observe health")


def composition(*adapters: RecordingAdapter) -> LocalAppComposition:
    return LocalAppComposition(
        node_registry=NodeRegistry(
            [
                NodeDescription(
                    id="local",
                    name="Local node",
                    availability="available",
                    health=NodeHealth(healthy=True),
                    capabilities=[Capability(name="chat")],
                    adapters=[adapter.name for adapter in adapters],
                )
            ]
        ),
        adapter_registry=AdapterRegistry(adapters),
    )


def request_payload() -> dict[str, object]:
    return {
        "kind": "chat",
        "request": {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": {"name": "chat"},
        },
    }


def route_set(app) -> set[tuple[str, str]]:
    return {
        (method, route.path)
        for included_router in app.routes
        for route in getattr(
            getattr(included_router, "original_router", None), "routes", ()
        )
        if isinstance(route, APIRoute)
        for method in route.methods
    }


def call(app, method: str, path: str, payload: dict[str, object] | None = None):
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.request(method, path, json=payload)

    return asyncio.run(send())


def test_receiver_app_has_only_the_closed_receiver_route_set() -> None:
    app = create_receiver_app(local_app_composition=composition(RecordingAdapter()))

    assert route_set(app) == {
        ("POST", "/internal/cluster/request"),
        ("GET", "/internal/cluster/status"),
    }
    assert (
        call(app, "POST", "/internal/cluster/request", request_payload()).status_code
        == 200
    )
    assert call(app, "GET", "/internal/cluster/status").status_code == 200
    for method, path in [
        ("POST", "/v1/chat"),
        ("POST", "/v1/chat/sources"),
        ("POST", "/v1/summarize"),
        ("POST", "/v1/classify"),
        ("POST", "/internal/chat/external-information-decision"),
        ("GET", "/docs"),
        ("GET", "/redoc"),
        ("GET", "/openapi.json"),
    ]:
        assert call(app, method, path).status_code == 404


def test_ordinary_app_retains_native_and_receiver_routes() -> None:
    app = create_app(local_app_composition=composition(RecordingAdapter()))

    routes = route_set(app)
    assert ("POST", "/v1/chat") in routes
    assert ("POST", "/internal/cluster/request") in routes
    assert ("GET", "/internal/cluster/status") in routes


def test_receiver_app_reuses_the_exact_composition_for_request_and_status() -> None:
    adapter = RecordingAdapter()
    supplied = composition(adapter)
    app = create_receiver_app(local_app_composition=supplied)

    assert app.state.local_app_composition is supplied
    assert app.state.local_app_composition.node_registry is supplied.node_registry
    assert app.state.local_app_composition.adapter_registry is supplied.adapter_registry
    assert (
        app.state.local_app_composition.execution_intervals
        is supplied.execution_intervals
    )

    response = call(app, "POST", "/internal/cluster/request", request_payload())

    assert response.status_code == 200
    assert response.json() == {
        "content": "receiver result",
        "adapter": "recording",
        "model": None,
        "node_id": "local",
    }
    assert [request.capability.name for request in adapter.requests] == ["chat"]
    assert call(app, "GET", "/internal/cluster/status").json() == {
        "runtime_status": "available"
    }
    assert adapter.health_calls == 1


def test_receiver_status_remains_fail_closed_before_multi_adapter_observation() -> None:
    first = FailingHealthAdapter("first")
    second = FailingHealthAdapter("second")
    app = create_receiver_app(local_app_composition=composition(first, second))

    response = call(app, "GET", "/internal/cluster/status")

    assert response.status_code == 500
    assert response.json() == {"detail": "Unable to inspect local runtime status"}
