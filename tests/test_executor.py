import asyncio

import pytest

from home_ai_cluster.adapters.base import RuntimeAdapterUnavailableError
from home_ai_cluster.core.executor import (
    InvalidClassificationLabelError,
    execute_declared_routing_decision,
    execute_local_routing_decision,
    execute_remote_routing_decision,
    execute_routing_decision,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClassifyRequest,
    ClassifyResult,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
    SummarizeRequest,
)
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.remote_transport import RemoteTransportError
from home_ai_cluster.core.router import RoutingDecision


class RecordingAdapter:
    def __init__(
        self,
        result: RuntimeResult | None = None,
        error: RuntimeAdapterUnavailableError | None = None,
    ) -> None:
        self._result = result or RuntimeResult(content="result", adapter="adapter")
        self._error = error
        self.chat_requests: list[ClusterRequest] = []
        self.summarize_requests: list[SummarizeRequest] = []

    @property
    def name(self) -> str:
        return "adapter"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.chat_requests.append(request)

        if self._error is not None:
            raise self._error

        return self._result

    async def summarize(self, request: SummarizeRequest) -> RuntimeResult:
        self.summarize_requests.append(request)
        return self._result


class SummarizeRecordingAdapter(RecordingAdapter):
    def __init__(self, result: RuntimeResult | None = None) -> None:
        super().__init__(result=result)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="summarize")]

    async def summarize(self, request: SummarizeRequest) -> RuntimeResult:
        self.summarize_requests.append(request)
        return self._result


class ClassifyRecordingAdapter(RecordingAdapter):
    def __init__(self, proposal: str) -> None:
        super().__init__()
        self._proposal = proposal
        self.classify_requests: list[ClassifyRequest] = []

    def capabilities(self) -> list[Capability]:
        return [Capability(name="classify")]

    async def classify(self, request: ClassifyRequest) -> str:
        self.classify_requests.append(request)
        return self._proposal


class FakeRemoteTransport:
    def __init__(
        self,
        result: ClusterResult | None = None,
        error: RemoteTransportError | None = None,
    ) -> None:
        self._result = result or ClusterResult(
            content="remote result",
            adapter="remote-adapter",
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


def make_node(node_id: str = "local") -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["adapter"],
    )


def make_decision(
    adapter: RecordingAdapter,
    node_id: str = "local",
) -> RoutingDecision:
    return RoutingDecision(
        node=make_node(node_id),
        adapter=adapter,
        capability=Capability(name="chat"),
        reason="test decision",
    )


def make_declaration(node_id: str = "local") -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node(node_id),
        transport_address=f"http://{node_id}.local:8000",
    )


def test_execute_local_routing_decision_passes_exact_request() -> None:
    adapter = RecordingAdapter()
    request = make_request()

    asyncio.run(execute_local_routing_decision(request, make_decision(adapter)))

    assert adapter.chat_requests == [request]
    assert adapter.chat_requests[0] is request


def test_execute_local_routing_decision_attributes_selected_local_node() -> None:
    result = RuntimeResult(content="Hello", adapter="adapter")
    adapter = RecordingAdapter(result=result)

    actual = asyncio.run(
        execute_local_routing_decision(make_request(), make_decision(adapter))
    )

    assert actual.content == result.content
    assert actual.adapter == result.adapter
    assert actual.node_id == "local"


def test_execute_local_routing_decision_dispatches_summarize_with_attribution() -> None:
    result = RuntimeResult(content="", adapter="adapter", model="model")
    adapter = SummarizeRecordingAdapter(result=result)
    request = SummarizeRequest(text="Source text")
    decision = RoutingDecision(
        node=NodeDescription(
            id="selected-local",
            name="Selected local node",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="summarize")],
            adapters=["adapter"],
        ),
        adapter=adapter,
        capability=Capability(name="summarize"),
        reason="test summarize decision",
    )

    actual = asyncio.run(execute_local_routing_decision(request, decision))

    assert adapter.summarize_requests == [request]
    assert adapter.summarize_requests[0] is request
    assert adapter.chat_requests == []
    assert actual == ClusterResult(
        content="",
        adapter="adapter",
        model="model",
        node_id="selected-local",
    )


@pytest.mark.parametrize(
    ("labels", "proposal"),
    [
        (["invoice", "personal"], "invoice"),
        (["invoice", "Invoice"], "Invoice"),
        (["invoice", " invoice"], " invoice"),
        (["invoice", "étiquette"], "étiquette"),
    ],
)
def test_execute_local_routing_decision_dispatches_classify_with_exact_attribution(
    labels: list[str],
    proposal: str,
) -> None:
    adapter = ClassifyRecordingAdapter(proposal)
    request = ClassifyRequest(text="Source text", labels=labels)
    decision = RoutingDecision(
        node=NodeDescription(
            id="selected-local",
            name="Selected local node",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="classify")],
            adapters=["adapter"],
        ),
        adapter=adapter,
        capability=Capability(name="classify"),
        reason="test classify decision",
    )

    actual = asyncio.run(execute_local_routing_decision(request, decision))

    assert adapter.classify_requests == [request]
    assert adapter.classify_requests[0] is request
    assert adapter.chat_requests == []
    assert adapter.summarize_requests == []
    assert isinstance(actual, ClassifyResult)
    assert actual.selected_label == proposal
    assert actual.node_id == "selected-local"


@pytest.mark.parametrize(
    "proposal",
    ["unknown", "Invoice", " invoice", "invoice ", "The label is invoice", ""],
)
def test_execute_local_routing_decision_rejects_invalid_classification_proposals(
    proposal: str,
) -> None:
    adapter = ClassifyRecordingAdapter(proposal)
    request = ClassifyRequest(text="Source text", labels=["invoice", "personal"])
    decision = RoutingDecision(
        node=make_node(),
        adapter=adapter,
        capability=Capability(name="classify"),
        reason="test classify decision",
    )

    with pytest.raises(InvalidClassificationLabelError):
        asyncio.run(execute_local_routing_decision(request, decision))

    assert adapter.classify_requests == [request]
    assert adapter.chat_requests == []
    assert adapter.summarize_requests == []


def test_execute_routing_decision_delegates_to_local_execution_path() -> None:
    adapter = RecordingAdapter()
    request = make_request()

    asyncio.run(execute_routing_decision(request, make_decision(adapter)))

    assert adapter.chat_requests == [request]
    assert adapter.chat_requests[0] is request


def test_execute_routing_decision_does_not_inspect_remote_declarations() -> None:
    adapter = RecordingAdapter()
    decision = make_decision(adapter)

    asyncio.run(execute_routing_decision(make_request(), decision))

    assert not hasattr(decision, "remote_declarations")
    assert not hasattr(decision, "remote_node_declarations")
    assert not hasattr(decision, "declaration_registry")


def test_execute_routing_decision_does_not_require_remote_transport() -> None:
    adapter = RecordingAdapter()
    request = make_request()

    result = asyncio.run(execute_routing_decision(request, make_decision(adapter)))

    assert result.adapter == "adapter"
    assert not hasattr(adapter, "send")


def test_execute_remote_routing_decision_passes_exact_request_to_transport() -> None:
    transport = FakeRemoteTransport()
    request = make_request()

    asyncio.run(
        execute_remote_routing_decision(
            request,
            make_decision(RecordingAdapter()),
            make_declaration(),
            transport,
        )
    )

    assert transport.requests == [request]
    assert transport.requests[0] is request


def test_execute_remote_routing_decision_passes_exact_declaration() -> None:
    transport = FakeRemoteTransport()
    declaration = make_declaration()

    asyncio.run(
        execute_remote_routing_decision(
            make_request(),
            make_decision(RecordingAdapter()),
            declaration,
            transport,
        )
    )

    assert transport.declarations == [declaration]
    assert transport.declarations[0] is declaration


def test_execute_remote_routing_decision_uses_declaration_node_id() -> None:
    result = ClusterResult(
        content="Hello from remote", adapter="remote-adapter", node_id="remote-response"
    )
    transport = FakeRemoteTransport(result=result)

    actual = asyncio.run(
        execute_remote_routing_decision(
            make_request(),
            make_decision(RecordingAdapter()),
            make_declaration(),
            transport,
        )
    )

    assert actual.content == result.content
    assert actual.adapter == result.adapter
    assert actual.node_id == "local"


def test_execute_remote_routing_decision_propagates_transport_errors() -> None:
    error = RemoteTransportError("remote transport failed")
    transport = FakeRemoteTransport(error=error)

    with pytest.raises(RemoteTransportError) as raised:
        asyncio.run(
            execute_remote_routing_decision(
                make_request(),
                make_decision(RecordingAdapter()),
                make_declaration(),
                transport,
            )
        )

    assert raised.value is error


def test_execute_remote_routing_decision_does_not_call_selected_local_adapter() -> None:
    adapter = RecordingAdapter()
    transport = FakeRemoteTransport()

    asyncio.run(
        execute_remote_routing_decision(
            make_request(),
            make_decision(adapter),
            make_declaration(),
            transport,
        )
    )

    assert adapter.chat_requests == []


def test_execute_declared_routing_decision_uses_local_without_declaration() -> None:
    adapter = RecordingAdapter()
    transport = FakeRemoteTransport()
    request = make_request()
    registry = RemoteNodeDeclarationRegistry([make_declaration("other")])

    result = asyncio.run(
        execute_declared_routing_decision(
            request,
            make_decision(adapter),
            registry,
            transport,
        )
    )

    assert result.adapter == "adapter"
    assert adapter.chat_requests == [request]
    assert adapter.chat_requests[0] is request
    assert transport.requests == []


def test_execute_declared_routing_decision_uses_remote_transport() -> None:
    adapter = RecordingAdapter()
    transport_result = ClusterResult(
        content="Hello from declared remote",
        adapter="remote-adapter",
        node_id="remote-response",
    )
    transport = FakeRemoteTransport(result=transport_result)
    request = make_request()
    declaration = make_declaration("declared-remote")
    declaration.transport_address = "http://192.0.2.7:8000"
    registry = RemoteNodeDeclarationRegistry([declaration])

    result = asyncio.run(
        execute_declared_routing_decision(
            request,
            make_decision(adapter, "declared-remote"),
            registry,
            transport,
        )
    )

    assert result.content == transport_result.content
    assert result.node_id == "declared-remote"
    assert result.node_id != declaration.transport_address
    assert result.node_id != transport_result.node_id
    assert transport.requests == [request]
    assert transport.requests[0] is request
    assert transport.declarations == [declaration]
    assert transport.declarations[0] is declaration
    assert adapter.chat_requests == []


def test_execute_local_routing_decision_propagates_adapter_errors() -> None:
    error = RuntimeAdapterUnavailableError("adapter failed")
    adapter = RecordingAdapter(error=error)

    with pytest.raises(RuntimeAdapterUnavailableError) as raised:
        asyncio.run(
            execute_local_routing_decision(make_request(), make_decision(adapter))
        )

    assert raised.value is error


def test_execute_routing_decision_propagates_adapter_errors() -> None:
    error = RuntimeAdapterUnavailableError("adapter failed")
    adapter = RecordingAdapter(error=error)

    with pytest.raises(RuntimeAdapterUnavailableError) as raised:
        asyncio.run(execute_routing_decision(make_request(), make_decision(adapter)))

    assert raised.value is error
