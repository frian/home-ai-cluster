import asyncio
import socket
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from home_ai_cluster.adapters.base import RuntimeConnectionUnavailableBeforeRequestError
from home_ai_cluster.api.wiring import LocalAppComposition, build_static_remote_wiring
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
from home_ai_cluster.core.remote_transport import RemoteTransportError
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.local_runtime_composition import (
    create_llama_server_local_app_composition,
    create_local_runtime_composition,
)
from home_ai_cluster.main import create_app
from home_ai_cluster.static_cluster import (
    LOCAL_NODE_ID,
    REMOTE_HTTP_ADAPTER_NAME,
    STATIC_CLUSTER_HOST,
    STATIC_CLUSTER_PORT,
    create_remote_declaration,
    create_static_cluster_app,
    create_static_cluster_collection_app,
    main,
    parse_args,
)
from home_ai_cluster.static_cluster_declaration import (
    RemoteNodeDeclaration as ParsedRemoteNodeDeclaration,
)
from home_ai_cluster.static_cluster_declaration import (
    load_static_cluster_declarations,
)


class FakeAdapter:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error
        self.requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return "ollama"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.requests.append(request)
        if self._error is not None:
            raise self._error
        return RuntimeResult(content="local result", adapter=self.name)


class FakeRemoteTransport:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error
        self.requests: list[ClusterRequest] = []
        self.declarations: list[RemoteNodeDeclaration] = []

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        self.requests.append(request)
        self.declarations.append(declaration)
        if self._error is not None:
            raise self._error
        return ClusterResult(
            content="remote result",
            adapter="remote",
            node_id="receiving-node",
        )


def make_local_node() -> NodeDescription:
    return NodeDescription(
        id=LOCAL_NODE_ID,
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["ollama"],
    )


def make_local_composition(adapter: FakeAdapter) -> LocalAppComposition:
    return LocalAppComposition(
        node_registry=NodeRegistry([make_local_node()]),
        adapter_registry=AdapterRegistry([adapter]),
    )


def make_wiring(
    *,
    local_error: Exception | None = None,
    remote_error: Exception | None = None,
) -> tuple[object, FakeAdapter, FakeRemoteTransport]:
    local = FakeAdapter(local_error)
    remote = FakeRemoteTransport(remote_error)
    local_composition = make_local_composition(local)
    wiring = build_static_remote_wiring(
        node_registry=local_composition.node_registry,
        adapter_registry=local_composition.adapter_registry,
        remote_declaration=create_remote_declaration(
            "operator-remote", "https://private.example:9443"
        ),
        remote_transport=remote,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )
    return wiring, local, remote


def post(app: FastAPI) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as client:
            return await client.post(
                "/v1/chat",
                json={
                    "messages": [{"role": "user", "content": "test message"}],
                    "capability": "chat",
                },
            )

    return asyncio.run(send())


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--remote-node-id", "", "--remote-base-url", "http://remote.test"],
        [
            "--remote-node-id",
            LOCAL_NODE_ID,
            "--remote-base-url",
            "http://remote.test",
        ],
        ["--remote-node-id", "remote", "--remote-base-url", "remote.test"],
        ["--remote-node-id", "remote", "--remote-base-url", "http:///missing"],
    ],
)
def test_parse_args_rejects_invalid_remote_declarations(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        parse_args(argv)


def test_parse_args_normalizes_valid_remote_base_url() -> None:
    args = parse_args(
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.example:8000/",
        ]
    )

    assert args.remote_node_id == "operator-remote"
    assert args.remote_base_url == "https://remote.example:8000"


def test_remote_declaration_is_neutral_and_has_fixed_rfc_facts() -> None:
    declaration = create_remote_declaration("operator-remote", "https://remote.test")

    assert declaration.node.id == "operator-remote"
    assert declaration.node.name == "Declared remote node operator-remote"
    assert declaration.node.availability == "available"
    assert declaration.node.health == NodeHealth(healthy=True)
    assert declaration.node.capabilities == [Capability(name="chat")]
    assert declaration.node.adapters == [REMOTE_HTTP_ADAPTER_NAME]
    assert declaration.transport_address == "https://remote.test"


def test_static_cluster_app_construction_is_inert_and_closes_its_client() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    local_composition = create_local_runtime_composition(runtime="ollama")
    app = create_static_cluster_app(
        "operator-remote",
        "https://remote.test",
        local_app_composition=local_composition,
        client=client,
    )

    wiring = app.state.static_remote_wiring
    declarations = wiring.remote_registry.list_declarations()
    assert wiring.node_registry is local_composition.node_registry
    assert wiring.adapter_registry is local_composition.adapter_registry
    assert len(wiring.node_registry.list_nodes()) == 1
    assert len(declarations) == 1
    assert declarations[0].node.id == "operator-remote"
    assert app.state.static_cluster_http_client is client
    assert requests == []

    async def run_lifespan() -> None:
        async with app.router.lifespan_context(app):
            assert not client.is_closed

    asyncio.run(run_lifespan())
    assert client.is_closed


def test_ordered_declaration_reaches_remote_http_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declaration_path = tmp_path / "cluster.toml"
    declaration_path.write_text(
        '[[remote_nodes]]\n'
        'node_id = "remote-a"\n'
        'base_url = "http://remote-a.test:8000"\n'
        '\n'
        '[[remote_nodes]]\n'
        'node_id = "remote-b"\n'
        'base_url = "http://remote-b.test:8000"\n',
        encoding="utf-8",
    )
    declarations = load_static_cluster_declarations(declaration_path)
    remote_requests: list[httpx.Request] = []

    def remote_handler(request: httpx.Request) -> httpx.Response:
        remote_requests.append(request)
        if request.url.host == "remote-a.test":
            raise httpx.ConnectError("remote-a connection refused", request=request)
        if request.url.host == "remote-b.test":
            return httpx.Response(
                200,
                json={
                    "content": "remote result",
                    "adapter": "remote",
                    "node_id": "receiving-local",
                },
            )
        raise AssertionError(f"unexpected remote endpoint: {request.url}")

    def fail_network(*_: object, **__: object) -> None:
        raise AssertionError("the integration test must not use the network")

    monkeypatch.setattr(socket, "getaddrinfo", fail_network)
    monkeypatch.setattr(socket, "create_connection", fail_network)
    local = FakeAdapter(RuntimeConnectionUnavailableBeforeRequestError("unavailable"))
    local_composition = make_local_composition(local)

    remote_client = httpx.AsyncClient(
        transport=httpx.MockTransport(remote_handler)
    )
    app = create_static_cluster_collection_app(
        declarations.remote_nodes,
        local_app_composition=local_composition,
        client=remote_client,
    )
    wiring = app.state.static_remote_collection_wiring

    assert wiring.node_registry is local_composition.node_registry
    assert wiring.adapter_registry is local_composition.adapter_registry

    async def send_request() -> httpx.Response:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://cluster.test",
            ) as client:
                return await client.post(
                    "/v1/chat",
                    json={
                        "messages": [{"role": "user", "content": "Hello"}],
                        "capability": "chat",
                    },
                )

    response = asyncio.run(send_request())

    assert response.status_code == 200
    assert response.json()["node_id"] == "remote-b"
    assert [remote.node_id for remote in declarations.remote_nodes] == [
        "remote-a",
        "remote-b",
    ]
    assert [
        declaration.node.id
        for declaration in wiring.remote_registry.list_declarations()
    ] == [
        "remote-a",
        "remote-b",
    ]
    assert [request.url.host for request in remote_requests] == [
        "remote-a.test",
        "remote-b.test",
    ]
    assert [request.url.path for request in remote_requests] == [
        "/internal/cluster/request",
        "/internal/cluster/request",
    ]
    assert len(local.requests) == 1
    assert remote_client.is_closed


def test_static_cluster_prefers_usable_local_candidate() -> None:
    wiring, local, remote = make_wiring()

    response = post(create_app(static_remote_wiring=wiring))

    assert response.status_code == 200
    assert response.json()["node_id"] == LOCAL_NODE_ID
    assert len(local.requests) == 1
    assert remote.requests == []


def test_static_cluster_falls_back_once_and_attributes_declared_remote_node() -> None:
    wiring, local, remote = make_wiring(
        local_error=RuntimeConnectionUnavailableBeforeRequestError("not connected")
    )

    response = post(create_app(static_remote_wiring=wiring))

    assert response.status_code == 200
    assert response.json()["node_id"] == "operator-remote"
    assert len(local.requests) == 1
    assert len(remote.requests) == 1
    assert remote.declarations == wiring.remote_registry.list_declarations()


def test_static_cluster_normalizes_exhausted_connection_failures() -> None:
    local_error = RuntimeConnectionUnavailableBeforeRequestError(
        "httpx ConnectError http://127.0.0.1:11434 local-model"
    )
    remote_error = RuntimeConnectionUnavailableBeforeRequestError(
        "httpx ConnectError https://private.example:9443 remote-model"
    )
    wiring, local, remote = make_wiring(
        local_error=local_error,
        remote_error=remote_error,
    )

    response = post(create_app(static_remote_wiring=wiring))

    assert response.status_code == 503
    assert response.json() == {"detail": "Runtime adapter unavailable"}
    for value in (
        "httpx",
        "ConnectError",
        "RuntimeConnectionUnavailableBeforeRequestError",
        "http://",
        "https://",
        "traceback",
        "private.example",
        "local-model",
        "remote-model",
    ):
        assert value not in response.text
    assert len(local.requests) == 1
    assert len(remote.requests) == 1


def test_static_cluster_routes_call_neutral_static_remote_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    wiring, _, _ = make_wiring()
    expected = ClusterResult(
        content="routed result",
        adapter="remote",
        node_id="operator-remote",
    )
    calls: list[tuple[object, ...]] = []

    async def neutral_fallback(*args: object) -> ClusterResult:
        calls.append(args)
        return expected

    monkeypatch.setattr(
        routes,
        "orchestrate_request_with_static_remote_fallback",
        neutral_fallback,
    )

    response = post(create_app(static_remote_wiring=wiring))

    assert response.status_code == 200
    assert response.json()["node_id"] == "operator-remote"
    assert len(calls) == 1
    _, node_registry, adapter_registry, remote_registry, remote_transport = calls[0]
    assert node_registry is wiring.node_registry
    assert adapter_registry is wiring.adapter_registry
    assert remote_registry is wiring.remote_registry
    assert remote_transport is wiring.remote_transport


def test_static_cluster_hides_remote_base_url_from_public_transport_failure() -> None:
    wiring, local, remote = make_wiring(
        local_error=RuntimeConnectionUnavailableBeforeRequestError("not connected"),
        remote_error=RemoteTransportError("https://private.example:9443 failed"),
    )

    response = post(create_app(static_remote_wiring=wiring))

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert "private.example" not in response.text
    assert len(local.requests) == 1
    assert len(remote.requests) == 1


@pytest.mark.parametrize(
    ("runtime_argv", "composition_arguments"),
    [
        (
            ["--runtime", "ollama"],
            {
                "runtime": "ollama",
                "llama_server_base_url": None,
                "llama_server_model": None,
            },
        ),
        (
            [
                "--runtime",
                "llama-server",
                "--llama-server-base-url",
                "http://127.0.0.1:8080",
                "--llama-server-model",
                "local-model",
            ],
            {
                "runtime": "llama-server",
                "llama_server_base_url": "http://127.0.0.1:8080",
                "llama_server_model": "local-model",
            },
        ),
    ],
)
def test_main_runs_fixed_loopback_static_cluster_server(
    monkeypatch: pytest.MonkeyPatch,
    runtime_argv: list[str],
    composition_arguments: dict[str, str | None],
) -> None:
    from home_ai_cluster import static_cluster

    app = FastAPI()
    recorded: dict[str, object] = {}
    local_composition = create_local_runtime_composition(runtime="ollama")

    def create_local_composition(**kwargs: object) -> LocalAppComposition:
        recorded["composition_arguments"] = kwargs
        return local_composition

    monkeypatch.setattr(
        static_cluster,
        "create_local_runtime_composition",
        create_local_composition,
    )
    monkeypatch.setattr(
        static_cluster,
        "create_static_cluster_app",
        lambda *_, local_app_composition: recorded.update(
            local_app_composition=local_app_composition
        )
        or app,
    )
    monkeypatch.setattr(
        static_cluster.uvicorn,
        "run",
        lambda run_app, *, host, port: recorded.update(
            app=run_app, host=host, port=port
        ),
    )

    main(
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.test",
            *runtime_argv,
        ]
    )

    assert recorded == {
        "composition_arguments": composition_arguments,
        "local_app_composition": local_composition,
        "app": app,
        "host": STATIC_CLUSTER_HOST,
        "port": STATIC_CLUSTER_PORT,
    }


def test_static_cluster_constructors_accept_llama_server_composition_without_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import local_runtime_composition

    class RecordingLlamaServerAdapter:
        def __init__(self, **_: object) -> None:
            self.health_calls = 0
            self.chat_calls = 0

        @property
        def name(self) -> str:
            return "llama-server"

        def health(self) -> AdapterHealth:
            self.health_calls += 1
            return AdapterHealth(available=True)

        def capabilities(self) -> list[Capability]:
            return [Capability(name="chat")]

        async def chat(self, request: ClusterRequest) -> RuntimeResult:
            self.chat_calls += 1
            return RuntimeResult(content="unused", adapter=self.name)

    created: list[RecordingLlamaServerAdapter] = []

    def create_adapter(**_: object) -> RecordingLlamaServerAdapter:
        adapter = RecordingLlamaServerAdapter()
        created.append(adapter)
        return adapter

    monkeypatch.setattr(
        local_runtime_composition,
        "LlamaServerAdapter",
        create_adapter,
    )

    local_composition = create_llama_server_local_app_composition(
        base_url="http://127.0.0.1:8080",
        model="local-model",
    )
    inline_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: None))
    collection_client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: None)
    )
    inline_app = create_static_cluster_app(
        "operator-remote",
        "https://remote.test",
        local_app_composition=local_composition,
        client=inline_client,
    )
    collection_app = create_static_cluster_collection_app(
        [
            ParsedRemoteNodeDeclaration(
                node_id="operator-remote",
                base_url="https://remote.test",
            )
        ],
        local_app_composition=local_composition,
        client=collection_client,
    )

    assert len(created) == 1
    assert created[0].health_calls == 0
    assert created[0].chat_calls == 0
    assert (
        inline_app.state.static_remote_wiring.node_registry
        is local_composition.node_registry
    )
    assert (
        inline_app.state.static_remote_wiring.adapter_registry
        is local_composition.adapter_registry
    )
    assert (
        collection_app.state.static_remote_collection_wiring.node_registry
        is local_composition.node_registry
    )
    assert (
        collection_app.state.static_remote_collection_wiring.adapter_registry
        is local_composition.adapter_registry
    )

    asyncio.run(inline_client.aclose())
    asyncio.run(collection_client.aclose())
