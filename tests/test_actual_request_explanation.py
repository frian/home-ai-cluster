import asyncio
import json

import pytest

from home_ai_cluster.actual_request_explanation import (
    create_request,
    evaluate_actual_request,
    main,
)
from home_ai_cluster.adapters.base import RuntimeAdapter
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import build_remote_node_declaration_registry


class RecordingAdapter(RuntimeAdapter):
    def __init__(self) -> None:
        self.chat_calls = 0
        self.requests: list[ClusterRequest] = []

    @property
    def name(self) -> str:
        return "recording"

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name="chat")]

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        self.chat_calls += 1
        self.requests.append(request)
        return RuntimeResult(
            content="explained response",
            adapter=self.name,
            model="test-model",
        )


def create_local_registries() -> tuple[NodeRegistry, AdapterRegistry, RecordingAdapter]:
    adapter = RecordingAdapter()
    node = NodeDescription(
        id="test-local",
        name="Test local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name="chat")],
        adapters=[adapter.name],
    )
    return NodeRegistry([node]), AdapterRegistry([adapter]), adapter


def test_create_request_preserves_message_and_local_only_default() -> None:
    request = create_request("chat", "Hello")

    assert request.capability.name == "chat"
    assert request.messages[0].content == "Hello"
    assert request.constraints.local_only is True


def test_evaluate_actual_request_selects_and_executes_exactly_once() -> None:
    node_registry, adapter_registry, adapter = create_local_registries()

    projection = asyncio.run(
        evaluate_actual_request(
            "chat",
            "Hello",
            node_registry=node_registry,
            adapter_registry=adapter_registry,
            remote_registry=build_remote_node_declaration_registry([]),
        )
    )

    assert adapter.chat_calls == 1
    assert len(adapter.requests) == 1
    assert projection == {
        "routing": {
            "requested_capability": "chat",
            "matched_candidate_families": ["local"],
            "selectable_candidate_families": ["local"],
            "excluded_candidate_families": [],
            "selected_candidate_family": "local",
            "selected_node_id": "test-local",
            "outcome_rule": "local-only",
            "failure_reason": None,
        },
        "result": {
            "node_id": "test-local",
            "adapter": "recording",
            "model": "test-model",
            "content": "explained response",
        },
    }


def test_main_writes_one_json_object(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    expected = {
        "routing": {"selected_node_id": "test-local"},
        "result": {"content": "response"},
    }

    async def fake_evaluate(capability: str, message: str) -> dict[str, object]:
        assert capability == "chat"
        assert message == "Hello"
        return expected

    monkeypatch.setattr(
        "home_ai_cluster.actual_request_explanation.evaluate_actual_request",
        fake_evaluate,
    )

    main(["--capability", "chat", "--message", "Hello"])

    captured = capsys.readouterr()
    assert captured.out == json.dumps(expected) + "\n"
    assert captured.err == ""


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--capability", "chat"],
        ["--message", "Hello"],
        ["--capability", "   ", "--message", "Hello"],
        ["--capability", "chat", "--message", "   "],
    ],
)
def test_invalid_invocation_exits_nonzero(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(argv)

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == ""
    assert captured.err
