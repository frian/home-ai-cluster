import pytest

from home_ai_cluster.api.wiring import (
    LocalAppComposition,
    build_static_remote_collection_wiring,
    build_static_remote_wiring,
)
from home_ai_cluster.core.adapter_execution_contracts import (
    AdapterExecutionContractError,
    validate_adapter_execution_contracts,
)
from home_ai_cluster.core.local_capability_binding import (
    LocalCapabilityBinding,
    LocalCapabilityBindings,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import RemoteNodeDeclaration
from home_ai_cluster.core.routing_candidates import RoutingCandidateSelectionMode


class CommonAdapter:
    def __init__(self, capabilities: set[str]) -> None:
        self._capabilities = capabilities

    @property
    def name(self) -> str:
        return "partial"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name=name) for name in self._capabilities]


class ChatAdapter(CommonAdapter):
    async def chat(self, request: object) -> object:
        return object()


class SummarizeAdapter(CommonAdapter):
    async def summarize(self, request: object) -> object:
        return object()


class ClassifyAdapter(CommonAdapter):
    async def classify(self, request: object) -> str:
        return "label"


def local_composition(adapter: CommonAdapter) -> LocalAppComposition:
    return LocalAppComposition(
        node_registry=NodeRegistry(
            [
                NodeDescription(
                    id="local",
                    name="Local node",
                    availability="available",
                    health=NodeHealth(healthy=True),
                    capabilities=adapter.capabilities(),
                    adapters=[adapter.name],
                )
            ]
        ),
        adapter_registry=AdapterRegistry([adapter]),
    )


def test_chat_only_adapter_is_admitted_without_unrelated_operations() -> None:
    adapter = ChatAdapter({"chat"})

    local_composition(adapter)


def test_chat_and_code_share_the_chat_execution_contract() -> None:
    adapter = ChatAdapter({"chat", "code"})

    local_composition(adapter)


@pytest.mark.parametrize(
    ("adapter", "capability"),
    [
        (CommonAdapter({"chat"}), "chat-shaped execution"),
        (CommonAdapter({"code"}), "chat-shaped execution"),
        (CommonAdapter({"summarize"}), "summarize"),
        (CommonAdapter({"classify"}), "classify"),
    ],
)
def test_claim_without_required_execution_contract_fails_admission(
    adapter: CommonAdapter, capability: str
) -> None:
    with pytest.raises(AdapterExecutionContractError, match=capability):
        local_composition(adapter)


def test_operation_without_positive_capability_claim_does_not_create_support() -> None:
    adapter = SummarizeAdapter(set())

    validate_adapter_execution_contracts([adapter])
    assert adapter.capabilities() == []


def test_all_positive_claims_are_validated_even_when_binding_omits_one() -> None:
    adapter = ChatAdapter({"chat", "summarize"})
    binding = LocalCapabilityBinding(frozenset({"chat"}), adapter)
    bindings = LocalCapabilityBindings([binding])

    with pytest.raises(AdapterExecutionContractError, match="summarize"):
        LocalAppComposition(
            node_registry=NodeRegistry(),
            adapter_registry=AdapterRegistry(
                [adapter], local_capability_bindings=bindings
            ),
        )

    assert bindings.capability_names == frozenset({"chat"})


def test_legacy_non_binding_composition_is_admitted_before_routing() -> None:
    with pytest.raises(AdapterExecutionContractError, match="classify"):
        local_composition(CommonAdapter({"classify"}))

    local_composition(ChatAdapter({"chat"}))


def test_generic_registry_storage_is_not_executable_admission() -> None:
    adapter = CommonAdapter({"classify"})

    registry = AdapterRegistry([adapter])

    assert registry.list_adapters() == [adapter]


def test_admission_does_not_observe_health() -> None:
    class HealthFailingChatAdapter(ChatAdapter):
        def health(self) -> AdapterHealth:
            raise AssertionError("admission must not call health")

    local_composition(HealthFailingChatAdapter({"chat"}))


@pytest.mark.parametrize(
    "build_wiring",
    [build_static_remote_wiring, build_static_remote_collection_wiring],
)
def test_static_remote_wiring_admits_local_adapters(
    build_wiring: object,
) -> None:
    adapter = CommonAdapter({"summarize"})
    declaration = RemoteNodeDeclaration(
        node=NodeDescription(
            id="remote",
            name="Remote node",
            availability="available",
            health=NodeHealth(healthy=True),
            capabilities=[Capability(name="chat")],
            adapters=["remote"],
        ),
        transport_address="https://remote.test",
    )
    arguments = dict(
        node_registry=NodeRegistry(),
        adapter_registry=AdapterRegistry([adapter]),
        remote_transport=object(),
        selection_mode=RoutingCandidateSelectionMode.AUTOMATIC_CAPABILITY,
    )

    with pytest.raises(AdapterExecutionContractError, match="summarize"):
        if build_wiring is build_static_remote_wiring:
            build_wiring(remote_declaration=declaration, **arguments)
        else:
            build_wiring(remote_declarations=[declaration], **arguments)
