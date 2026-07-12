import asyncio

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
    RequestConstraints,
    RuntimeResult,
)
from home_ai_cluster.core.orchestrator import (
    NoSelectableRoutingCandidateError,
    orchestrate_request_with_automatic_capability_selection,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.remote_transport import RemoteTransportError
from home_ai_cluster.core.routing_candidates import NoSelectableCandidateReason


class RecordingAdapter:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return "local-adapter"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return RuntimeResult(content="local", adapter=self.name)


class RecordingRemoteTransport:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.requests: list[ClusterRequest] = []

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return ClusterResult(content="remote", adapter="remote", node_id="reported")


def make_request(local_only: bool) -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
        constraints=RequestConstraints(local_only=local_only),
    )


def make_node(node_id: str, adapter_name: str) -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=[adapter_name],
    )


def make_dependencies(
    *,
    local: bool,
    remote: bool,
    adapter_error: Exception | None = None,
    transport_error: Exception | None = None,
) -> tuple[
    NodeRegistry,
    AdapterRegistry,
    RemoteNodeDeclarationRegistry,
    RecordingAdapter,
    RecordingRemoteTransport,
]:
    adapter = RecordingAdapter(adapter_error)
    transport = RecordingRemoteTransport(transport_error)
    nodes = [make_node("local", adapter.name)] if local else []
    declarations = (
        [
            RemoteNodeDeclaration(
                node=make_node("remote", "remote-adapter"),
                transport_address="http://remote.example:8000",
            )
        ]
        if remote
        else []
    )
    return (
        NodeRegistry(nodes),
        AdapterRegistry([adapter] if local else []),
        RemoteNodeDeclarationRegistry(declarations),
        adapter,
        transport,
    )


@pytest.mark.parametrize(
    ("local_only", "local", "remote", "selected", "reason"),
    [
        (True, True, True, "local", None),
        (True, True, False, "local", None),
        (
            True,
            False,
            True,
            None,
            NoSelectableCandidateReason.LOCAL_ONLY_EXCLUDED_DECLARED_REMOTE,
        ),
        (True, False, False, None, NoSelectableCandidateReason.NO_MATCHING_CANDIDATE),
        (False, True, True, "local", None),
        (False, True, False, "local", None),
        (False, False, True, "remote", None),
        (False, False, False, None, NoSelectableCandidateReason.NO_MATCHING_CANDIDATE),
    ],
)
def test_automatic_orchestration_uses_the_rfc_0025_matrix(
    local_only: bool,
    local: bool,
    remote: bool,
    selected: str | None,
    reason: NoSelectableCandidateReason | None,
) -> None:
    dependencies = make_dependencies(local=local, remote=remote)
    node_registry, adapter_registry, remote_registry, adapter, transport = dependencies
    request = make_request(local_only)

    if selected is None:
        with pytest.raises(NoSelectableRoutingCandidateError) as raised:
            asyncio.run(
                orchestrate_request_with_automatic_capability_selection(
                    request,
                    node_registry,
                    adapter_registry,
                    remote_registry,
                    transport,
                )
            )
        assert raised.value.explanation.no_selectable_candidate_reason == reason
        assert adapter.requests == []
        assert transport.requests == []
        return

    result = asyncio.run(
        orchestrate_request_with_automatic_capability_selection(
            request,
            node_registry,
            adapter_registry,
            remote_registry,
            transport,
        )
    )

    if selected == "local":
        assert adapter.requests == [request]
        assert transport.requests == []
        assert result.node_id == "local"
    else:
        assert adapter.requests == []
        assert transport.requests == [request]
        assert result.node_id == "remote"


def test_selected_local_failure_propagates_without_remote_fallback() -> None:
    error = RuntimeAdapterUnavailableError("local failed")
    dependencies = make_dependencies(local=True, remote=True, adapter_error=error)
    node_registry, adapter_registry, remote_registry, adapter, transport = dependencies

    with pytest.raises(RuntimeAdapterUnavailableError) as raised:
        asyncio.run(
            orchestrate_request_with_automatic_capability_selection(
                make_request(False),
                node_registry,
                adapter_registry,
                remote_registry,
                transport,
            )
        )

    assert raised.value is error
    assert len(adapter.requests) == 1
    assert transport.requests == []


def test_selected_remote_failure_propagates_without_local_fallback() -> None:
    error = RemoteTransportError("remote failed")
    dependencies = make_dependencies(local=False, remote=True, transport_error=error)
    node_registry, adapter_registry, remote_registry, adapter, transport = dependencies

    with pytest.raises(RemoteTransportError) as raised:
        asyncio.run(
            orchestrate_request_with_automatic_capability_selection(
                make_request(False),
                node_registry,
                adapter_registry,
                remote_registry,
                transport,
            )
        )

    assert raised.value is error
    assert adapter.requests == []
    assert transport.requests == [make_request(False)]


def test_no_selectable_candidate_fails_before_selected_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.core import orchestrator as module

    dependencies = make_dependencies(local=False, remote=True)
    node_registry, adapter_registry, remote_registry, _, transport = dependencies

    async def fail_execution(*args: object, **kwargs: object) -> ClusterResult:
        raise AssertionError("selected-candidate execution must not be called")

    monkeypatch.setattr(
        module, "orchestrate_request_with_selected_candidate", fail_execution
    )

    with pytest.raises(NoSelectableRoutingCandidateError):
        asyncio.run(
            orchestrate_request_with_automatic_capability_selection(
                make_request(True),
                node_registry,
                adapter_registry,
                remote_registry,
                transport,
            )
        )


def test_automatic_orchestration_discovers_selects_and_executes_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.core import orchestrator as module

    dependencies = make_dependencies(local=True, remote=True)
    node_registry, adapter_registry, remote_registry, _, transport = dependencies
    request = make_request(False)
    calls = {"discovery": 0, "selection": 0, "execution": 0}
    discovery = module.routing_candidates_for_request
    selection = module.select_automatic_capability_routing_candidate
    execution = module.orchestrate_request_with_selected_candidate

    def count_discovery(*args: object):
        calls["discovery"] += 1
        return discovery(*args)  # type: ignore[arg-type]

    def count_selection(*args: object):
        calls["selection"] += 1
        return selection(*args)  # type: ignore[arg-type]

    async def count_execution(*args: object, **kwargs: object):
        calls["execution"] += 1
        return await execution(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(module, "routing_candidates_for_request", count_discovery)
    monkeypatch.setattr(
        module, "select_automatic_capability_routing_candidate", count_selection
    )
    monkeypatch.setattr(
        module, "orchestrate_request_with_selected_candidate", count_execution
    )

    asyncio.run(
        orchestrate_request_with_automatic_capability_selection(
            request,
            node_registry,
            adapter_registry,
            remote_registry,
            transport,
        )
    )

    assert calls == {"discovery": 1, "selection": 1, "execution": 1}
