import asyncio
import json

import pytest

import home_ai_cluster.commands.actual_request_explanation as request_explanation
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
    create_request,
    evaluate_actual_request,
    main,
)
from home_ai_cluster.core.execution_intervals import ExecutionIntervalCardinality
from home_ai_cluster.core.models import (
    AdapterHealth,
    Capability,
    ClusterRequest,
    NodeDescription,
    NodeHealth,
    RuntimeResult,
)
from home_ai_cluster.core.orchestrator import NoSelectableRoutingCandidateError
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import build_remote_node_declaration_registry


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


def test_create_request_preserves_message_and_local_only_default() -> None:
    request = create_request("chat", "Hello")

    assert request.capability.name == "chat"
    assert request.messages[0].content == "Hello"
    assert request.constraints.local_only is True


def test_successful_account_has_the_structured_rfc_0034_projection() -> None:
    account, adapter = evaluate(
        RuntimeResult(
            content="explained response", adapter="recording", model="test-model"
        )
    )

    assert list(account) == ["status", "routing", "result", "failure"]
    assert account == {
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


def test_no_selectable_candidate_preserves_exception_routing_and_does_not_execute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    select_once = request_explanation.select_automatic_capability_routing_candidate

    def raise_no_selectable_candidate(
        request: ClusterRequest, candidates: object
    ) -> object:
        selection = select_once(request, candidates)  # type: ignore[arg-type]
        raise NoSelectableRoutingCandidateError(selection.explanation)

    monkeypatch.setattr(
        request_explanation,
        "select_automatic_capability_routing_candidate",
        raise_no_selectable_candidate,
    )

    account, adapter = evaluate(
        RuntimeResult(content="unused", adapter="recording"),
        requested_capability="vision",
    )

    assert account == {
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


def test_evaluate_selects_and_executes_at_most_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    select = request_explanation.select_automatic_capability_routing_candidate
    selections = 0

    def record_selection(request: ClusterRequest, candidates: object) -> object:
        nonlocal selections
        selections += 1
        return select(request, candidates)  # type: ignore[arg-type]

    monkeypatch.setattr(
        request_explanation,
        "select_automatic_capability_routing_candidate",
        record_selection,
    )

    account, adapter = evaluate(RuntimeResult(content="response", adapter="recording"))

    assert account["status"] == "succeeded"
    assert selections == 1
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
    assert account["result"] is None
    assert account["failure"] == EXECUTION_FAILED_FAILURE
    serialized = json.dumps(account)
    assert "private prompt content" not in serialized
    assert "private-host" not in serialized
    assert "RuntimeError" not in serialized
    assert adapter.chat_calls == 1


def test_evaluate_uses_default_local_registries_and_empty_remote_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    nodes, adapters, _ = create_local_registries(
        RuntimeResult(content="response", adapter="recording")
    )
    calls: list[str] = []

    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.create_static_local_node_registry",
        lambda: calls.append("nodes") or nodes,
    )
    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.create_static_runtime_adapter_registry",
        lambda: calls.append("adapters") or adapters,
    )
    monkeypatch.setattr(
        "home_ai_cluster.commands.actual_request_explanation.build_remote_node_declaration_registry",
        lambda declarations: (
            calls.append("remotes")
            or build_remote_node_declaration_registry(declarations)
        ),
    )

    account = asyncio.run(evaluate_actual_request("chat", "Hello"))

    assert calls == ["nodes", "adapters", "remotes"]
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
