import asyncio

import httpx
import pytest
from pydantic import ValidationError

from home_ai_cluster import code_command
from home_ai_cluster.core.models import (
    INTERNAL_CLUSTER_REQUEST_ADAPTER,
    Capability,
    ChatMessage,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
)
from home_ai_cluster.core.registry import NodeRegistry
from home_ai_cluster.core.remote_transport import internal_cluster_request_body
from home_ai_cluster.main import create_app
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


def test_code_eligibility_excludes_chat_only_node() -> None:
    nodes = NodeRegistry(
        [
            NodeDescription(
                id="chat", name="chat", availability="available",
                health=NodeHealth(healthy=True), capabilities=[Capability(name="chat")],
                adapters=["test"],
            ),
            NodeDescription(
                id="code", name="code", availability="available",
                health=NodeHealth(healthy=True),
                capabilities=[Capability(name="chat"), Capability(name="code")],
                adapters=["test"],
            ),
        ]
    )

    assert [node.id for node in nodes.nodes_for(Capability(name="code"))] == ["code"]


def test_code_uses_legacy_chat_transport_envelope() -> None:
    body = internal_cluster_request_body(make_request(["code"]))

    assert body["kind"] == "chat"
    assert body["request"]["capability"] == {"name": "code"}


def test_code_command_requires_one_bounded_explicit_message() -> None:
    assert code_command._native_request("hello")["capability"] == "code"
    with pytest.raises(code_command.chat_command._InvalidRequestInput):
        code_command._parse_input(["--message", "x" * 65_537])
    with pytest.raises(code_command.chat_command._InvalidRequestInput):
        code_command._parse_input([])


def test_code_command_uses_chat_path_and_code_specific_404(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    recorded: dict[str, object] = {}

    class Response:
        status_code = 404

    def post(request: dict[str, object], **kwargs: object) -> Response:
        recorded.update(request)
        return Response()

    monkeypatch.setattr(code_command.chat_command, "_post_native_request", post)
    with pytest.raises(SystemExit) as error:
        code_command.main(["--message", "hello"])

    assert error.value.code == 1
    assert recorded["capability"] == "code"
    assert capsys.readouterr().err == "error: no available code capability\n"


def test_native_chat_route_accepts_one_explicit_code_message() -> None:
    captured_requests: list[ClusterRequest] = []
    app = create_app()

    async def orchestrate(request: ClusterRequest) -> ClusterResult:
        captured_requests.append(request)
        return ClusterResult(content="text", adapter="test", node_id="local")

    app.state.automatic_proof_orchestrator = orchestrate

    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            return await client.post(
                "/v1/chat",
                json={
                    "capability": "code",
                    "messages": [{"role": "user", "content": "instruction"}],
                },
            )

    response = asyncio.run(send())

    assert response.status_code == 200
    assert response.json()["content"] == "text"
    assert response.json()["node_id"] == "local"
    assert len(captured_requests) == 1
    assert captured_requests[0].capability == Capability(name="code")
    assert captured_requests[0].messages == [
        ChatMessage(role="user", content="instruction")
    ]
