import asyncio
import json
import struct
import zlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from home_ai_cluster.adapters.base import (
    RuntimeAdapter,
    RuntimeAdapterUnavailableError,
    RuntimeConnectionUnavailableBeforeRequestError,
)
from home_ai_cluster.commands.actual_request_explanation import (
    EXECUTION_FAILED_FAILURE,
    EXECUTION_PERMISSION_DENIED_FAILURE,
    HISTORY_RECORDING_WARNING,
    INTERNAL_FAILURE_MESSAGE,
    NO_SELECTABLE_CANDIDATE_FAILURE,
    RUNTIME_UNAVAILABLE_FAILURE,
    _evaluate_ordinary_request,
    create_request,
    evaluate_actual_request,
    main,
)
from home_ai_cluster.core.execution_intervals import ExecutionIntervalCardinality
from home_ai_cluster.core.local_capability_binding import (
    LocalCapabilityBinding,
    LocalCapabilityBindings,
)
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ChatMessage,
    ClassifyRequest,
    ClassifyResult,
    ClusterRequest,
    ClusterResult,
    ImageGenerationRequest,
    ImageGenerationResult,
    NodeDescription,
    NodeHealth,
    RequestConstraints,
    RuntimeResult,
    SummarizeRequest,
)
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import build_remote_node_declaration_registry
from home_ai_cluster.core.remote_transport import RemoteExecutionPermissionDeniedError
from home_ai_cluster.core.routing_candidates import (
    routing_candidates_for_request,
    select_automatic_capability_routing_candidate,
)
from home_ai_cluster.local_runtime_composition import (
    LocalCapabilityBindingValues,
    LocalRuntimeCompositionValues,
    MultiBindingRuntimeCompositionValues,
)
from home_ai_cluster.request_history import record_for_account
from home_ai_cluster.retained_configuration import (
    RetainedConfiguration,
    RetainedLocalConfiguration,
    save_retained_configuration,
)
from home_ai_cluster.static_cluster import create_remote_declaration
from home_ai_cluster.static_cluster_declaration import RemoteNodeDeclaration


class RecordingAdapter(RuntimeAdapter):
    def __init__(self, result: RuntimeResult | Exception) -> None:
        self._result = result
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
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def create_local_registries(
    result: RuntimeResult | Exception,
    *,
    capability: str = "chat",
) -> tuple[NodeRegistry, AdapterRegistry, RecordingAdapter]:
    adapter = RecordingAdapter(result)
    node = NodeDescription(
        id="test-local",
        name="Test local node",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name=capability)],
        adapters=[adapter.name],
    )
    return NodeRegistry([node]), AdapterRegistry([adapter]), adapter


def evaluate(
    result: RuntimeResult | Exception,
    *,
    requested_capability: str = "chat",
    node_capability: str = "chat",
) -> tuple[dict[str, object], RecordingAdapter]:
    nodes, adapters, adapter = create_local_registries(
        result, capability=node_capability
    )
    account = asyncio.run(
        evaluate_actual_request(
            requested_capability,
            "private prompt content",
            node_registry=nodes,
            adapter_registry=adapters,
            remote_registry=build_remote_node_declaration_registry([]),
        )
    )
    return account, adapter


def test_create_request_preserves_message_and_allows_ordinary_remote_fallback() -> None:
    request = create_request("chat", "Hello")

    assert request.capability.name == "chat"
    assert request.messages[0].content == "Hello"
    assert request.constraints.local_only is False


def test_successful_account_has_the_structured_rfc_0034_projection() -> None:
    account, adapter = evaluate(
        RuntimeResult(
            content="explained response", adapter="recording", model="test-model"
        )
    )

    assert list(account) == ["status", "routing", "result", "failure", "lifecycle"]
    assert account["lifecycle"] == {
        "candidates": [
            {
                "family": "local",
                "node_id": "test-local",
                "fact": "execution-permission-granted",
            },
            {"family": "local", "node_id": "test-local", "fact": "adapter-invoked"},
        ],
        "continuations": [],
        "final_node_id": "test-local",
    }
    assert {
        key: account[key] for key in ("status", "routing", "result", "failure")
    } == {
        "status": "succeeded",
        "routing": {
            "requested_capability": "chat",
            "matched_candidate_families": ["local"],
            "selectable_candidate_families": ["local"],
            "excluded_candidate_families": [],
            "selected_candidate_family": "local",
            "selected_node_id": "test-local",
            "outcome_rule": "local-only",
            "failure_reason": None,
            "local_execution_permission": "granted",
            "candidate_consideration": "executed",
        },
        "result": {
            "node_id": "test-local",
            "adapter": "recording",
            "model": "test-model",
            "content": "explained response",
        },
        "failure": None,
    }
    assert adapter.chat_calls == 1
    assert len(adapter.requests) == 1


def test_no_selectable_candidate_preserves_exception_routing_and_does_not_execute() -> (
    None
):
    account, adapter = evaluate(
        RuntimeResult(content="unused", adapter="recording"),
        requested_capability="vision",
    )

    assert {
        key: account[key] for key in ("status", "routing", "result", "failure")
    } == {
        "status": "failed",
        "routing": {
            "requested_capability": "vision",
            "matched_candidate_families": [],
            "selectable_candidate_families": [],
            "excluded_candidate_families": [],
            "selected_candidate_family": None,
            "selected_node_id": None,
            "outcome_rule": "no-selectable-candidate",
            "failure_reason": "no-matching-candidate",
            "local_execution_permission": "not-applicable",
            "candidate_consideration": "ended",
        },
        "result": None,
        "failure": NO_SELECTABLE_CANDIDATE_FAILURE,
    }
    assert adapter.chat_calls == 0


def test_evaluate_selects_and_executes_at_most_once() -> None:
    account, adapter = evaluate(RuntimeResult(content="response", adapter="recording"))

    assert account["status"] == "succeeded"
    assert adapter.chat_calls == 1


def test_actual_request_reports_local_execution_permission_denial() -> None:
    async def run() -> tuple[dict[str, object], RecordingAdapter]:
        nodes, adapters, adapter = create_local_registries(
            RuntimeResult(content="unused", adapter="recording")
        )
        intervals = ExecutionIntervalCardinality()
        assert await intervals.try_enter()
        account = await evaluate_actual_request(
            "chat",
            "private prompt content",
            node_registry=nodes,
            adapter_registry=adapters,
            remote_registry=build_remote_node_declaration_registry([]),
            execution_intervals=intervals,
        )
        assert intervals.value == 1
        await intervals.exit()
        return account, adapter

    account, adapter = asyncio.run(run())

    assert account["failure"] == EXECUTION_PERMISSION_DENIED_FAILURE
    assert account["routing"]["selectable_candidate_families"] == ["local"]
    assert account["routing"]["local_execution_permission"] == "denied"
    assert account["routing"]["candidate_consideration"] == "ended"
    assert adapter.chat_calls == 0
    assert account["lifecycle"] == {
        "candidates": [
            {
                "family": "local",
                "node_id": "test-local",
                "fact": "execution-permission-denied",
            }
        ],
        "continuations": [],
        "final_node_id": None,
    }


@pytest.mark.parametrize(
    "error",
    [
        RuntimeAdapterUnavailableError("http://private-host authorization=secret"),
        RuntimeConnectionUnavailableBeforeRequestError(
            "http://private-host authorization=secret"
        ),
    ],
)
def test_runtime_unavailable_failures_keep_selection_without_leaking(
    error: Exception,
) -> None:
    account, adapter = evaluate(error)

    assert account["status"] == "failed"
    assert account["routing"] == {
        "requested_capability": "chat",
        "matched_candidate_families": ["local"],
        "selectable_candidate_families": ["local"],
        "excluded_candidate_families": [],
        "selected_candidate_family": "local",
        "selected_node_id": "test-local",
        "outcome_rule": "local-only",
        "failure_reason": None,
        "local_execution_permission": "granted",
        "candidate_consideration": "executed",
    }
    assert account["result"] is None
    assert account["failure"] == RUNTIME_UNAVAILABLE_FAILURE
    assert "private-host" not in json.dumps(account)
    assert "Runtime" not in json.dumps(account)
    assert adapter.chat_calls == 1


def test_unexpected_execution_failure_is_safely_normalized() -> None:
    account, adapter = evaluate(
        RuntimeError("private prompt content http://private-host token=secret")
    )

    assert account["status"] == "failed"
    assert account["routing"]["selected_candidate_family"] == "local"
    assert account["routing"]["selected_node_id"] == "test-local"
    assert account["routing"]["candidate_consideration"] == "executed"
    assert account["result"] is None
    assert account["failure"] == EXECUTION_FAILED_FAILURE
    serialized = json.dumps(account)
    assert "private prompt content" not in serialized
    assert "private-host" not in serialized
    assert "RuntimeError" not in serialized
    assert adapter.chat_calls == 1
    assert account["lifecycle"] == {
        "candidates": [
            {
                "family": "local",
                "node_id": "test-local",
                "fact": "execution-permission-granted",
            },
            {"family": "local", "node_id": "test-local", "fact": "adapter-invoked"},
        ],
        "continuations": [],
        "final_node_id": None,
    }


def test_evaluate_uses_its_own_effective_ordinary_wiring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    nodes, adapters, _ = create_local_registries(
        RuntimeResult(content="response", adapter="recording")
    )
    calls: list[object] = []
    composition = SimpleNamespace(
        node_registry=nodes,
        adapter_registry=adapters,
        execution_intervals=ExecutionIntervalCardinality(),
    )
    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.load_retained_configuration",
        lambda: RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=LocalRuntimeCompositionValues(runtime="ollama"),
                local_capabilities=("chat",),
                execution_limit=2,
            ),
            remote_nodes=(
                RemoteNodeDeclaration("remote-a", "http://remote-a.test"),
                RemoteNodeDeclaration("remote-b", "http://remote-b.test"),
            ),
        ),
    )
    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.local_runtime.parse_args",
        lambda _: calls.append("parse") or object(),
    )
    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.local_runtime.create_local_runtime_app",
        lambda _: (
            calls.append("local")
            or SimpleNamespace(state=SimpleNamespace(local_app_composition=composition))
        ),
    )
    original_compose = __import__(
        "home_ai_cluster.static_cluster", fromlist=["x"]
    )._compose_effective_ordinary_request_wiring

    def compose(**kwargs: object) -> object:
        calls.append(kwargs)
        return original_compose(**kwargs)

    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.static_cluster._compose_effective_ordinary_request_wiring",
        compose,
    )

    account = asyncio.run(evaluate_actual_request("chat", "Hello"))

    assert calls[:2] == ["parse", "local"]
    assert calls[2]["local_app_composition"] is composition
    assert [node.node_id for node in calls[2]["remote_nodes"]] == [
        "remote-a",
        "remote-b",
    ]
    assert calls[2]["caller_local_capabilities"] == ("chat",)
    assert account["status"] == "succeeded"


def test_evaluate_uses_real_retained_multi_binding_ordinary_composition(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local-app-data"))
    save_retained_configuration(
        RetainedConfiguration(
            local=RetainedLocalConfiguration(
                runtime=MultiBindingRuntimeCompositionValues(
                    bindings=(
                        LocalCapabilityBindingValues(
                            capabilities=("chat", "summarize"),
                            runtime="ollama",
                            model="chat-model",
                        ),
                        LocalCapabilityBindingValues(
                            capabilities=("classify",),
                            runtime="ollaya",
                            base_url="http://127.0.0.1:11435",
                            model="classify-model",
                        ),
                    )
                ),
                local_capabilities=("classify",),
                execution_limit=2,
            ),
            remote_nodes=(
                RemoteNodeDeclaration(
                    "remote-a", "http://remote-a.test", ("classify",)
                ),
                RemoteNodeDeclaration(
                    "remote-b", "http://remote-b.test", ("classify",)
                ),
            ),
        )
    )

    class Client:
        def __init__(self) -> None:
            self.close_calls = 0

        async def aclose(self) -> None:
            self.close_calls += 1

    class RecordingHttpRemoteTransport:
        def __init__(self, client: Client) -> None:
            self.client = client

    client = Client()
    captured: dict[str, object] = {}

    async def capture_orchestration(
        request, nodes, adapters, remotes, remote_transport, intervals, lifecycle
    ):
        captured.update(
            nodes=nodes,
            adapters=adapters,
            remotes=remotes,
            remote_transport=remote_transport,
            intervals=intervals,
        )
        selection = select_automatic_capability_routing_candidate(
            request, routing_candidates_for_request(request, nodes, adapters, remotes)
        )
        assert selection.selected is not None
        lifecycle.selected(selection.explanation)
        lifecycle.succeeded("local")
        assert isinstance(request, ClassifyRequest)
        assert request.labels == ["a", "b"]
        return ClassifyResult(selected_label="a", node_id="local")

    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.static_cluster.create_static_cluster_http_client",
        lambda: client,
    )
    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.static_cluster.HttpRemoteTransport",
        RecordingHttpRemoteTransport,
    )
    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.orchestrate_request_with_ordered_static_remote_fallback",
        capture_orchestration,
    )
    account = asyncio.run(
        _evaluate_ordinary_request(
            ClassifyRequest(
                text="Hello",
                labels=["a", "b"],
                constraints=RequestConstraints(local_only=False),
            )
        )
    )

    nodes = captured["nodes"]
    assert isinstance(nodes, NodeRegistry)
    assert [capability.name for capability in nodes.list_nodes()[0].capabilities] == [
        "classify"
    ]
    adapters = captured["adapters"]
    assert isinstance(adapters, AdapterRegistry)
    assert adapters.has_local_capability_bindings
    assert adapters.bound_adapter_for(Capability(name="chat")).name == "ollama"
    assert adapters.bound_adapter_for(Capability(name="classify")).name == "ollaya"
    remotes = captured["remotes"]
    assert [declaration.node.id for declaration in remotes.list_declarations()] == [
        "remote-a",
        "remote-b",
    ]
    intervals = captured["intervals"]
    assert isinstance(intervals, ExecutionIntervalCardinality)

    async def verify_execution_limit() -> None:
        assert await intervals.try_enter()
        assert await intervals.try_enter()
        assert not await intervals.try_enter()
        await intervals.exit()
        await intervals.exit()

    asyncio.run(verify_execution_limit())
    remote_transport = captured["remote_transport"]
    assert isinstance(remote_transport, RecordingHttpRemoteTransport)
    assert remote_transport.client is client
    assert client.close_calls == 1
    assert account["status"] == "succeeded"


@pytest.mark.parametrize(
    "account, expected_exit",
    [
        (
            {
                "status": "succeeded",
                "routing": {},
                "result": {"content": "response"},
                "failure": None,
            },
            0,
        ),
        (
            {
                "status": "failed",
                "routing": {},
                "result": None,
                "failure": EXECUTION_FAILED_FAILURE,
            },
            1,
        ),
    ],
)
def test_main_emits_one_compact_account_with_expected_exit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    account: dict[str, object],
    expected_exit: int,
) -> None:
    async def fake_evaluate(capability: str, message: str) -> dict[str, object]:
        assert capability == "chat"
        assert message == "Hello"
        return account

    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.evaluate_actual_request",
        fake_evaluate,
    )

    if expected_exit:
        with pytest.raises(SystemExit) as raised:
            main(["--capability", "chat", "--message", "Hello"])
        assert raised.value.code == expected_exit
    else:
        main(["--capability", "chat", "--message", "Hello"])

    captured = capsys.readouterr()
    assert captured.out == json.dumps(account, separators=(",", ":")) + "\n"
    assert captured.err == ""


def test_main_reports_safe_stderr_for_internal_account_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def fail_evaluation(capability: str, message: str) -> dict[str, object]:
        raise RuntimeError("private prompt content http://private-host token=secret")

    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.evaluate_actual_request",
        fail_evaluation,
    )

    with pytest.raises(SystemExit) as raised:
        main(["--capability", "chat", "--message", "Hello"])

    captured = capsys.readouterr()
    assert raised.value.code != 0
    assert captured.out == ""
    assert captured.err == INTERNAL_FAILURE_MESSAGE + "\n"


def test_main_does_not_record_history_without_explicit_flag(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    account = {
        "status": "succeeded",
        "routing": {"requested_capability": "chat"},
        "result": {"content": "response"},
        "failure": None,
    }

    async def fake_evaluate(capability: str, message: str) -> dict[str, object]:
        return account

    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.evaluate_actual_request",
        fake_evaluate,
    )
    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.record_account",
        lambda _: pytest.fail("history recording must be opt-in"),
    )

    main(["--capability", "chat", "--message", "Hello"])

    captured = capsys.readouterr()
    assert captured.out == json.dumps(account, separators=(",", ":")) + "\n"
    assert captured.err == ""
    assert not (tmp_path / "home-ai-cluster").exists()


def test_main_records_unchanged_account_with_explicit_flag(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    account = {
        "status": "succeeded",
        "routing": {
            "requested_capability": "chat",
            "selected_candidate_family": "local",
            "outcome_rule": "local-only",
        },
        "result": {"content": "response"},
        "failure": None,
    }

    async def fake_evaluate(capability: str, message: str) -> dict[str, object]:
        return account

    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.evaluate_actual_request",
        fake_evaluate,
    )

    main(["--capability", "chat", "--message", "Hello", "--record-history"])

    captured = capsys.readouterr()
    assert captured.out == json.dumps(account, separators=(",", ":")) + "\n"
    assert captured.err == ""
    assert json.loads(
        (tmp_path / "home-ai-cluster" / "request-history.jsonl").read_text(
            encoding="utf-8"
        )
    ) == {
        "status": "succeeded",
        "requested_capability": "chat",
        "selected_candidate_family": "local",
        "outcome_rule": "local-only",
        "failure_status": None,
    }


@pytest.mark.parametrize("status", ["succeeded", "failed"])
def test_main_preserves_account_and_exit_when_history_recording_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    status: str,
) -> None:
    account = {
        "status": status,
        "routing": {"requested_capability": "chat"},
        "result": {"content": "response"} if status == "succeeded" else None,
        "failure": None if status == "succeeded" else EXECUTION_FAILED_FAILURE,
    }

    async def fake_evaluate(capability: str, message: str) -> dict[str, object]:
        return account

    def fail_record(account: dict[str, object]) -> None:
        raise PermissionError("/private/state request-history.jsonl")

    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.evaluate_actual_request",
        fake_evaluate,
    )
    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.record_account",
        fail_record,
    )

    arguments = ["--capability", "chat", "--message", "Hello", "--record-history"]
    if status == "failed":
        with pytest.raises(SystemExit) as raised:
            main(arguments)
        assert raised.value.code != 0
    else:
        main(arguments)

    captured = capsys.readouterr()
    assert captured.out == json.dumps(account, separators=(",", ":")) + "\n"
    assert captured.err == HISTORY_RECORDING_WARNING + "\n"
    assert "/private" not in captured.err


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


class ScriptedExplanationRemoteTransport:
    def __init__(self, outcomes: dict[str, ClusterResult | Exception]) -> None:
        self.outcomes = outcomes
        self.node_ids: list[str] = []

    async def send(self, request: object, declaration: object) -> ClusterResult:
        node_id = declaration.node.id
        self.node_ids.append(node_id)
        outcome = self.outcomes[node_id]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_explanation_direct_remote_success_uses_transport_lifecycle_facts() -> None:
    transport = ScriptedExplanationRemoteTransport(
        {"remote": ClusterResult(content="remote", adapter="remote", node_id="wrong")}
    )
    account = asyncio.run(
        evaluate_actual_request(
            "chat",
            "private prompt",
            node_registry=NodeRegistry(),
            adapter_registry=AdapterRegistry(),
            remote_registry=build_remote_node_declaration_registry(
                [create_remote_declaration("remote", "http://remote.test", ("chat",))]
            ),
            remote_transport=transport,
        )
    )

    assert account["status"] == "succeeded"
    assert account["routing"]["local_execution_permission"] == "not-applicable"
    assert account["routing"]["candidate_consideration"] == "executed"
    assert account["lifecycle"] == {
        "candidates": [
            {
                "family": "declared-remote",
                "node_id": "remote",
                "fact": "transport-invoked",
            }
        ],
        "continuations": [],
        "final_node_id": "remote",
    }
    assert transport.node_ids == ["remote"]


def test_explanation_local_denial_continues_remotely_without_local_invocation() -> None:
    nodes, adapters, adapter = create_local_registries(
        RuntimeResult(content="unused", adapter="recording")
    )
    transport = ScriptedExplanationRemoteTransport(
        {"remote": ClusterResult(content="remote", adapter="remote", node_id="wrong")}
    )

    async def run() -> dict[str, object]:
        intervals = ExecutionIntervalCardinality()
        assert await intervals.try_enter()
        account = await evaluate_actual_request(
            "chat",
            "private prompt",
            node_registry=nodes,
            adapter_registry=adapters,
            remote_registry=build_remote_node_declaration_registry(
                [create_remote_declaration("remote", "http://remote.test", ("chat",))]
            ),
            remote_transport=transport,
            execution_intervals=intervals,
        )
        assert intervals.value == 1
        await intervals.exit()
        return account

    account = asyncio.run(run())
    assert account["status"] == "succeeded"
    assert account["routing"]["local_execution_permission"] == "denied"
    assert account["routing"]["candidate_consideration"] == "ended"
    assert adapter.chat_calls == 0
    assert account["lifecycle"] == {
        "candidates": [
            {
                "family": "local",
                "node_id": "test-local",
                "fact": "execution-permission-denied",
            },
            {
                "family": "declared-remote",
                "node_id": "remote",
                "fact": "transport-invoked",
            },
        ],
        "continuations": [
            {"node_id": "test-local", "reason": "local-execution-permission-denied"}
        ],
        "final_node_id": "remote",
    }


def test_explanation_pretransmission_local_unavailability_continues_remotely() -> None:
    nodes, adapters, adapter = create_local_registries(
        RuntimeConnectionUnavailableBeforeRequestError("private unavailable")
    )
    transport = ScriptedExplanationRemoteTransport(
        {"remote": ClusterResult(content="remote", adapter="remote", node_id="wrong")}
    )
    account = asyncio.run(
        evaluate_actual_request(
            "chat",
            "private prompt",
            node_registry=nodes,
            adapter_registry=adapters,
            remote_registry=build_remote_node_declaration_registry(
                [create_remote_declaration("remote", "http://remote.test", ("chat",))]
            ),
            remote_transport=transport,
        )
    )

    assert account["status"] == "succeeded"
    assert account["routing"]["local_execution_permission"] == "granted"
    assert account["routing"]["candidate_consideration"] == "executed"
    assert account["lifecycle"]["continuations"] == [
        {
            "node_id": "test-local",
            "reason": "local-runtime-connection-unavailable-before-request",
        }
    ]
    assert account["lifecycle"]["candidates"] == [
        {
            "family": "local",
            "node_id": "test-local",
            "fact": "execution-permission-granted",
        },
        {"family": "local", "node_id": "test-local", "fact": "adapter-invoked"},
        {
            "family": "declared-remote",
            "node_id": "remote",
            "fact": "transport-invoked",
        },
    ]
    assert account["lifecycle"]["final_node_id"] == "remote"
    assert adapter.chat_calls == 1
    assert transport.node_ids == ["remote"]


def test_explanation_remote_permission_exhaustion_preserves_failed_lifecycle() -> None:
    transport = ScriptedExplanationRemoteTransport(
        {
            "remote-a": RemoteExecutionPermissionDeniedError("private refusal"),
            "remote-b": RemoteExecutionPermissionDeniedError("private refusal"),
        }
    )
    account = asyncio.run(
        evaluate_actual_request(
            "chat",
            "private prompt",
            node_registry=NodeRegistry(),
            adapter_registry=AdapterRegistry(),
            remote_registry=build_remote_node_declaration_registry(
                [
                    create_remote_declaration("remote-a", "http://a.test", ("chat",)),
                    create_remote_declaration("remote-b", "http://b.test", ("chat",)),
                ]
            ),
            remote_transport=transport,
        )
    )

    assert account["failure"] == EXECUTION_PERMISSION_DENIED_FAILURE
    assert account["routing"]["local_execution_permission"] == "not-applicable"
    assert account["routing"]["candidate_consideration"] == "executed"
    assert account["lifecycle"] == {
        "candidates": [
            {
                "family": "declared-remote",
                "node_id": "remote-a",
                "fact": "transport-invoked",
            },
            {
                "family": "declared-remote",
                "node_id": "remote-a",
                "fact": "execution-permission-refused",
            },
            {
                "family": "declared-remote",
                "node_id": "remote-b",
                "fact": "transport-invoked",
            },
            {
                "family": "declared-remote",
                "node_id": "remote-b",
                "fact": "execution-permission-refused",
            },
        ],
        "continuations": [
            {"node_id": "remote-a", "reason": "remote-execution-permission-refused"}
        ],
        "final_node_id": None,
    }
    assert transport.node_ids == ["remote-a", "remote-b"]


def test_explanation_ordered_remote_connection_continuation_is_same_request() -> None:
    transport = ScriptedExplanationRemoteTransport(
        {
            "remote-a": RuntimeConnectionUnavailableBeforeRequestError(
                "private unavailable"
            ),
            "remote-b": ClusterResult(
                content="remote", adapter="remote", node_id="wrong"
            ),
        }
    )
    account = asyncio.run(
        evaluate_actual_request(
            "chat",
            "private prompt",
            node_registry=NodeRegistry(),
            adapter_registry=AdapterRegistry(),
            remote_registry=build_remote_node_declaration_registry(
                [
                    create_remote_declaration("remote-a", "http://a.test", ("chat",)),
                    create_remote_declaration("remote-b", "http://b.test", ("chat",)),
                ]
            ),
            remote_transport=transport,
        )
    )

    assert account["status"] == "succeeded"
    assert account["lifecycle"] == {
        "candidates": [
            {
                "family": "declared-remote",
                "node_id": "remote-a",
                "fact": "transport-invoked",
            },
            {
                "family": "declared-remote",
                "node_id": "remote-b",
                "fact": "transport-invoked",
            },
        ],
        "continuations": [
            {
                "node_id": "remote-a",
                "reason": "remote-runtime-connection-unavailable-before-request",
            }
        ],
        "final_node_id": "remote-b",
    }
    assert transport.node_ids == ["remote-a", "remote-b"]


def test_explanation_local_pretransmission_without_remote_has_no_continuation() -> None:
    nodes, adapters, _ = create_local_registries(
        RuntimeConnectionUnavailableBeforeRequestError("private unavailable")
    )

    account = asyncio.run(
        evaluate_actual_request(
            "chat",
            "private prompt",
            node_registry=nodes,
            adapter_registry=adapters,
            remote_registry=build_remote_node_declaration_registry([]),
        )
    )

    assert account["failure"] == RUNTIME_UNAVAILABLE_FAILURE
    assert account["lifecycle"]["continuations"] == []


def test_explanation_remote_connection_exhaustion_continues_only_to_next_remote() -> (
    None
):
    transport = ScriptedExplanationRemoteTransport(
        {
            "remote-a": RuntimeConnectionUnavailableBeforeRequestError(
                "private unavailable"
            ),
            "remote-b": RuntimeConnectionUnavailableBeforeRequestError(
                "private unavailable"
            ),
        }
    )

    account = asyncio.run(
        evaluate_actual_request(
            "chat",
            "private prompt",
            node_registry=NodeRegistry(),
            adapter_registry=AdapterRegistry(),
            remote_registry=build_remote_node_declaration_registry(
                [
                    create_remote_declaration("remote-a", "http://a.test", ("chat",)),
                    create_remote_declaration("remote-b", "http://b.test", ("chat",)),
                ]
            ),
            remote_transport=transport,
        )
    )

    assert account["failure"] == RUNTIME_UNAVAILABLE_FAILURE
    assert account["lifecycle"]["continuations"] == [
        {
            "node_id": "remote-a",
            "reason": "remote-runtime-connection-unavailable-before-request",
        }
    ]
    assert transport.node_ids == ["remote-a", "remote-b"]


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _tiny_png() -> bytes:
    return b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)),
            _png_chunk(b"IDAT", zlib.compress(b"\0\0\0\0")),
            _png_chunk(b"IEND", b""),
        )
    )


class ShapeAdapter:
    name = "shape-test"

    def __init__(self, capability: str, outcome: object) -> None:
        self.capability = capability
        self.outcome = outcome
        self.requests: list[object] = []

    def health(self) -> AdapterHealth:
        return AdapterHealth(available=True)

    def capabilities(self) -> list[Capability]:
        return [Capability(name=self.capability)]

    def _respond(self, request: object) -> object:
        self.requests.append(request)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome

    async def chat(self, request: ClusterRequest) -> RuntimeResult:
        return self._respond(request)  # type: ignore[return-value]

    async def summarize(self, request: SummarizeRequest) -> RuntimeResult:
        return self._respond(request)  # type: ignore[return-value]

    async def classify(self, request: ClassifyRequest) -> str:
        return self._respond(request)  # type: ignore[return-value]

    async def generate_image(self, request: ImageGenerationRequest) -> bytes:
        return self._respond(request)  # type: ignore[return-value]


def _shape_registries(capability: str, adapter: ShapeAdapter):
    node = NodeDescription(
        id="shape-local",
        name="shape local",
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name=capability)],
        adapters=[adapter.name],
    )
    return NodeRegistry([node]), AdapterRegistry([adapter])


def test_summarize_explanation_uses_real_request_and_lifecycle() -> None:
    adapter = ShapeAdapter(
        "summarize", RuntimeResult(content="summary", adapter="shape-test")
    )
    nodes, adapters = _shape_registries("summarize", adapter)
    account = asyncio.run(
        evaluate_actual_request(
            "summarize",
            "private source text",
            node_registry=nodes,
            adapter_registry=adapters,
        )
    )
    assert len(adapter.requests) == 1
    assert isinstance(adapter.requests[0], SummarizeRequest)
    assert not isinstance(adapter.requests[0], ClusterRequest)
    assert adapter.requests[0].text == "private source text"
    assert adapter.requests[0].constraints.local_only is False
    assert account["result"]["content"] == "summary"
    assert account["routing"]["requested_capability"] == "summarize"
    assert account["lifecycle"]["candidates"][-1]["fact"] == "adapter-invoked"
    assert "private source text" not in json.dumps(account)


def test_classify_explanation_preserves_labels_and_omits_private_input() -> None:
    adapter = ShapeAdapter("classify", "alpha")
    nodes, adapters = _shape_registries("classify", adapter)
    request = ClassifyRequest(
        text="private classification input",
        labels=["alpha", "beta"],
        constraints=RequestConstraints(local_only=False),
    )
    account = asyncio.run(
        _evaluate_ordinary_request(
            request, node_registry=nodes, adapter_registry=adapters
        )
    )
    assert adapter.requests == [request]
    assert request.labels == ["alpha", "beta"]
    assert request.capability.name == "classify"
    assert request.constraints.prefer_fast_response is False
    assert request.constraints.min_context_size is None
    assert account["status"] == "succeeded"
    assert account["result"] == {"node_id": "shape-local"}
    assert account["lifecycle"]["final_node_id"] == "shape-local"
    assert account["lifecycle"]["candidates"][-1]["fact"] == "adapter-invoked"
    assert "private classification input" not in json.dumps(account)
    assert "alpha" not in json.dumps(account)
    assert record_for_account(account) == {
        "status": "succeeded",
        "requested_capability": "classify",
        "selected_candidate_family": "local",
        "outcome_rule": "local-only",
        "failure_status": None,
    }


def test_code_explanation_uses_bounded_textual_request_without_workspace() -> None:
    adapter = ShapeAdapter(
        "code", RuntimeResult(content="safe answer", adapter="shape-test")
    )
    nodes, adapters = _shape_registries("code", adapter)
    account = asyncio.run(
        evaluate_actual_request(
            "code",
            "private code source",
            node_registry=nodes,
            adapter_registry=adapters,
        )
    )
    assert len(adapter.requests) == 1
    request = adapter.requests[0]
    assert isinstance(request, ClusterRequest)
    assert request.capability.name == "code"
    assert len(request.messages) == 1
    assert request.messages[0] == ChatMessage(
        role="user", content="private code source"
    )
    assert account["result"]["content"] == "safe answer"
    assert account["lifecycle"]["candidates"][-1]["fact"] == "adapter-invoked"
    assert "private code source" not in json.dumps(account)


def test_image_explanation_uses_real_request_without_serializing_png() -> None:
    image = _tiny_png()
    adapter = ShapeAdapter("image-generation", image)
    nodes, _ = _shape_registries("image-generation", adapter)
    adapters = AdapterRegistry(
        [adapter],
        local_capability_bindings=LocalCapabilityBindings(
            [LocalCapabilityBinding(frozenset({"image-generation"}), adapter)]
        ),
    )
    account = asyncio.run(
        evaluate_actual_request(
            "image-generation",
            "private image instruction",
            node_registry=nodes,
            adapter_registry=adapters,
        )
    )
    assert len(adapter.requests) == 1
    request = adapter.requests[0]
    assert isinstance(request, ImageGenerationRequest)
    assert request.instruction == "private image instruction"
    assert request.width is None and request.height is None
    assert request.constraints.local_only is False
    assert account["status"] == "succeeded"
    assert account["result"] == {"node_id": "shape-local"}
    assert account["routing"]["selected_candidate_family"] == "local"
    assert account["lifecycle"]["candidates"][-1]["fact"] == "adapter-invoked"
    serialized = json.dumps(account)
    assert "private image instruction" not in serialized
    assert "image_bytes" not in serialized
    assert "content" not in account["result"]
    assert record_for_account(account) == {
        "status": "succeeded",
        "requested_capability": "image-generation",
        "selected_candidate_family": "local",
        "outcome_rule": "local-only",
        "failure_status": None,
    }


def test_summarize_pretransmission_fallback_uses_same_lifecycle() -> None:
    adapter = ShapeAdapter(
        "summarize",
        RuntimeConnectionUnavailableBeforeRequestError("private local failure"),
    )
    nodes, adapters = _shape_registries("summarize", adapter)
    transport = ScriptedExplanationRemoteTransport(
        {"remote": ClusterResult(content="summary", adapter="remote", node_id="wrong")}
    )
    account = asyncio.run(
        evaluate_actual_request(
            "summarize",
            "private source text",
            node_registry=nodes,
            adapter_registry=adapters,
            remote_registry=build_remote_node_declaration_registry(
                [
                    create_remote_declaration(
                        "remote", "http://remote.test", ("summarize",)
                    )
                ]
            ),
            remote_transport=transport,
        )
    )
    assert isinstance(adapter.requests[0], SummarizeRequest)
    assert transport.node_ids == ["remote"]
    assert account["result"]["node_id"] == "remote"
    assert account["lifecycle"]["continuations"] == [
        {
            "node_id": "shape-local",
            "reason": "local-runtime-connection-unavailable-before-request",
        }
    ]
    assert "private source text" not in json.dumps(account)


def test_image_remote_fallback_keeps_real_shape_and_result_private() -> None:
    adapter = ShapeAdapter(
        "image-generation",
        RuntimeConnectionUnavailableBeforeRequestError("private local failure"),
    )
    nodes, adapters = _shape_registries("image-generation", adapter)
    image = _tiny_png()
    transport = ScriptedExplanationRemoteTransport(
        {"remote": ImageGenerationResult(image_bytes=image, node_id="wrong")}
    )
    account = asyncio.run(
        evaluate_actual_request(
            "image-generation",
            "private image instruction",
            node_registry=nodes,
            adapter_registry=adapters,
            remote_registry=build_remote_node_declaration_registry(
                [
                    create_remote_declaration(
                        "remote", "http://remote.test", ("image-generation",)
                    )
                ]
            ),
            remote_transport=transport,
        )
    )
    assert isinstance(adapter.requests[0], ImageGenerationRequest)
    assert transport.node_ids == ["remote"]
    assert account["result"] == {"node_id": "remote"}
    assert account["lifecycle"]["final_node_id"] == "remote"
    assert account["lifecycle"]["continuations"] == [
        {
            "node_id": "shape-local",
            "reason": "local-runtime-connection-unavailable-before-request",
        }
    ]
    assert "image_bytes" not in json.dumps(account)
    assert "private image instruction" not in json.dumps(account)


def test_public_classify_explanation_requires_unavailable_labels(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--capability", "classify", "--message", "private input"])
    assert raised.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "requires labels" in captured.err
    assert "private input" not in captured.err
