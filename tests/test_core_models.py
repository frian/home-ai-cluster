import pytest
from pydantic import ValidationError

from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
    RequestConstraints,
)


def test_cluster_request_defaults_to_local_only_constraints() -> None:
    request = ClusterRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        capability=Capability(name="chat"),
    )

    assert request.capability == Capability(name="chat")
    assert request.constraints == RequestConstraints(local_only=True)


def test_cluster_request_requires_at_least_one_message() -> None:
    with pytest.raises(ValidationError):
        ClusterRequest(messages=[], capability=Capability(name="chat"))


def test_chat_message_requires_supported_role() -> None:
    with pytest.raises(ValidationError):
        ChatMessage(role="tool", content="Hello")  # type: ignore[arg-type]


def test_min_context_size_must_be_positive_when_provided() -> None:
    with pytest.raises(ValidationError):
        RequestConstraints(min_context_size=0)


def test_adapter_health_can_explain_unavailability() -> None:
    health = AdapterHealth(available=False, reason="runtime is not reachable")

    assert health.available is False
    assert health.reason == "runtime is not reachable"


def test_node_description_keeps_minimal_static_node_shape() -> None:
    node = NodeDescription(
        id="local",
        name="Local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=["ollama"],
    )

    assert node.model_dump() == {
        "id": "local",
        "name": "Local node",
        "availability": "available",
        "health": {"healthy": True, "reason": None},
        "capabilities": [{"name": "chat"}],
        "adapters": ["ollama"],
    }
    assert "models" not in NodeDescription.model_fields


def test_cluster_result_keeps_runtime_details_minimal() -> None:
    result = ClusterResult(content="Hello", adapter="test-runtime")

    assert result.content == "Hello"
    assert result.adapter == "test-runtime"
    assert result.model is None
