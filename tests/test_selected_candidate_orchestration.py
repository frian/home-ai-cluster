import asyncio
import inspect

import pytest

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
)
from home_ai_cluster.core.orchestrator import (
    InvalidSelectedRoutingCandidateError,
    MissingRemoteTransportError,
    orchestrate_request,
    orchestrate_request_with_selected_candidate,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    DECLARED_REMOTE_ROUTING_REASON,
    DeclaredRemoteRoutingCandidate,
    RemoteNodeDeclaration,
)
from home_ai_cluster.core.remote_transport import RemoteTransportError
from home_ai_cluster.core.router import (
    NoMatchingAdapterError,
    RoutingDecision,
    route_request,
)
from home_ai_cluster.core.routing_candidates import (
    LocalRoutingCandidate,
    RoutingCandidateSelectionMode,
    SelectedRoutingCandidate,
)


class RecordingAdapter:
    def __init__(
        self,
        result: RuntimeResult | None = None,
        error: RuntimeAdapterUnavailableError | None = None,
    ) -> None:
        self._result = result or RuntimeResult(content="Local hello", adapter="local")
        self._error = error
        self.chat_requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return "local"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.chat_requests.append(request)

        if self._error is not None:
            raise self._error

        return self._result


class RecordingRemoteTransport:
    def __init__(
        self,
        result: ClusterResult | None = None,
        error: RemoteTransportError | None = None,
    ) -> None:
        self._result = result or ClusterResult(
            content="Remote hello",
            adapter="remote",
            node_id="remote-response",
        )
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

        return self._result


def make_request() -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
    )


def make_node(node_id: str, adapter_name: str = "local") -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=[adapter_name],
    )


def make_local_candidate(
    adapter: RecordingAdapter | None = None,
) -> LocalRoutingCandidate:
    local_adapter = adapter or RecordingAdapter()
    return LocalRoutingCandidate(
        decision=RoutingDecision(
            node=make_node("local", local_adapter.name),
            adapter=local_adapter,
            capability=Capability(name="chat"),
            reason="Selected local candidate for test.",
        )
    )


def make_declared_remote_candidate(
    node_id: str = "remote",
) -> DeclaredRemoteRoutingCandidate:
    declaration = RemoteNodeDeclaration(
        node=make_node(node_id, "remote-adapter"),
        transport_address=f"http://{node_id}.local:8000",
    )
    return DeclaredRemoteRoutingCandidate(
        node=declaration.node,
        declaration=declaration,
        capability=Capability(name="chat"),
        reason=DECLARED_REMOTE_ROUTING_REASON,
    )


def make_selected_local(
    adapter: RecordingAdapter | None = None,
) -> SelectedRoutingCandidate:
    return SelectedRoutingCandidate(
        local=make_local_candidate(adapter),
        declared_remote=None,
        mode=RoutingCandidateSelectionMode.LOCAL_ONLY,
    )


def make_selected_declared_remote() -> SelectedRoutingCandidate:
    return SelectedRoutingCandidate(
        local=None,
        declared_remote=make_declared_remote_candidate(),
        mode=RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
    )


def test_local_selected_candidate_executes_through_local_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.core import orchestrator as orchestrator_module

    request = make_request()
    selected = make_selected_local()
    result = ClusterResult(content="Boundary local", adapter="local", node_id="local")
    calls: list[tuple[ClusterRequest, RoutingDecision]] = []

    async def execute_local(
        received_request: ClusterRequest,
        decision: RoutingDecision,
    ) -> ClusterResult:
        calls.append((received_request, decision))
        return result

    monkeypatch.setattr(
        orchestrator_module,
        "execute_local_routing_decision",
        execute_local,
    )

    actual = asyncio.run(orchestrate_request_with_selected_candidate(request, selected))

    assert actual is result
    assert calls == [(request, selected.local.decision)]


def test_local_selected_candidate_does_not_require_remote_transport() -> None:
    adapter = RecordingAdapter()
    request = make_request()

    actual = asyncio.run(
        orchestrate_request_with_selected_candidate(
            request,
            make_selected_local(adapter),
        )
    )

    assert actual.adapter == "local"
    assert adapter.chat_requests == [request]


def test_declared_remote_selected_candidate_requires_explicit_transport() -> None:
    with pytest.raises(
        MissingRemoteTransportError,
        match="requires RemoteTransport",
    ):
        asyncio.run(
            orchestrate_request_with_selected_candidate(
                make_request(),
                make_selected_declared_remote(),
            )
        )


def test_declared_remote_selected_candidate_executes_through_remote_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.core import orchestrator as orchestrator_module

    request = make_request()
    selected = make_selected_declared_remote()
    transport = RecordingRemoteTransport()
    result = ClusterResult(
        content="Boundary remote", adapter="remote", node_id="remote"
    )
    calls: list[
        tuple[
            ClusterRequest,
            DeclaredRemoteRoutingCandidate,
            RecordingRemoteTransport,
        ]
    ] = []

    async def execute_remote(
        received_request: ClusterRequest,
        candidate: DeclaredRemoteRoutingCandidate,
        received_transport: RecordingRemoteTransport,
    ) -> ClusterResult:
        calls.append((received_request, candidate, received_transport))
        return result

    monkeypatch.setattr(
        orchestrator_module,
        "execute_declared_remote_routing_candidate",
        execute_remote,
    )

    actual = asyncio.run(
        orchestrate_request_with_selected_candidate(
            request,
            selected,
            remote_transport=transport,
        )
    )

    assert actual is result
    assert calls == [(request, selected.declared_remote, transport)]


def test_declared_remote_selected_candidate_uses_transport() -> None:
    request = make_request()
    selected = make_selected_declared_remote()
    transport = RecordingRemoteTransport()

    actual = asyncio.run(
        orchestrate_request_with_selected_candidate(
            request,
            selected,
            remote_transport=transport,
        )
    )

    assert actual.adapter == "remote"
    assert transport.requests == [request]
    assert transport.declarations == [selected.declared_remote.declaration]


@pytest.mark.parametrize(
    "selected",
    [
        None,
        SelectedRoutingCandidate(
            local=None,
            declared_remote=None,
            mode=RoutingCandidateSelectionMode.LOCAL_ONLY,
        ),
        SelectedRoutingCandidate(
            local=make_local_candidate(),
            declared_remote=make_declared_remote_candidate(),
            mode=RoutingCandidateSelectionMode.PREFER_LOCAL,
        ),
    ],
)
def test_missing_or_invalid_selected_candidate_fails_explicitly(
    selected: SelectedRoutingCandidate | None,
) -> None:
    with pytest.raises(InvalidSelectedRoutingCandidateError):
        asyncio.run(
            orchestrate_request_with_selected_candidate(
                make_request(),
                selected,  # type: ignore[arg-type]
            )
        )


def test_helper_does_not_call_route_request(monkeypatch: pytest.MonkeyPatch) -> None:
    from home_ai_cluster.core import orchestrator as orchestrator_module

    def fail_route_request(*args: object) -> NoMatchingAdapterError:
        raise AssertionError("route_request must not be called")

    monkeypatch.setattr(orchestrator_module, "route_request", fail_route_request)

    actual = asyncio.run(
        orchestrate_request_with_selected_candidate(
            make_request(),
            make_selected_local(),
        )
    )

    assert actual.adapter == "local"


def test_helper_does_not_rerun_discovery_or_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.core import routing_candidates as routing_candidates_module

    def fail_discovery(*args: object) -> None:
        raise AssertionError("candidate discovery must not be called")

    def fail_selection(*args: object) -> None:
        raise AssertionError("candidate selection must not be called")

    monkeypatch.setattr(
        routing_candidates_module,
        "routing_candidates_for_request",
        fail_discovery,
    )
    monkeypatch.setattr(
        routing_candidates_module,
        "select_routing_candidate",
        fail_selection,
    )

    actual = asyncio.run(
        orchestrate_request_with_selected_candidate(
            make_request(),
            make_selected_local(),
        )
    )

    assert actual.adapter == "local"


def test_helper_does_not_retry_or_fallback_from_local_failure() -> None:
    error = RuntimeAdapterUnavailableError("local failed")
    adapter = RecordingAdapter(error=error)
    transport = RecordingRemoteTransport()

    with pytest.raises(RuntimeAdapterUnavailableError) as raised:
        asyncio.run(
            orchestrate_request_with_selected_candidate(
                make_request(),
                make_selected_local(adapter),
                remote_transport=transport,
            )
        )

    assert raised.value is error
    assert transport.requests == []
    assert transport.declarations == []


def test_helper_does_not_retry_or_fallback_from_remote_failure() -> None:
    error = RemoteTransportError("remote failed")
    transport = RecordingRemoteTransport(error=error)

    with pytest.raises(RemoteTransportError) as raised:
        asyncio.run(
            orchestrate_request_with_selected_candidate(
                make_request(),
                make_selected_declared_remote(),
                remote_transport=transport,
            )
        )

    assert raised.value is error
    assert transport.requests == [make_request()]


def test_helper_does_not_change_v1_chat_or_active_orchestrator() -> None:
    import home_ai_cluster.api.routes as routes

    result = RuntimeResult(content="Active local", adapter="local")
    adapter = RecordingAdapter(result=result)
    node = make_node("local", adapter.name)
    request = make_request()

    actual = asyncio.run(
        orchestrate_request(
            request,
            NodeRegistry([node]),
            AdapterRegistry([adapter]),
        )
    )

    chat_routes = [
        route
        for route in routes.router.routes
        if getattr(route, "path", None) == "/v1/chat"
    ]

    assert len(chat_routes) == 1
    assert getattr(chat_routes[0], "methods", set()) == {"POST"}
    assert list(inspect.signature(orchestrate_request).parameters) == [
        "request",
        "node_registry",
        "adapter_registry",
    ]
    assert list(inspect.signature(route_request).parameters) == [
        "request",
        "node_registry",
        "adapter_registry",
    ]
    assert actual.content == result.content
    assert actual.node_id == "local"
    assert adapter.chat_requests == [request]
