import asyncio

import httpx
import pytest

from home_ai_cluster.adapters.base import (
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
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
    orchestrate_request_with_automatic_capability_fallback,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.remote_transport import RemoteTransportError


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
        self.declarations: list[RemoteNodeDeclaration] = []

    async def send(
        self,
        request: ClusterRequest,
        declaration: RemoteNodeDeclaration,
    ) -> ClusterResult:
        self.requests.append(request)
        self.declarations.append(declaration)
        if self.error is not None:
            raise self.error
        return ClusterResult(content="remote", adapter="remote", node_id="reported")


def make_request(local_only: bool = False) -> ClusterRequest:
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
    local: bool = True,
    remote: bool = True,
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
    declarations = (
        [
            RemoteNodeDeclaration(
                node=make_node("declared-remote", "remote-adapter"),
                transport_address="http://remote.example:8000",
            )
        ]
        if remote
        else []
    )
    return (
        NodeRegistry([make_node("local", adapter.name)] if local else []),
        AdapterRegistry([adapter] if local else []),
        RemoteNodeDeclarationRegistry(declarations),
        adapter,
        transport,
    )


def run_fallback(
    dependencies: tuple[
        NodeRegistry,
        AdapterRegistry,
        RemoteNodeDeclarationRegistry,
        RecordingAdapter,
        RecordingRemoteTransport,
    ],
    request: ClusterRequest,
) -> ClusterResult:
    nodes, adapters, remotes, _, transport = dependencies
    return asyncio.run(
        orchestrate_request_with_automatic_capability_fallback(
            request, nodes, adapters, remotes, transport
        )
    )


def test_narrow_failure_discovers_selects_and_attempts_each_candidate_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from home_ai_cluster.core import orchestrator as module

    error = RuntimeConnectionUnavailableBeforeRequestError("not connected")
    dependencies = make_dependencies(adapter_error=error)
    nodes, adapters, remotes, adapter, transport = dependencies
    request = make_request()
    calls = {"discovery": 0, "selection": 0, "local": 0, "remote": 0}
    discovered = None
    discovery = module.routing_candidates_for_request
    selection = module.select_automatic_capability_routing_candidate
    execute_local = module.orchestrate_request_with_selected_candidate
    execute_remote = module.execute_declared_remote_routing_candidate

    def count_discovery(*args: object):
        nonlocal discovered
        calls["discovery"] += 1
        discovered = discovery(*args)  # type: ignore[arg-type]
        return discovered

    def count_selection(*args: object):
        calls["selection"] += 1
        return selection(*args)  # type: ignore[arg-type]

    async def count_local(*args: object, **kwargs: object) -> ClusterResult:
        calls["local"] += 1
        return await execute_local(*args, **kwargs)  # type: ignore[arg-type]

    async def count_remote(*args: object, **kwargs: object) -> ClusterResult:
        calls["remote"] += 1
        assert args[1] is discovered.declared_remote
        return await execute_remote(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(module, "routing_candidates_for_request", count_discovery)
    monkeypatch.setattr(
        module, "select_automatic_capability_routing_candidate", count_selection
    )
    monkeypatch.setattr(
        module, "orchestrate_request_with_selected_candidate", count_local
    )
    monkeypatch.setattr(
        module, "execute_declared_remote_routing_candidate", count_remote
    )

    result = run_fallback((nodes, adapters, remotes, adapter, transport), request)

    assert result.node_id == "declared-remote"
    assert calls == {"discovery": 1, "selection": 1, "local": 1, "remote": 1}
    assert adapter.requests == [request]
    assert transport.requests == [request]


def test_local_success_does_not_contact_remote() -> None:
    dependencies = make_dependencies()
    result = run_fallback(dependencies, make_request())

    assert result.node_id == "local"
    assert len(dependencies[3].requests) == 1
    assert dependencies[4].requests == []


@pytest.mark.parametrize(
    "error",
    [
        RuntimeAdapterUnavailableError("broad failure"),
        RuntimeError("arbitrary failure"),
        httpx.ConnectTimeout("timed out"),
        httpx.HTTPStatusError(
            "bad status",
            request=httpx.Request("POST", "http://runtime/api/chat"),
            response=httpx.Response(503),
        ),
    ],
)
def test_non_narrow_local_failures_do_not_fallback(error: Exception) -> None:
    dependencies = make_dependencies(adapter_error=error)

    with pytest.raises(type(error)) as raised:
        run_fallback(dependencies, make_request())

    assert raised.value is error
    assert len(dependencies[3].requests) == 1
    assert dependencies[4].requests == []


def test_narrow_failure_without_remote_remains_visible() -> None:
    error = RuntimeConnectionUnavailableBeforeRequestError("not connected")
    dependencies = make_dependencies(remote=False, adapter_error=error)

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError) as raised:
        run_fallback(dependencies, make_request())

    assert raised.value is error
    assert len(dependencies[3].requests) == 1
    assert dependencies[4].requests == []


def test_remote_failure_is_visible_without_retry() -> None:
    error = RemoteTransportError("remote failed")
    dependencies = make_dependencies(
        adapter_error=RuntimeConnectionUnavailableBeforeRequestError("not connected"),
        transport_error=error,
    )

    with pytest.raises(RemoteTransportError) as raised:
        run_fallback(dependencies, make_request())

    assert raised.value is error
    assert len(dependencies[3].requests) == 1
    assert len(dependencies[4].requests) == 1


def test_local_only_prevents_remote_fallback() -> None:
    error = RuntimeConnectionUnavailableBeforeRequestError("not connected")
    dependencies = make_dependencies(adapter_error=error)

    with pytest.raises(RuntimeConnectionUnavailableBeforeRequestError) as raised:
        run_fallback(dependencies, make_request(local_only=True))

    assert raised.value is error
    assert len(dependencies[3].requests) == 1
    assert dependencies[4].requests == []


def test_initially_selected_remote_uses_existing_single_execution_path() -> None:
    dependencies = make_dependencies(local=False)
    result = run_fallback(dependencies, make_request())

    assert result.node_id == "declared-remote"
    assert dependencies[3].requests == []
    assert len(dependencies[4].requests) == 1


def test_no_selectable_candidate_preserves_existing_error() -> None:
    dependencies = make_dependencies(local=False, remote=False)

    with pytest.raises(NoSelectableRoutingCandidateError):
        run_fallback(dependencies, make_request())

    assert dependencies[3].requests == []
    assert dependencies[4].requests == []
