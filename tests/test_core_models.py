import pytest
from pydantic import ValidationError

from home_ai_cluster.core.models import (
    AdapterHealth,
    ApplicationStatus,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    ClusterStatusNode,
    ClusterStatusResult,
    DeclarationStatus,
    NodeDescription,
    NodeHealth,
    RequestConstraints,
    RuntimeStatus,
    SummarizeRequest,
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


@pytest.mark.parametrize("attempted_capability", ["chat", "summarization", "other"])
def test_summarize_request_has_a_fixed_routing_visible_capability(
    attempted_capability: str,
) -> None:
    request = SummarizeRequest(
        text="  Source text  ",
        capability=Capability(name=attempted_capability),
    )

    assert request.capability == Capability(name="summarize")
    assert request.model_dump() == {
        "text": "  Source text  ",
        "constraints": {
            "local_only": True,
            "prefer_fast_response": False,
            "min_context_size": None,
        },
    }
    assert "messages" not in request.model_dump()
    assert "capability" not in request.model_dump()


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_summarize_request_rejects_blank_text(text: str) -> None:
    with pytest.raises(ValidationError):
        SummarizeRequest(text=text)


def test_summarize_request_requires_string_text() -> None:
    with pytest.raises(ValidationError):
        SummarizeRequest(text=123)  # type: ignore[arg-type]


@pytest.mark.parametrize("text", ["Hello", "  Hello  ", "é"])
def test_summarize_request_preserves_accepted_text(text: str) -> None:
    assert SummarizeRequest(text=text).text == text


def test_summarize_request_accepts_text_at_the_ascii_byte_limit() -> None:
    at_limit = "a" * 65_536

    assert SummarizeRequest(text=at_limit).text == at_limit


def test_summarize_request_rejects_text_above_the_ascii_byte_limit() -> None:
    with pytest.raises(ValidationError):
        SummarizeRequest(text="a" * 65_537)


def test_summarize_request_enforces_the_multibyte_utf8_byte_limit() -> None:
    at_limit = "é" * 32_768

    assert SummarizeRequest(text=at_limit).text == at_limit

    with pytest.raises(ValidationError):
        SummarizeRequest(text=at_limit + "a")


def test_summarize_request_preserves_explicit_constraints_independently() -> None:
    request = SummarizeRequest(
        text="Source text", constraints=RequestConstraints(local_only=False)
    )
    other_request = SummarizeRequest(text="Other source text")

    assert request.constraints == RequestConstraints(local_only=False)
    assert other_request.constraints == RequestConstraints()
    assert request.constraints is not other_request.constraints


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


def test_cluster_result_requires_node_attribution() -> None:
    result = ClusterResult(
        content="Hello", adapter="test-runtime", node_id="selected-node"
    )

    assert result.content == "Hello"
    assert result.adapter == "test-runtime"
    assert result.model is None
    assert result.node_id == "selected-node"


def test_cluster_status_result_has_only_the_accepted_privacy_safe_fields() -> None:
    result = ClusterStatusResult(
        declaration_status=DeclarationStatus.COHERENT,
        nodes=(
            ClusterStatusNode(
                node_id="local",
                application_status=ApplicationStatus.LOCAL,
                runtime_status=RuntimeStatus.AVAILABLE,
            ),
        ),
    )

    assert result.model_dump(mode="json") == {
        "declaration_status": "coherent",
        "nodes": [
            {
                "node_id": "local",
                "application_status": "local",
                "runtime_status": "available",
            }
        ],
    }
    with pytest.raises(ValidationError):
        ClusterStatusNode(
            node_id="local",
            application_status=ApplicationStatus.LOCAL,
            runtime_status=RuntimeStatus.AVAILABLE,
            runtime_url="http://private.example",
        )
