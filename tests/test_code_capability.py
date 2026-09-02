import asyncio

import httpx
import pytest
from pydantic import ValidationError

from home_ai_cluster.api.wiring import LocalAppComposition
from home_ai_cluster.commands import code_command
from home_ai_cluster.core.models import (
    INTERNAL_CLUSTER_REQUEST_ADAPTER,
    AdapterHealth,
    Capability,
    ChatMessage,
    ClusterRequest,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_transport import internal_cluster_request_body
from home_ai_cluster.core.static_capabilities import (
    DEFAULT_STATIC_CAPABILITY_NAMES,
    validate_static_capabilities,
)
from home_ai_cluster.main import create_app


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
                id="chat",
                name="chat",
                availability="available",
                health=NodeHealth(healthy=True),
                capabilities=[Capability(name="chat")],
                adapters=["test"],
            ),
            NodeDescription(
                id="code",
                name="code",
                availability="available",
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


@pytest.mark.parametrize(
    "argv",
    (
        ["   "],
        ["--message", "   "],
        ["--message", "first", "--message", "second"],
        ["message", "--message", "other"],
        ["one", "two"],
        ["--unknown"],
        ["--message", "x" * 65_537],
    ),
)
def test_code_command_requires_one_bounded_message(argv: list[str]) -> None:
    assert code_command._native_request("hello")["capability"] == "code"
    with pytest.raises(code_command.chat_command._InvalidRequestInput):
        code_command._parse_input(argv)


def test_code_positional_and_option_messages_normalize_to_the_same_request() -> None:
    positional = code_command._parse_input(["Write a function"])
    option = code_command._parse_input(["--message", "Write a function"])

    assert positional.message == option.message == "Write a function"
    assert code_command._native_request(
        positional.message
    ) == code_command._native_request(option.message)


def test_code_rejects_both_message_forms_before_request_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        code_command.chat_command,
        "_post_native_request",
        lambda *args, **kwargs: pytest.fail("must not request"),
    )

    with pytest.raises(SystemExit) as raised:
        code_command.main(["request", "--message", "other"])

    assert raised.value.code == 2


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
    class RecordingCodeAdapter:
        @property
        def name(self) -> str:
            return "test"

        def health(self) -> AdapterHealth:
            return AdapterHealth(available=True)

        def capabilities(self) -> list[Capability]:
            return [Capability(name="code")]

        async def chat(self, request: ClusterRequest) -> RuntimeResult:
            captured_requests.append(request)
            return RuntimeResult(content="text", adapter=self.name)

    captured_requests: list[ClusterRequest] = []
    adapter = RecordingCodeAdapter()
    app = create_app(
        local_app_composition=LocalAppComposition(
            node_registry=NodeRegistry(
                [
                    NodeDescription(
                        id="local",
                        name="local",
                        availability="available",
                        health=NodeHealth(healthy=True),
                        capabilities=[Capability(name="code")],
                        adapters=[adapter.name],
                    )
                ]
            ),
            adapter_registry=AdapterRegistry([adapter]),
        )
    )

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
