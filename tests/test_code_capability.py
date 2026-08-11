import pytest
from pydantic import ValidationError

from home_ai_cluster import code_command
from home_ai_cluster.core.models import (
    INTERNAL_CLUSTER_REQUEST_ADAPTER,
    Capability,
    ChatMessage,
    ClusterRequest,
)
from home_ai_cluster.static_capabilities import (
    DEFAULT_STATIC_CAPABILITY_NAMES,
    validate_static_capabilities,
)


def make_request(messages: list[str], capability: str = "code") -> ClusterRequest:
    return ClusterRequest(
        messages=[ChatMessage(role="user", content=content) for content in messages],
        capability=Capability(name=capability),
    )


def test_code_bound_counts_aggregate_utf8_bytes() -> None:
    assert make_request(["a" * 65_536]).capability.name == "code"
    assert make_request(["é" * 16_384, "b" * 32_768]).capability.name == "code"
    with pytest.raises(ValidationError):
        make_request(["a" * 65_537])
    with pytest.raises(ValidationError):
        make_request(["é" * 32_769])


def test_chat_and_diagnostic_capabilities_remain_unbounded() -> None:
    assert make_request(["a" * 65_537], "chat").capability.name == "chat"
    assert make_request(["a" * 65_537], "vision").capability.name == "vision"


def test_static_code_is_explicit_and_omission_default_is_unchanged() -> None:
    assert DEFAULT_STATIC_CAPABILITY_NAMES == ("chat", "summarize")
    assert validate_static_capabilities(["code"], subject="local") == ("code",)
    assert validate_static_capabilities(["code"], subject="remote") == ("code",)
    with pytest.raises(ValueError, match="duplicate"):
        validate_static_capabilities(["code", "code"], subject="local")


def test_internal_message_envelope_preserves_code_and_rejects_vision() -> None:
    code = INTERNAL_CLUSTER_REQUEST_ADAPTER.validate_python(
        {"kind": "chat", "request": make_request(["code"]).model_dump()}
    )
    assert code.request.capability.name == "code"
    with pytest.raises(ValidationError):
        INTERNAL_CLUSTER_REQUEST_ADAPTER.validate_python(
            {
                "kind": "chat",
                "request": make_request(["diagnostic"], "vision").model_dump(),
            }
        )


def test_code_command_requires_one_bounded_explicit_message() -> None:
    assert code_command._native_request("hello")["capability"] == "code"
    with pytest.raises(code_command.chat_command._InvalidRequestInput):
        code_command._parse_input(["--message", "x" * 65_537])
    with pytest.raises(code_command.chat_command._InvalidRequestInput):
        code_command._parse_input([])
