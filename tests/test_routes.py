import asyncio

import httpx
import pytest
from pydantic import ValidationError

from home_ai_cluster.adapters.base import (
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.api.routes import InternalClusterStatusResponse
from home_ai_cluster.api.wiring import (
    build_static_remote_collection_wiring,
    build_static_remote_wiring,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClassifyRequest,
    ClassifyResult,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
    SummarizeRequest,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode
from home_ai_cluster.main import create_app


class RecordingChatAdapter:
    def __init__(self) -> None:
        self.requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return "test"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.requests.append(request)
        user_messages = [
            message.content for message in request.messages if message.role == "user"
        ]
        content = user_messages[-1] if user_messages else request.messages[-1].content

        return RuntimeResult(content=content, adapter=self.name)


class RecordingSummarizeAdapter:
    def __init__(self) -> None:
        self.requests: list[SummarizeRequest] = []

    @property
    def name(self) -> str:
        return "summarize-test"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="summarize")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        raise AssertionError("summarize adapter must not receive chat")

    async def summarize(self, request: SummarizeRequest) -> RuntimeResult:
        self.requests.append(request)
        return RuntimeResult(content="summary", adapter=self.name, model="test-model")


class RecordingClassifyAdapter:
    def __init__(self, proposal: str) -> None:
        self.proposal = proposal
        self.requests: list[ClassifyRequest] = []
        self.chat_calls = 0
        self.summarize_calls = 0

    @property
    def name(self) -> str:
        return "classify-test"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="classify")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.chat_calls += 1
        raise AssertionError("classify adapter must not receive chat")

    async def summarize(self, request: SummarizeRequest) -> RuntimeResult:
        self.summarize_calls += 1
        raise AssertionError("classify adapter must not receive summarize")

    async def classify(self, request: ClassifyRequest) -> str:
        self.requests.append(request)
        return self.proposal


class UnavailableSummarizeAdapter(RecordingSummarizeAdapter):
    async def summarize(self, request: SummarizeRequest) -> RuntimeResult:
        raise RuntimeAdapterUnavailableError("private runtime detail")


class UnavailableClassifyAdapter(RecordingClassifyAdapter):
    async def classify(self, request: ClassifyRequest) -> str:
        self.requests.append(request)
        raise RuntimeAdapterUnavailableError("private runtime detail")


class UnavailableChatAdapter(RecordingChatAdapter):
    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        raise RuntimeAdapterUnavailableError("Runtime adapter unavailable")


class RuntimeSpecificUnavailableChatAdapter(RecordingChatAdapter):
    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        cause = RuntimeError("ollama connection refused on localhost:11434")
        raise RuntimeAdapterUnavailableError("ollama leaked detail") from cause


class StatusAdapter:
    def __init__(self, health_result: AdapterHealth | Exception) -> None:
        self._health_result = health_result
        self.health_calls = 0
        self.chat_calls = 0

    @property
    def name(self) -> str:
        return "private-adapter-name"

    def health(self) -> AdapterHealth:
        self.health_calls += 1
        if isinstance(self._health_result, Exception):
            raise self._health_result
        return self._health_result

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.chat_calls += 1
        raise AssertionError("status endpoint must not execute chat")


def create_test_registry() -> AdapterRegistry:
    return AdapterRegistry([RecordingChatAdapter()])


def create_unavailable_registry() -> AdapterRegistry:
    return AdapterRegistry([UnavailableChatAdapter()])


def create_runtime_specific_unavailable_registry() -> AdapterRegistry:
    return AdapterRegistry([RuntimeSpecificUnavailableChatAdapter()])


def create_test_node_registry() -> NodeRegistry:
    return NodeRegistry(
        [
            NodeDescription(
                id="local",
                name="Local node",
                availability="available",
                health=NodeHealth(healthy=True),
                capabilities=[Capability(name="chat")],
                adapters=["test"],
            )
        ]
    )


def create_status_node_registry() -> NodeRegistry:
    return NodeRegistry(
        [
            NodeDescription(
                id="private-machine-name",
                name="Private machine name",
                availability="available",
                health=NodeHealth(healthy=True),
                capabilities=[Capability(name="chat")],
                adapters=["private-adapter-name"],
            )
        ]
    )


async def post_async(path: str, payload: dict[str, object]) -> httpx.Response:
    transport = httpx.ASGITransport(app=create_app())

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.post(path, json=payload)


async def post_chat_async(payload: dict[str, object]) -> httpx.Response:
    return await post_async("/v1/chat", payload)


async def post_summarize_async(payload: object) -> httpx.Response:
    return await post_async("/v1/summarize", payload)  # type: ignore[arg-type]


async def post_classify_async(payload: object) -> httpx.Response:
    return await post_async("/v1/classify", payload)  # type: ignore[arg-type]


def post_summarize(payload: object) -> httpx.Response:
    return asyncio.run(post_summarize_async(payload))


def post_classify(payload: object) -> httpx.Response:
    return asyncio.run(post_classify_async(payload))


def post_chat(payload: dict[str, object]) -> httpx.Response:
    return asyncio.run(post_chat_async(payload))


async def post_internal_cluster_request_async(
    payload: dict[str, object],
) -> httpx.Response:
    return await post_async("/internal/cluster/request", payload)


def post_internal_cluster_request(payload: dict[str, object]) -> httpx.Response:
    return asyncio.run(post_internal_cluster_request_async(payload))


async def get_internal_cluster_status_async() -> httpx.Response:
    transport = httpx.ASGITransport(app=create_app())

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.get("/internal/cluster/status")


def get_internal_cluster_status() -> httpx.Response:
    return asyncio.run(get_internal_cluster_status_async())


@pytest.fixture
def use_test_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    from home_ai_cluster.api import routes

    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        create_test_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_test_node_registry,
    )


def test_chat_endpoint_returns_cluster_result_json(use_test_registry: None) -> None:
    response = post_chat(
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": "chat",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "content": "Hello",
        "adapter": "test",
        "model": None,
        "node_id": "local",
    }
    assert "reason" not in response.json()
    assert "node" not in response.json()
    assert "selected_node" not in response.json()
    assert "routing" not in response.json()
    assert "health" not in response.json()


def test_summarize_endpoint_executes_local_adapter_and_preserves_text(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    from home_ai_cluster.api import routes
    from home_ai_cluster.request_history import history_file

    adapter = RecordingSummarizeAdapter()
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    node_registry = NodeRegistry(
        [
            NodeDescription(
                id="selected-local",
                name="Selected local node",
                availability="available",
                health=NodeHealth(healthy=True),
                capabilities=[Capability(name="summarize")],
                adapters=[adapter.name],
            )
        ]
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        lambda: node_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = post_summarize({"text": "  Source\n</source> text  "})

    assert response.status_code == 200
    assert response.json() == {
        "content": "summary",
        "adapter": "summarize-test",
        "model": "test-model",
        "node_id": "selected-local",
    }
    assert adapter.requests == [SummarizeRequest(text="  Source\n</source> text  ")]
    assert not history_file().exists()


def test_summarize_endpoint_ignores_public_extra_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    adapter = RecordingSummarizeAdapter()
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        lambda: NodeRegistry(
            [
                NodeDescription(
                    id="local",
                    name="Local node",
                    availability="available",
                    health=NodeHealth(healthy=True),
                    capabilities=[Capability(name="summarize")],
                    adapters=[adapter.name],
                )
            ]
        ),
    )

    response = post_summarize(
        {"text": "Source", "capability": "chat", "messages": [{"role": "user"}]}
    )

    assert response.status_code == 200
    assert adapter.requests == [SummarizeRequest(text="Source")]


@pytest.mark.parametrize(
    "payload",
    [{}, {"text": 42}, {"text": "   "}, {"text": "a" * 65_537}],
)
def test_summarize_endpoint_returns_uniform_validation_error(payload: object) -> None:
    response = post_summarize(payload)

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid summarize request"}
    assert "a" * 64 not in response.text


def test_summarize_endpoint_returns_uniform_error_for_malformed_json() -> None:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.post("/v1/summarize", content=b'{"text":')

    response = asyncio.run(send())

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid summarize request"}


def test_summarize_endpoint_excludes_chat_only_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    adapter = RecordingChatAdapter()
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_test_node_registry,
    )

    response = post_summarize({"text": "Source"})

    assert response.status_code == 404
    assert response.json() == {"detail": "No adapter provides capability: summarize"}
    assert adapter.requests == []


def test_invalid_summarize_request_does_not_invoke_adapter(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    from home_ai_cluster.api import routes
    from home_ai_cluster.request_history import history_file

    adapter = RecordingSummarizeAdapter()
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    node = NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="summarize")],
        adapters=[adapter.name],
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        lambda: NodeRegistry([node]),
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = post_summarize({"text": "\n\t"})

    assert response.status_code == 422
    assert adapter.requests == []
    assert not history_file().exists()


def test_summarize_endpoint_returns_runtime_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    adapter = UnavailableSummarizeAdapter()
    node = NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="summarize")],
        adapters=[adapter.name],
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        lambda: NodeRegistry([node]),
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = post_summarize({"text": "Source"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Runtime adapter unavailable"}
    assert "private runtime detail" not in response.text


def test_summarize_endpoint_uses_eligible_declared_remote_when_local_is_chat_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    from home_ai_cluster.request_history import history_file

    class RecordingRemoteTransport:
        def __init__(self) -> None:
            self.requests: list[SummarizeRequest] = []

        async def send(
            self,
            request: ClusterRequest | SummarizeRequest,
            declaration: RemoteNodeDeclaration,
        ) -> ClusterResult:
            assert isinstance(request, SummarizeRequest)
            self.requests.append(request)
            return ClusterResult(
                content="remote summary",
                adapter="remote-adapter",
                model="remote-model",
                node_id="untrusted-receiver-id",
            )

    local = RecordingChatAdapter()
    declaration = RemoteNodeDeclaration(
        node=NodeDescription(
            id="declared-remote",
            name="Declared remote",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="summarize")],
            adapters=["remote-adapter"],
        ),
        transport_address="http://remote.example:8000",
    )
    transport = RecordingRemoteTransport()
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    wiring = build_static_remote_wiring(
        node_registry=NodeRegistry(
            [
                NodeDescription(
                    id="local",
                    name="Local node",
                    availability="available",
                    health=NodeHealth(healthy=True),
                    capabilities=[Capability(name="chat")],
                    adapters=[local.name],
                )
            ]
        ),
        adapter_registry=AdapterRegistry([local]),
        remote_declaration=declaration,
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )

    async def send() -> httpx.Response:
        app = create_app(static_remote_wiring=wiring)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            return await client.post("/v1/summarize", json={"text": "  Source  "})

    response = asyncio.run(send())

    assert response.status_code == 200
    assert response.json() == {
        "content": "remote summary",
        "adapter": "remote-adapter",
        "model": "remote-model",
        "node_id": "declared-remote",
    }
    assert transport.requests == [
        SummarizeRequest(
            text="  Source  ",
            constraints={"local_only": False},
        )
    ]
    assert local.requests == []
    assert not history_file().exists()


def test_classify_endpoint_executes_local_adapter_with_exact_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    adapter = RecordingClassifyAdapter(" Personal ")
    node = NodeDescription(
        id="selected-local",
        name="Selected local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="classify")],
        adapters=[adapter.name],
    )
    monkeypatch.setattr(
        routes, "create_static_local_node_registry", lambda: NodeRegistry([node])
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )
    labels = ["invoice", " Personal ", "Résumé"]

    response = post_classify({"text": "  Source\ntext  ", "labels": labels})

    assert response.status_code == 200
    assert response.json() == {
        "selected_label": " Personal ",
        "node_id": "selected-local",
    }
    assert adapter.requests == [ClassifyRequest(text="  Source\ntext  ", labels=labels)]
    assert adapter.chat_calls == 0
    assert adapter.summarize_calls == 0


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"text": "Source"},
        {"text": "   ", "labels": ["invoice", "personal"]},
        {"text": "a" * 65_537, "labels": ["invoice", "personal"]},
        {"text": "Source", "labels": ["invoice"]},
        {"text": "Source", "labels": ["a"] * 33},
        {"text": "Source", "labels": ["invoice", ""]},
        {"text": "Source", "labels": ["invoice", "é" * 65]},
        {"text": "Source", "labels": ["invoice", "invoice"]},
        {"text": "Source", "labels": ["invoice", 2]},
        [],
    ],
)
def test_classify_endpoint_returns_uniform_validation_error_without_execution(
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
) -> None:
    from home_ai_cluster.api import routes

    adapter = RecordingClassifyAdapter("invoice")
    node = NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="classify")],
        adapters=[adapter.name],
    )
    monkeypatch.setattr(
        routes, "create_static_local_node_registry", lambda: NodeRegistry([node])
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = post_classify(payload)

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid classify request"}
    assert adapter.requests == []


def test_classify_endpoint_returns_uniform_error_for_malformed_json() -> None:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.post("/v1/classify", content=b'{"text":')

    response = asyncio.run(send())

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid classify request"}


def test_classify_endpoint_excludes_local_candidate_without_classify(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    adapter = RecordingChatAdapter()
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_test_node_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = post_classify({"text": "Source", "labels": ["invoice", "personal"]})

    assert response.status_code == 404
    assert response.json() == {"detail": "No adapter provides capability: classify"}
    assert adapter.requests == []


def test_classify_endpoint_returns_safe_runtime_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    adapter = UnavailableClassifyAdapter("invoice")
    node = NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="classify")],
        adapters=[adapter.name],
    )
    monkeypatch.setattr(
        routes, "create_static_local_node_registry", lambda: NodeRegistry([node])
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = post_classify({"text": "Source", "labels": ["invoice", "personal"]})

    assert response.status_code == 503
    assert response.json() == {"detail": "Runtime adapter unavailable"}
    assert "private runtime detail" not in response.text


def test_classify_endpoint_returns_safe_invalid_proposal_without_fallback() -> None:
    adapter = RecordingClassifyAdapter("private proposal")
    local = NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="classify")],
        adapters=[adapter.name],
    )
    declaration = RemoteNodeDeclaration(
        node=NodeDescription(
            id="remote",
            name="Declared remote",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="classify")],
            adapters=["remote"],
        ),
        transport_address="http://remote.example:8000",
    )

    class RemoteTransport:
        calls = 0

        async def send(
            self, request: ClassifyRequest, _: RemoteNodeDeclaration
        ) -> ClassifyResult:
            self.calls += 1
            return ClassifyResult(selected_label="invoice", node_id="receiver")

    transport = RemoteTransport()
    wiring = build_static_remote_wiring(
        node_registry=NodeRegistry([local]),
        adapter_registry=AdapterRegistry([adapter]),
        remote_declaration=declaration,
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )

    async def send() -> httpx.Response:
        app = create_app(static_remote_wiring=wiring)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as client:
            return await client.post(
                "/v1/classify",
                json={"text": "Source", "labels": ["invoice", "personal"]},
            )

    response = asyncio.run(send())

    assert response.status_code == 500
    assert response.json() == {"detail": "execution-failed"}
    assert "private proposal" not in response.text
    assert adapter.requests == [
        ClassifyRequest(
            text="Source",
            labels=["invoice", "personal"],
            constraints={"local_only": False},
        )
    ]
    assert transport.calls == 0


def test_classify_endpoint_uses_eligible_declared_remote_with_exact_request() -> None:
    local = RecordingChatAdapter()
    declaration = RemoteNodeDeclaration(
        node=NodeDescription(
            id="declared-remote",
            name="Declared remote",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="classify")],
            adapters=["remote"],
        ),
        transport_address="http://remote.example:8000",
    )

    class RemoteTransport:
        def __init__(self) -> None:
            self.requests: list[ClassifyRequest] = []

        async def send(
            self, request: ClassifyRequest, _: RemoteNodeDeclaration
        ) -> ClassifyResult:
            self.requests.append(request)
            return ClassifyResult(selected_label="Résumé", node_id="receiver")

    transport = RemoteTransport()
    wiring = build_static_remote_wiring(
        node_registry=NodeRegistry(
            [
                NodeDescription(
                    id="local",
                    name="Local node",
                    availability="available",
                    health=NodeHealth(healthy=True),
                    capabilities=[Capability(name="chat")],
                    adapters=[local.name],
                )
            ]
        ),
        adapter_registry=AdapterRegistry([local]),
        remote_declaration=declaration,
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )

    async def send() -> httpx.Response:
        app = create_app(static_remote_wiring=wiring)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            return await client.post(
                "/v1/classify",
                json={"text": "Source", "labels": ["invoice", "Résumé"]},
            )

    response = asyncio.run(send())

    assert response.status_code == 200
    assert response.json() == {
        "selected_label": "Résumé",
        "node_id": "declared-remote",
    }
    assert transport.requests == [
        ClassifyRequest(
            text="Source",
            labels=["invoice", "Résumé"],
            constraints={"local_only": False},
        )
    ]
    assert local.requests == []


def test_classify_endpoint_falls_through_ordered_eligible_remotes_once() -> None:
    local = RecordingChatAdapter()

    def declaration(node_id: str, capability: str) -> RemoteNodeDeclaration:
        return RemoteNodeDeclaration(
            node=NodeDescription(
                id=node_id,
                name=f"Declared {node_id}",
                availability="available",
                health=NodeHealth(healthy=True),
                capabilities=[Capability(name=capability)],
                adapters=["remote"],
            ),
            transport_address=f"http://{node_id}.example:8000",
        )

    class RemoteTransport:
        def __init__(self) -> None:
            self.attempts: list[str] = []

        async def send(
            self, request: ClassifyRequest, remote: RemoteNodeDeclaration
        ) -> ClassifyResult:
            self.attempts.append(remote.node.id)
            assert request.labels == ["invoice", "personal"]
            if remote.node.id == "first":
                raise RuntimeConnectionUnavailableBeforeRequestError("unavailable")
            return ClassifyResult(selected_label="personal", node_id="receiver")

    transport = RemoteTransport()
    wiring = build_static_remote_collection_wiring(
        node_registry=NodeRegistry(
            [
                NodeDescription(
                    id="local",
                    name="Local node",
                    availability="available",
                    health=NodeHealth(healthy=True),
                    capabilities=[Capability(name="chat")],
                    adapters=[local.name],
                )
            ]
        ),
        adapter_registry=AdapterRegistry([local]),
        remote_declarations=[
            declaration("chat-only", "chat"),
            declaration("first", "classify"),
            declaration("second", "classify"),
        ],
        remote_transport=transport,
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )

    async def send() -> httpx.Response:
        app = create_app(static_remote_collection_wiring=wiring)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            return await client.post(
                "/v1/classify",
                json={"text": "Source", "labels": ["invoice", "personal"]},
            )

    response = asyncio.run(send())

    assert response.status_code == 200
    assert response.json() == {"selected_label": "personal", "node_id": "second"}
    assert transport.attempts == ["first", "second"]
    assert local.requests == []


def test_chat_endpoint_uses_last_user_message(use_test_registry: None) -> None:
    response = post_chat(
        {
            "messages": [
                {"role": "user", "content": "First"},
                {"role": "assistant", "content": "Middle"},
                {"role": "user", "content": "Second"},
            ],
            "capability": "chat",
        },
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Second"


def test_chat_endpoint_rejects_unsupported_capability(
    use_test_registry: None,
) -> None:
    response = post_chat(
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": "embeddings",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No adapter provides capability: embeddings",
    }


def test_chat_endpoint_returns_503_when_runtime_adapter_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        create_unavailable_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_test_node_registry,
    )
    response = post_chat(
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": "chat",
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Runtime adapter unavailable"}


def test_chat_endpoint_hides_runtime_specific_unavailable_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        create_runtime_specific_unavailable_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_test_node_registry,
    )
    response = post_chat(
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "capability": "chat",
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Runtime adapter unavailable"}
    assert "ollama" not in response.text
    assert "localhost:11434" not in response.text
    assert "connection refused" not in response.text


def test_internal_cluster_request_endpoint_accepts_normalized_cluster_request(
    use_test_registry: None,
) -> None:
    response = post_internal_cluster_request(
        {
            "kind": "chat",
            "request": {
                "messages": [{"role": "user", "content": "Hello internal"}],
                "capability": {"name": "chat"},
                "constraints": {"local_only": True},
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "content": "Hello internal",
        "adapter": "test",
        "model": None,
        "node_id": "local",
    }


def test_internal_cluster_request_endpoint_rejects_unsupported_capability(
    use_test_registry: None,
) -> None:
    response = post_internal_cluster_request(
        {
            "kind": "chat",
            "request": {
                "messages": [{"role": "user", "content": "Hello"}],
                "capability": {"name": "embeddings"},
            },
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No adapter provides capability: embeddings",
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"messages": [{"role": "user", "content": "old body"}]},
        {"kind": "unknown", "request": {}},
        {"kind": "chat"},
        {"request": {}},
        {"kind": "chat", "request": {}, "extra": True},
        {"kind": "chat", "request": {"text": "source"}},
        {"kind": "summarize", "request": {"messages": []}},
        {"kind": "summarize", "request": {"text": "source", "extra": True}},
        {"kind": "summarize", "request": {"text": "\n\t"}},
        {"kind": "summarize", "request": {"text": "a" * 65_537}},
    ],
)
def test_internal_cluster_request_rejects_invalid_envelopes(payload: object) -> None:
    response = post_internal_cluster_request(payload)  # type: ignore[arg-type]

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid internal cluster request"}
    assert "old body" not in response.text


def test_internal_cluster_request_rejects_malformed_json() -> None:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.post("/internal/cluster/request", content=b'{"kind":')

    response = asyncio.run(send())

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid internal cluster request"}


def test_internal_cluster_request_executes_tagged_summarize_locally(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    from home_ai_cluster.api import routes
    from home_ai_cluster.request_history import history_file

    adapter = RecordingSummarizeAdapter()
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    node = NodeDescription(
        id="receiver-local",
        name="Receiver local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="summarize")],
        adapters=[adapter.name],
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        lambda: NodeRegistry([node]),
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = post_internal_cluster_request(
        {
            "kind": "summarize",
            "request": {"text": "  Source\n</source>  ", "constraints": {}},
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "content": "summary",
        "adapter": "summarize-test",
        "model": "test-model",
        "node_id": "receiver-local",
    }
    assert adapter.requests == [SummarizeRequest(text="  Source\n</source>  ")]
    assert not history_file().exists()


def test_internal_cluster_request_executes_classify_locally(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    adapter = RecordingClassifyAdapter(" invoice")
    node = NodeDescription(
        id="receiver-local",
        name="Receiver local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="classify")],
        adapters=[adapter.name],
    )
    monkeypatch.setattr(
        routes, "create_static_local_node_registry", lambda: NodeRegistry([node])
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = post_internal_cluster_request(
        {
            "kind": "classify",
            "request": {
                "text": "Source text étiquette",
                "labels": ["invoice", "Invoice", " invoice", "étiquette"],
            },
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "selected_label": " invoice",
        "node_id": "receiver-local",
    }
    assert adapter.requests == [
        ClassifyRequest(
            text="Source text étiquette",
            labels=["invoice", "Invoice", " invoice", "étiquette"],
        )
    ]
    assert adapter.chat_calls == 0
    assert adapter.summarize_calls == 0


def test_internal_cluster_request_maps_invalid_classify_proposal_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    adapter = RecordingClassifyAdapter("private proposal")
    node = NodeDescription(
        id="receiver",
        name="Receiver",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="classify")],
        adapters=[adapter.name],
    )
    monkeypatch.setattr(
        routes, "create_static_local_node_registry", lambda: NodeRegistry([node])
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = post_internal_cluster_request(
        {
            "kind": "classify",
            "request": {"text": "private source", "labels": ["invoice", "personal"]},
        }
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "execution-failed"}
    assert adapter.requests == [
        ClassifyRequest(text="private source", labels=["invoice", "personal"])
    ]
    assert "private proposal" not in response.text
    assert "invoice" not in response.text
    assert "private source" not in response.text


@pytest.mark.parametrize(
    "payload",
    [
        {"kind": "classify"},
        {"kind": "classify", "request": {"labels": ["a", "b"]}},
        {"kind": "classify", "request": {"text": " ", "labels": ["a", "b"]}},
        {"kind": "classify", "request": {"text": "a" * 65_537, "labels": ["a", "b"]}},
        {"kind": "classify", "request": {"text": "x"}},
        {"kind": "classify", "request": {"text": "x", "labels": ["a"]}},
        {
            "kind": "classify",
            "request": {"text": "x", "labels": [str(i) for i in range(33)]},
        },
        {"kind": "classify", "request": {"text": "x", "labels": ["a", ""]}},
        {"kind": "classify", "request": {"text": "x", "labels": ["a", "é" * 65]}},
        {"kind": "classify", "request": {"text": "x", "labels": ["a", "a"]}},
        {"kind": "classify", "request": {"text": "x", "labels": ["a", 2]}},
        {
            "kind": "classify",
            "request": {"text": "x", "labels": ["a", "b"], "extra": True},
        },
        {"kind": "unknown", "request": {}},
    ],
)
def test_internal_cluster_request_rejects_malformed_classify_before_execution(
    monkeypatch: pytest.MonkeyPatch, payload: dict[str, object]
) -> None:
    from home_ai_cluster.api import routes

    adapter = RecordingClassifyAdapter("invoice")
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = post_internal_cluster_request(payload)

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid internal cluster request"}
    assert adapter.requests == []


@pytest.mark.parametrize(
    ("health_result", "expected_runtime_status"),
    [
        (AdapterHealth(available=True), "available"),
        (AdapterHealth(available=False), "unavailable"),
        (
            RuntimeError("http://private-host:11434 authorization=secret"),
            "observation-failed",
        ),
    ],
)
def test_internal_cluster_status_returns_one_normalized_local_observation(
    monkeypatch: pytest.MonkeyPatch,
    health_result: AdapterHealth | Exception,
    expected_runtime_status: str,
) -> None:
    from home_ai_cluster.api import routes

    adapter = StatusAdapter(health_result)
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_status_node_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = get_internal_cluster_status()

    assert response.status_code == 200
    assert response.json() == {"runtime_status": expected_runtime_status}
    assert adapter.health_calls == 1
    assert adapter.chat_calls == 0


def test_internal_cluster_status_hides_local_runtime_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    adapter = StatusAdapter(
        RuntimeError("http://private-host:11434 authorization=secret")
    )
    monkeypatch.setattr(
        routes,
        "create_static_local_node_registry",
        create_status_node_registry,
    )
    monkeypatch.setattr(
        routes,
        "create_static_runtime_adapter_registry",
        lambda: AdapterRegistry([adapter]),
    )

    response = get_internal_cluster_status()

    assert set(response.json()) == {"runtime_status"}
    assert response.json() == {"runtime_status": "observation-failed"}
    for forbidden in (
        "private-machine-name",
        "Private machine name",
        "private-adapter-name",
        "private-host",
        "authorization",
        "secret",
        "node_id",
        "application_status",
        "declaration_status",
        "reason",
        "model",
        "url",
    ):
        assert forbidden not in response.text


def test_internal_cluster_status_returns_safe_error_when_snapshot_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.api import routes

    def fail_snapshot(*_: object, **__: object) -> dict[str, object]:
        raise RuntimeError("http://private-host:11434 authorization=secret")

    monkeypatch.setattr(routes, "project_health_snapshot", fail_snapshot)

    response = get_internal_cluster_status()

    assert response.status_code == 500
    assert response.json() == {"detail": "Unable to inspect local runtime status"}
    assert "private-host" not in response.text
    assert "authorization" not in response.text


def test_internal_cluster_status_response_is_closed_and_immutable() -> None:
    response = InternalClusterStatusResponse(runtime_status="available")

    with pytest.raises(ValidationError):
        InternalClusterStatusResponse(
            runtime_status="unknown",
            node_id="local",
        )
    with pytest.raises(ValidationError):
        response.runtime_status = "unavailable"  # type: ignore[misc]
