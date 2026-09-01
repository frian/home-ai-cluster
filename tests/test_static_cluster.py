import asyncio
import logging
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn
from fastapi import FastAPI

from home_ai_cluster.adapters.base import RuntimeConnectionUnavailableBeforeRequestError
from home_ai_cluster.api.wiring import LocalAppComposition, build_static_remote_wiring
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClassifyRequest,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
    RequestConstraints,
    RuntimeResult,
    SummarizeRequest,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
    declared_remote_routing_candidate_for_request,
)
from home_ai_cluster.core.remote_transport import (
    HttpRemoteTransport,
    RemoteTransportError,
)
from home_ai_cluster.core.routing_candidates import (
    RoutingCandidateSelectionMode,
    routing_candidates_for_request,
    select_automatic_capability_routing_candidate,
)
from home_ai_cluster.local_runtime_composition import (
    create_llama_server_local_app_composition,
    create_local_runtime_composition,
)
from home_ai_cluster.main import create_app
from home_ai_cluster.static_cluster import (
    LOCAL_NODE_ID,
    REMOTE_HTTP_ADAPTER_NAME,
    STATIC_CLUSTER_HOST,
    create_remote_declaration,
    create_static_cluster_app,
    create_static_cluster_collection_app,
    create_static_cluster_http_client,
    main,
    parse_args,
)
from home_ai_cluster.static_cluster_declaration import (
    RemoteNodeDeclaration as ParsedRemoteNodeDeclaration,
)
from home_ai_cluster.static_cluster_declaration import (
    load_static_cluster_declarations,
)


@pytest.fixture(autouse=True)
def isolated_retained_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))


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


def test_process_owned_remote_client_disables_httpx_environment_trust(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options: list[dict[str, object]] = []
    client = object()

    def create_client(**kwargs: object) -> object:
        options.append(kwargs)
        return client

    monkeypatch.setattr(
        "home_ai_cluster.static_cluster.httpx.AsyncClient", create_client
    )

    assert create_static_cluster_http_client() is client
    assert options == [{"timeout": None, "trust_env": False}]


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
    remote_capabilities: tuple[str, ...] = ("chat", "summarize"),
) -> tuple[object, FakeAdapter, FakeRemoteTransport]:
    local = FakeAdapter(local_error)
    remote = FakeRemoteTransport(remote_error)
    local_composition = make_local_composition(local)
    wiring = build_static_remote_wiring(
        node_registry=local_composition.node_registry,
        adapter_registry=local_composition.adapter_registry,
        remote_declaration=create_remote_declaration(
            "operator-remote",
            "https://private.example:9443",
            remote_capabilities,
        ),
        remote_transport=remote,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )
    return wiring, local, remote


def post(
    app: FastAPI,
    path: str = "/v1/chat",
    json: dict[str, object] | None = None,
) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as client:
            return await client.post(
                path,
                json=json
                or {
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
        ["--remote-node-id", "remote", "--remote-base-url", "http://user@remote.test"],
        [
            "--remote-node-id",
            "remote",
            "--remote-base-url",
            "http://user:secret@remote.test",
        ],
        [
            "--remote-node-id",
            "remote",
            "--remote-base-url",
            "http://remote.test/base",
        ],
        [
            "--remote-node-id",
            "remote",
            "--remote-base-url",
            "http://remote.test?token=x",
        ],
        [
            "--remote-node-id",
            "remote",
            "--remote-base-url",
            "http://remote.test#fragment",
        ],
        ["--remote-node-id", "remote", "--remote-base-url", "http://remote.test?"],
        ["--remote-node-id", "remote", "--remote-base-url", "http://remote.test#"],
        ["--remote-node-id", "remote", "--remote-base-url", "http://remote.test:"],
        ["--remote-node-id", "remote", "--remote-base-url", "http://remote.test:/"],
        [
            "--remote-node-id",
            "remote",
            "--remote-base-url",
            "http://remote.test:invalid",
        ],
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
    assert declaration.node.capabilities == [
        Capability(name="chat"),
        Capability(name="summarize"),
    ]
    assert declaration.node.adapters == [REMOTE_HTTP_ADAPTER_NAME]
    assert declaration.transport_address == "https://remote.test"


def test_ordinary_remote_declaration_is_eligible_for_summarize() -> None:
    declaration = create_remote_declaration("operator-remote", "https://remote.test")
    request = SummarizeRequest(text="Source text")

    candidate = declared_remote_routing_candidate_for_request(
        request,
        RemoteNodeDeclarationRegistry([declaration]),
    )

    assert candidate is not None
    assert candidate.node is declaration.node
    assert candidate.capability == Capability(name="summarize")


def test_explicit_classify_remote_declaration_is_eligible_for_classify() -> None:
    declaration = create_remote_declaration(
        "operator-remote", "https://remote.test", ("classify",)
    )
    request = ClassifyRequest(
        text="Source text",
        labels=["invoice", "personal"],
        constraints=RequestConstraints(local_only=False),
    )

    candidate = declared_remote_routing_candidate_for_request(
        request,
        RemoteNodeDeclarationRegistry([declaration]),
    )

    assert candidate is not None
    assert candidate.node is declaration.node
    assert candidate.capability == Capability(name="classify")


def test_explicit_classify_declaration_routes_to_the_eligible_remote() -> None:
    local = FakeAdapter()
    remote = FakeRemoteTransport()
    remote_declaration = create_remote_declaration(
        "classification-remote", "https://remote.test", ("classify",)
    )
    wiring = build_static_remote_wiring(
        node_registry=NodeRegistry([make_local_node()]),
        adapter_registry=AdapterRegistry([local]),
        remote_declaration=remote_declaration,
        remote_transport=remote,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )
    request = ClassifyRequest(
        text="Source text",
        labels=["invoice", "personal"],
        constraints=RequestConstraints(local_only=False),
    )

    candidates = routing_candidates_for_request(
        request,
        wiring.node_registry,
        wiring.adapter_registry,
        wiring.remote_registry,
    )
    selection = select_automatic_capability_routing_candidate(request, candidates)

    assert candidates.local is None
    assert candidates.declared_remote is not None
    assert selection.selected is not None
    assert selection.selected.local is None
    assert selection.selected.declared_remote is not None
    assert selection.selected.declared_remote.node.id == "classification-remote"


@pytest.mark.parametrize(
    ("capabilities", "expected"),
    [
        (("chat",), [Capability(name="chat")]),
        (("summarize",), [Capability(name="summarize")]),
        (("classify",), [Capability(name="classify")]),
        (
            ("classify", "chat", "summarize"),
            [
                Capability(name="classify"),
                Capability(name="chat"),
                Capability(name="summarize"),
            ],
        ),
    ],
)
def test_inline_capabilities_reach_remote_node_construction(
    capabilities: tuple[str, ...],
    expected: list[Capability],
) -> None:
    declaration = create_remote_declaration(
        "operator-remote",
        "https://remote.test",
        capabilities,
    )

    assert declaration.node.capabilities == expected


def test_ordered_toml_capabilities_reach_remote_node_construction(
    tmp_path: Path,
) -> None:
    declaration_path = tmp_path / "cluster.toml"
    declaration_path.write_text(
        "[[remote_nodes]]\n"
        'node_id = "chat-node"\n'
        'base_url = "http://chat.example:8000"\n'
        'capabilities = ["chat"]\n\n'
        "[[remote_nodes]]\n"
        'node_id = "summary-node"\n'
        'base_url = "http://summary.example:8000"\n'
        'capabilities = ["summarize"]\n',
        encoding="utf-8",
    )
    declarations = load_static_cluster_declarations(declaration_path)
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(500))
    )
    app = create_static_cluster_collection_app(
        declarations.remote_nodes,
        local_app_composition=create_local_runtime_composition(runtime="ollama"),
        client=client,
    )

    remote_registry = app.state.static_remote_collection_wiring.remote_registry
    remote_nodes = remote_registry.list_declarations()

    assert [declaration.node.id for declaration in remote_nodes] == [
        "chat-node",
        "summary-node",
    ]
    assert [declaration.node.capabilities for declaration in remote_nodes] == [
        [Capability(name="chat")],
        [Capability(name="summarize")],
    ]

    asyncio.run(client.aclose())


def test_main_wraps_the_fixed_loopback_static_cluster_application(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import static_cluster

    api_app = FastAPI()
    browser_app = FastAPI()
    recorded: dict[str, object] = {}

    monkeypatch.setattr(
        static_cluster,
        "create_local_runtime_composition",
        lambda **_: object(),
    )
    monkeypatch.setattr(
        static_cluster,
        "create_static_cluster_app",
        lambda *_args, **_kwargs: api_app,
    )
    monkeypatch.setattr(
        static_cluster,
        "add_loopback_browser_routes",
        lambda app: recorded.setdefault("api_app", app) and browser_app,
    )
    monkeypatch.setattr(
        static_cluster.uvicorn,
        "run",
        lambda app, *, host, port: recorded.update(app=app, host=host, port=port),
    )

    static_cluster.main(
        [
            "--remote-node-id",
            "remote-node",
            "--remote-base-url",
            "http://remote.example:8000",
        ]
    )

    assert recorded == {
        "api_app": api_app,
        "app": browser_app,
        "host": STATIC_CLUSTER_HOST,
        "port": 25042,
    }


def test_reusable_static_cluster_factory_remains_page_free() -> None:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(500))
    )
    app = create_static_cluster_app(
        "remote-node",
        "http://remote.example:8000",
        local_app_composition=create_local_runtime_composition(runtime="ollama"),
        client=client,
    )

    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            return await client.get("/")

    assert asyncio.run(send()).status_code == 404

    asyncio.run(client.aclose())


def test_main_passes_toml_local_capabilities_to_caller_composition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import static_cluster

    declaration_path = tmp_path / "cluster.toml"
    declaration_path.write_text(
        'local_capabilities = ["chat"]\n'
        "[[remote_nodes]]\n"
        'node_id = "summary-remote"\n'
        'base_url = "https://remote.example"\n'
        'capabilities = ["summarize"]\n',
        encoding="utf-8",
    )
    recorded: dict[str, object] = {}

    def create_collection_app(
        remote_nodes: tuple[ParsedRemoteNodeDeclaration, ...],
        *,
        local_app_composition: LocalAppComposition,
    ) -> FastAPI:
        recorded["remote_nodes"] = remote_nodes
        recorded["local_capabilities"] = (
            local_app_composition.node_registry.list_nodes()[0].capabilities
        )
        return FastAPI()

    monkeypatch.setattr(
        static_cluster,
        "create_static_cluster_collection_app",
        create_collection_app,
    )
    monkeypatch.setattr(static_cluster.uvicorn, "run", lambda *_1, **_2: None)

    main(["--declaration", str(declaration_path)])

    assert recorded == {
        "remote_nodes": (
            ParsedRemoteNodeDeclaration(
                node_id="summary-remote",
                base_url="https://remote.example",
                capabilities=("summarize",),
            ),
        ),
        "local_capabilities": [Capability(name="chat")],
    }


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
        "[[remote_nodes]]\n"
        'node_id = "remote-a"\n'
        'base_url = "http://remote-a.test:8000"\n'
        "\n"
        "[[remote_nodes]]\n"
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

    remote_client = httpx.AsyncClient(transport=httpx.MockTransport(remote_handler))
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


def test_restricted_caller_local_capabilities_route_by_eligibility() -> None:
    local = FakeAdapter()
    remote = FakeRemoteTransport()
    wiring = build_static_remote_wiring(
        node_registry=NodeRegistry([make_local_node()]),
        adapter_registry=AdapterRegistry([local]),
        remote_declaration=create_remote_declaration(
            "summary-remote",
            "https://remote.test",
            ("summarize",),
        ),
        remote_transport=remote,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )

    app = create_app(static_remote_wiring=wiring)

    async def send_summarize() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            return await client.post("/v1/summarize", json={"text": "Source"})

    chat_response = post(app)
    summarize_response = asyncio.run(send_summarize())

    assert chat_response.status_code == 200
    assert chat_response.json()["node_id"] == LOCAL_NODE_ID
    assert len(local.requests) == 1
    assert summarize_response.status_code == 200
    assert summarize_response.json()["node_id"] == "summary-remote"
    assert len(remote.requests) == 1
    assert isinstance(remote.requests[0], SummarizeRequest)
    assert remote.requests[0].text == "Source"


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


def test_static_cluster_preserves_receiver_runtime_unavailable_through_transport() -> (
    None
):
    receiver_requests: list[httpx.Request] = []

    def receiver(request: httpx.Request) -> httpx.Response:
        receiver_requests.append(request)
        return httpx.Response(
            503,
            json={
                "detail": "private-host secret-token private-model unavailable",
            },
        )

    local_composition = make_local_composition(FakeAdapter())
    remote_transport_client = httpx.AsyncClient(transport=httpx.MockTransport(receiver))
    wiring = build_static_remote_wiring(
        node_registry=local_composition.node_registry,
        adapter_registry=local_composition.adapter_registry,
        remote_declaration=create_remote_declaration(
            "operator-remote",
            "https://private.example:9443",
            ("summarize",),
        ),
        remote_transport=HttpRemoteTransport(remote_transport_client),
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )

    async def send() -> httpx.Response:
        async with remote_transport_client:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(
                    app=create_app(static_remote_wiring=wiring),
                    raise_app_exceptions=False,
                ),
                base_url="http://testserver",
            ) as client:
                return await client.post("/v1/summarize", json={"text": "source"})

    response = asyncio.run(send())

    assert response.status_code == 503
    assert response.json() == {"detail": "Runtime adapter unavailable"}
    assert len(receiver_requests) == 1
    for sensitive_value in ("private-host", "secret-token", "private-model"):
        assert sensitive_value not in response.text


@pytest.mark.parametrize(
    ("path", "body"),
    [
        (
            "/v1/chat",
            {
                "messages": [{"role": "user", "content": "private prompt"}],
                "capability": "chat",
            },
        ),
        ("/v1/summarize", {"text": "private prompt"}),
        (
            "/v1/classify",
            {"text": "private prompt", "labels": ["one", "two"]},
        ),
        (
            "/v1/chat/sources",
            {
                "question": "private prompt",
                "sources": [
                    {
                        "title": "source",
                        "url": "https://documentation.invalid/source",
                        "content": "private source content",
                    }
                ],
            },
        ),
    ],
)
def test_static_cluster_contains_remote_transport_failure_for_routed_families(
    path: str, body: dict[str, object]
) -> None:
    error = RemoteTransportError("fake-private-endpoint.invalid:9443 transport failed")
    error.__cause__ = RuntimeError("fake HTTPX transport detail")
    wiring, _, remote = make_wiring(
        local_error=RuntimeConnectionUnavailableBeforeRequestError("not connected"),
        remote_error=error,
        remote_capabilities=("chat", "summarize", "classify"),
    )

    response = post(create_app(static_remote_wiring=wiring), path, body)

    assert response.status_code == 500
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "Internal Server Error"
    for sensitive_value in (
        "fake-private-endpoint.invalid",
        "fake HTTPX transport detail",
        "private prompt",
        "private source content",
    ):
        assert sensitive_value not in response.text
    assert len(remote.requests) == 1


def test_static_cluster_remote_transport_failure_does_not_reach_uvicorn_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = RemoteTransportError("fake-private-endpoint.invalid:9443 transport failed")
    error.__cause__ = RuntimeError("fake HTTPX transport detail")
    wiring, _, remote = make_wiring(
        local_error=RuntimeConnectionUnavailableBeforeRequestError("not connected"),
        remote_error=error,
    )
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        host, port = listener.getsockname()

    server = uvicorn.Server(
        uvicorn.Config(
            create_app(static_remote_wiring=wiring),
            host=host,
            port=port,
            log_config=None,
            access_log=False,
        )
    )
    thread = threading.Thread(target=server.run)
    caplog.set_level(logging.ERROR, logger="uvicorn.error")
    thread.start()
    try:
        deadline = time.monotonic() + 2
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.01)
        assert server.started

        response = httpx.post(
            f"http://{host}:{port}/v1/chat",
            json={
                "messages": [{"role": "user", "content": "private prompt"}],
                "capability": "chat",
            },
            timeout=2,
            trust_env=False,
        )
    finally:
        server.should_exit = True
        thread.join(timeout=2)

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert len(remote.requests) == 1
    assert "Exception in ASGI application" not in caplog.text
    assert "fake-private-endpoint.invalid" not in caplog.text
    assert "fake HTTPX transport detail" not in caplog.text


@pytest.mark.parametrize(
    ("runtime_argv", "composition_arguments"),
    [
        (
            ["--runtime", "ollama"],
            {
                "runtime": "ollama",
                "ollama_model": None,
                "ollama_disable_thinking": False,
                "llama_server_base_url": None,
                "llama_server_model": None,
            },
        ),
        (
            ["--runtime", "ollama", "--ollama-model", "configured-model"],
            {
                "runtime": "ollama",
                "ollama_model": "configured-model",
                "ollama_disable_thinking": False,
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
                "ollama_model": None,
                "ollama_disable_thinking": False,
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
        lambda *_, capabilities, local_app_composition: (
            recorded.update(
                capabilities=capabilities,
                local_app_composition=local_app_composition,
            )
            or app
        ),
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
        "composition_arguments": {
            **composition_arguments,
            "capabilities": ("chat", "summarize"),
        },
        "capabilities": ("chat", "summarize"),
        "local_app_composition": local_composition,
        "app": app,
        "host": STATIC_CLUSTER_HOST,
        "port": 25042,
    }


def test_main_passes_explicit_inline_capabilities_to_static_app(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster import static_cluster

    recorded: dict[str, object] = {}
    local_composition = object()

    def create_local_composition(**kwargs: object) -> object:
        recorded["local_capabilities"] = kwargs["capabilities"]
        recorded["ollama_disable_thinking"] = kwargs["ollama_disable_thinking"]
        return local_composition

    monkeypatch.setattr(
        static_cluster,
        "create_local_runtime_composition",
        create_local_composition,
    )
    monkeypatch.setattr(
        static_cluster,
        "create_static_cluster_app",
        lambda *_, capabilities, local_app_composition: (
            recorded.update(
                capabilities=capabilities,
                local_app_composition=local_app_composition,
            )
            or FastAPI()
        ),
    )
    monkeypatch.setattr(static_cluster.uvicorn, "run", lambda *_1, **_2: None)

    main(
        [
            "--remote-node-id",
            "operator-remote",
            "--remote-base-url",
            "https://remote.test",
            "--local-capability",
            "chat",
            "--remote-capability",
            "summarize",
            "--ollama-disable-thinking",
        ]
    )

    assert recorded == {
        "local_capabilities": ("chat",),
        "ollama_disable_thinking": True,
        "capabilities": ("summarize",),
        "local_app_composition": local_composition,
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
    collection_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: None))
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
