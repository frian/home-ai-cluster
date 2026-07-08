import asyncio
import inspect

import pytest

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.orchestrator import orchestrate_request
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    DECLARED_REMOTE_ROUTING_REASON,
    DeclaredRemoteRoutingCandidate,
    RemoteNodeDeclaration,
)
from home_ai_cluster.core.router import (
    NoMatchingAdapterError,
    RoutingDecision,
    route_request,
)
from home_ai_cluster.core.routing_candidates import (
    LocalRoutingCandidate,
    RoutingCandidates,
    RoutingCandidateSelectionMode,
    select_routing_candidate,
)


class RecordingAdapter:
    def __init__(
        self,
        name: str = "local-adapter",
        result: ClusterResult | None = None,
    ) -> None:
        self._name = name
        self._result = result or ClusterResult(content="Hello", adapter=name)
        self.chat_requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return self._name

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> ClusterResult:
        self.chat_requests.append(request)
        return self._result


class RecordingRemoteTransport:
    def __init__(self) -> None:
        self.requests: list[ClusterRequest] = []
        self.declarations: list[RemoteNodeDeclaration] = []

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        self.requests.append(request)
        self.declarations.append(declaration)
        return ClusterResult(content="Remote hello", adapter="remote")


def make_request() -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
    )


def make_node(
    node_id: str,
    adapters: list[str] | None = None,
) -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=adapters or ["adapter"],
    )


def make_local_candidate(
    adapter: RecordingAdapter | None = None,
) -> LocalRoutingCandidate:
    local_adapter = adapter or RecordingAdapter()
    return LocalRoutingCandidate(
        RoutingDecision(
            node=make_node("local", [local_adapter.name]),
            adapter=local_adapter,
            capability=Capability(name="chat"),
            reason="Selected local candidate for test.",
        )
    )


def make_declared_remote_candidate() -> DeclaredRemoteRoutingCandidate:
    declaration = RemoteNodeDeclaration(
        node=make_node("remote", ["remote-adapter"]),
        transport_address="http://remote.local:8000",
    )
    return DeclaredRemoteRoutingCandidate(
        node=declaration.node,
        declaration=declaration,
        capability=Capability(name="chat"),
        reason=DECLARED_REMOTE_ROUTING_REASON,
    )


def make_candidates(
    local: LocalRoutingCandidate | None = None,
    declared_remote: DeclaredRemoteRoutingCandidate | None = None,
) -> RoutingCandidates:
    return RoutingCandidates(local=local, declared_remote=declared_remote)


@pytest.mark.parametrize(
    ("mode", "candidates", "expected_family"),
    [
        (
            RoutingCandidateSelectionMode.LOCAL_ONLY,
            make_candidates(local=make_local_candidate()),
            "local",
        ),
        (
            RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
            make_candidates(declared_remote=make_declared_remote_candidate()),
            "declared_remote",
        ),
        (
            RoutingCandidateSelectionMode.PREFER_LOCAL,
            make_candidates(
                local=make_local_candidate(),
                declared_remote=make_declared_remote_candidate(),
            ),
            "local",
        ),
        (
            RoutingCandidateSelectionMode.PREFER_LOCAL,
            make_candidates(declared_remote=make_declared_remote_candidate()),
            "declared_remote",
        ),
        (
            RoutingCandidateSelectionMode.PREFER_DECLARED_REMOTE,
            make_candidates(
                local=make_local_candidate(),
                declared_remote=make_declared_remote_candidate(),
            ),
            "declared_remote",
        ),
        (
            RoutingCandidateSelectionMode.PREFER_DECLARED_REMOTE,
            make_candidates(local=make_local_candidate()),
            "local",
        ),
    ],
)
def test_select_routing_candidate_returns_expected_candidate(
    mode: RoutingCandidateSelectionMode,
    candidates: RoutingCandidates,
    expected_family: str,
) -> None:
    selected = select_routing_candidate(candidates, mode)

    assert selected is not None
    assert selected.mode == mode
    if expected_family == "local":
        assert selected.local is candidates.local
        assert selected.declared_remote is None
    else:
        assert selected.local is None
        assert selected.declared_remote is candidates.declared_remote


@pytest.mark.parametrize(
    ("mode", "candidates"),
    [
        (
            RoutingCandidateSelectionMode.LOCAL_ONLY,
            make_candidates(declared_remote=make_declared_remote_candidate()),
        ),
        (
            RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
            make_candidates(local=make_local_candidate()),
        ),
        (
            RoutingCandidateSelectionMode.PREFER_LOCAL,
            make_candidates(),
        ),
        (
            RoutingCandidateSelectionMode.PREFER_DECLARED_REMOTE,
            make_candidates(),
        ),
    ],
)
def test_select_routing_candidate_returns_none_when_no_candidate_matches(
    mode: RoutingCandidateSelectionMode,
    candidates: RoutingCandidates,
) -> None:
    assert select_routing_candidate(candidates, mode) is None


@pytest.mark.parametrize(
    "mode",
    [
        RoutingCandidateSelectionMode.LOCAL_ONLY,
        RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
        RoutingCandidateSelectionMode.PREFER_LOCAL,
        RoutingCandidateSelectionMode.PREFER_DECLARED_REMOTE,
    ],
)
def test_selected_candidate_never_contains_both_candidate_families(
    mode: RoutingCandidateSelectionMode,
) -> None:
    selected = select_routing_candidate(
        make_candidates(
            local=make_local_candidate(),
            declared_remote=make_declared_remote_candidate(),
        ),
        mode,
    )

    assert selected is not None
    assert (selected.local is None) != (selected.declared_remote is None)


def test_select_routing_candidate_does_not_execute_local_adapters() -> None:
    adapter = RecordingAdapter()
    candidates = make_candidates(local=make_local_candidate(adapter))

    select_routing_candidate(candidates, RoutingCandidateSelectionMode.LOCAL_ONLY)

    assert adapter.chat_requests == []


def test_select_routing_candidate_does_not_use_remote_transports() -> None:
    transport = RecordingRemoteTransport()
    signature = inspect.signature(select_routing_candidate)

    select_routing_candidate(
        make_candidates(declared_remote=make_declared_remote_candidate()),
        RoutingCandidateSelectionMode.DECLARED_REMOTE_ONLY,
    )

    assert "remote_transport" not in signature.parameters
    assert transport.requests == []
    assert transport.declarations == []


def test_select_routing_candidate_does_not_change_orchestrate_request() -> None:
    result = ClusterResult(content="Hi", adapter="local-adapter")
    adapter = RecordingAdapter(result=result)
    node = make_node("local", ["local-adapter"])

    actual = asyncio.run(
        orchestrate_request(
            make_request(),
            NodeRegistry([node]),
            AdapterRegistry([adapter]),
        )
    )

    assert list(inspect.signature(orchestrate_request).parameters) == [
        "request",
        "node_registry",
        "adapter_registry",
    ]
    assert actual is result
    assert adapter.chat_requests == [make_request()]


def test_select_routing_candidate_does_not_change_route_request() -> None:
    node = make_node("local", ["missing-local-adapter"])

    assert list(inspect.signature(route_request).parameters) == [
        "request",
        "node_registry",
        "adapter_registry",
    ]
    with pytest.raises(
        NoMatchingAdapterError,
        match="No adapter provides capability on available node: chat",
    ):
        route_request(make_request(), NodeRegistry([node]), AdapterRegistry())
