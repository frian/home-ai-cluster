import inspect

from home_ai_cluster.core.execution_target import (
    remote_declaration_for_routing_decision,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.router import RoutingDecision


class RecordingAdapter:
    def __init__(self, name: str = "adapter") -> None:
        self._name = name
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
        return ClusterResult(content="result", adapter=self.name)


def make_node(
    node_id: str,
    *,
    name: str | None = None,
    adapters: list[str] | None = None,
) -> NodeDescription:
    return NodeDescription(
        id=node_id,
        name=name or f"{node_id} node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=adapters or ["adapter"],
    )


def make_declaration(
    node_id: str,
    *,
    name: str | None = None,
    transport_address: str | None = None,
) -> RemoteNodeDeclaration:
    return RemoteNodeDeclaration(
        node=make_node(node_id, name=name),
        transport_address=transport_address or f"http://{node_id}.local:8000",
    )


def make_decision(
    node: NodeDescription,
    adapter: RecordingAdapter | None = None,
) -> RoutingDecision:
    return RoutingDecision(
        node=node,
        adapter=adapter or RecordingAdapter(),
        capability=Capability(name="chat"),
        reason="test decision",
    )


def test_returns_matching_remote_declaration_for_routing_decision() -> None:
    declaration = make_declaration("remote")
    registry = RemoteNodeDeclarationRegistry([declaration])
    decision = make_decision(make_node("remote"))

    assert remote_declaration_for_routing_decision(decision, registry) is declaration


def test_returns_none_when_routing_decision_node_id_is_unknown() -> None:
    registry = RemoteNodeDeclarationRegistry([make_declaration("declared")])
    decision = make_decision(make_node("selected"))

    assert remote_declaration_for_routing_decision(decision, registry) is None


def test_uses_selected_node_id_only() -> None:
    matching = make_declaration(
        "selected-id",
        name="Different display name",
        transport_address="http://different-address.local:8000",
    )
    same_adapter_name = make_declaration("adapter")
    same_node_name = make_declaration("display-name", name="Selected display name")
    same_transport_address = make_declaration(
        "address-match",
        transport_address="http://selected-id.local:8000",
    )
    registry = RemoteNodeDeclarationRegistry(
        [
            same_adapter_name,
            same_node_name,
            same_transport_address,
            matching,
        ]
    )
    decision = make_decision(
        make_node(
            "selected-id",
            name="Selected display name",
            adapters=["adapter"],
        ),
        adapter=RecordingAdapter("adapter"),
    )

    assert remote_declaration_for_routing_decision(decision, registry) is matching


def test_does_not_call_selected_adapter() -> None:
    adapter = RecordingAdapter()
    registry = RemoteNodeDeclarationRegistry([make_declaration("remote")])
    decision = make_decision(make_node("remote"), adapter=adapter)

    remote_declaration_for_routing_decision(decision, registry)

    assert adapter.chat_requests == []


def test_does_not_require_or_call_remote_transport() -> None:
    registry = RemoteNodeDeclarationRegistry([make_declaration("remote")])
    decision = make_decision(make_node("remote"))

    result = remote_declaration_for_routing_decision(decision, registry)

    signature = inspect.signature(remote_declaration_for_routing_decision)
    assert list(signature.parameters) == ["decision", "remote_registry"]
    assert result is not None
    assert not hasattr(result, "send")


def test_does_not_mutate_registry() -> None:
    declaration = make_declaration("remote")
    registry = RemoteNodeDeclarationRegistry([declaration])
    decision = make_decision(make_node("remote"))

    remote_declaration_for_routing_decision(decision, registry)

    assert registry.list_declarations() == [declaration]
