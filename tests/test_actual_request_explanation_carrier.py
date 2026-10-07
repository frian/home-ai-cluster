"""RFC-0149: one explained execution in the active ordinary application."""

import asyncio
from types import SimpleNamespace

import httpx
import pytest
from starlette.requests import Request

from home_ai_cluster.adapters.base import RuntimeConnectionUnavailableBeforeRequestError
from home_ai_cluster.api.actual_request_explanation import _explanation
from home_ai_cluster.api.client_disconnect import ConfirmedClientDisconnect
from home_ai_cluster.core.execution_intervals import ExecutionIntervalCardinality
from home_ai_cluster.core.models import (
    Capability,
    ClusterRequest,
    ClusterResult,
    NodeDescription,
    NodeHealth,
    RequestConstraints,
    RuntimeResult,
)
from home_ai_cluster.core.ordinary_request_lifecycle import OrdinaryRequestLifecycle
from home_ai_cluster.core.registry import AdapterRegistry, NodeRegistry
from home_ai_cluster.core.remote_node import (
    RemoteNodeDeclaration,
    RemoteNodeDeclarationRegistry,
)
from home_ai_cluster.core.remote_transport import RemoteExecutionPermissionDeniedError
from home_ai_cluster.main import create_app, create_receiver_app
from home_ai_cluster.openai_compatibility import create_openai_compatibility_app
from home_ai_cluster.web.trusted_lan_browser import create_trusted_lan_browser_app

ROUTE = "/diagnostics/actual-request-explanation"
SECRET = "private prompt marker"


class Adapter:
    name = "fake"

    def __init__(self, outcome: Exception | None = None):
        self.outcome = outcome
        self.calls = []

    def capabilities(self):
        return [
            Capability(name=name) for name in ("chat", "code", "summarize", "classify")
        ]

    def health(self):
        raise AssertionError("unexpected health probe")

    async def _answer(self, request):
        self.calls.append(request)
        if self.outcome:
            raise self.outcome
        return RuntimeResult(content="answer", adapter=self.name, model="model")

    async def chat(self, request):
        return await self._answer(request)

    async def summarize(self, request):
        return await self._answer(request)

    async def classify(self, request):
        self.calls.append(request)
        return request.labels[0]


class Transport:
    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.calls = []

    async def send(self, request, declaration):
        node_id = declaration.node.id
        self.calls.append((node_id, request))
        outcome = self.outcomes[node_id]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class CountingIntervals(ExecutionIntervalCardinality):
    def __init__(self):
        super().__init__()
        self.enter_calls = 0

    async def try_enter(self):
        self.enter_calls += 1
        return await super().try_enter()


def node(node_id, capabilities=("chat", "code", "summarize", "classify")):
    return NodeDescription(
        id=node_id,
        name=node_id,
        availability="available",
        health=NodeHealth(healthy=True),
        capabilities=[Capability(name=name) for name in capabilities],
        adapters=["fake"],
    )


def app_for(*, adapter=None, remotes=(), outcomes=None, intervals=None):
    adapter = Adapter() if adapter is None else adapter
    intervals = ExecutionIntervalCardinality() if intervals is None else intervals
    nodes = NodeRegistry([node("local")]) if adapter else NodeRegistry()
    adapters = AdapterRegistry([adapter]) if adapter else AdapterRegistry()
    composition = SimpleNamespace(
        node_registry=nodes, adapter_registry=adapters, execution_intervals=intervals
    )
    transport = Transport(outcomes or {})
    wiring = None
    if remotes:
        wiring = SimpleNamespace(
            node_registry=nodes,
            adapter_registry=adapters,
            remote_registry=RemoteNodeDeclarationRegistry(
                [
                    RemoteNodeDeclaration(
                        node=node(remote_id),
                        transport_address=f"http://{remote_id}.invalid",
                    )
                    for remote_id in remotes
                ]
            ),
            remote_transport=transport,
            execution_intervals=intervals,
        )
    app = create_app(
        local_app_composition=composition,
        static_remote_wiring=wiring if len(remotes) == 1 else None,
        static_remote_collection_wiring=wiring if len(remotes) > 1 else None,
    )
    return app, adapter, transport, intervals


def post(app, body):
    async def call():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.post(ROUTE, json=body)

    return asyncio.run(call())


def chat(*, local_only=True, kind="chat"):
    return {
        "kind": kind,
        "local_only": local_only,
        "request": {
            "capability": kind,
            "messages": [{"role": "user", "content": SECRET}],
        },
    }


@pytest.mark.parametrize(
    ("body", "expected_result"),
    [
        (
            chat(),
            {
                "content": "answer",
                "adapter": "fake",
                "model": "model",
                "node_id": "local",
            },
        ),
        (
            chat(kind="code"),
            {
                "content": "answer",
                "adapter": "fake",
                "model": "model",
                "node_id": "local",
            },
        ),
        (
            {"kind": "summarize", "local_only": True, "request": {"text": SECRET}},
            {
                "content": "answer",
                "adapter": "fake",
                "model": "model",
                "node_id": "local",
            },
        ),
        (
            {
                "kind": "classify",
                "local_only": True,
                "request": {"text": SECRET, "labels": ["first", "second"]},
            },
            {"selected_label": "first", "node_id": "local"},
        ),
    ],
)
def test_local_capabilities_execute_once(body, expected_result):
    app, adapter, _, intervals = app_for(intervals=CountingIntervals())
    response = post(app, body)
    assert response.status_code == 200
    account = response.json()
    assert set(account) == {"status", "result", "failure", "explanation"}
    assert account["status"] == "succeeded"
    assert account["failure"] is None
    assert account["result"] == expected_result
    assert len(adapter.calls) == 1
    assert intervals.value == 0
    assert intervals.enter_calls == 1
    explanation = account["explanation"]
    assert set(explanation) == {
        "requested_capability",
        "local_only",
        "initial_selection",
        "candidate_facts",
        "continuations",
        "final_node_id",
    }
    assert explanation["initial_selection"] == {"kind": "local"}
    assert [fact["fact"] for fact in explanation["candidate_facts"]] == [
        "execution-permission-granted",
        "adapter-invoked",
    ]
    assert explanation["continuations"] == []
    assert explanation["final_node_id"] == "local"
    assert SECRET not in str(explanation)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda body: body.update(local_only=1),
        lambda body: body.update(extra="unexpected"),
        lambda body: body["request"].update(extra="unexpected"),
        lambda body: body["request"]["messages"][0].update(extra="unexpected"),
        lambda body: body["request"].update(capability="code"),
        lambda body: body.update(kind="image-generation"),
        lambda body: body.update(kind="unknown"),
        lambda body: body.update(request={"constraints": {"local_only": True}}),
    ],
)
def test_rejected_input_never_executes(mutation):
    app, adapter, _, _ = app_for()
    body = chat()
    mutation(body)
    response = post(app, body)
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid diagnostic input"}
    assert adapter.calls == []


@pytest.mark.parametrize("labels", [[], ["one"], ["same", "same"], ["", "other"]])
def test_invalid_classify_labels_never_execute(labels):
    app, adapter, _, _ = app_for()
    response = post(
        app,
        {
            "kind": "classify",
            "local_only": True,
            "request": {"text": SECRET, "labels": labels},
        },
    )
    assert response.status_code == 422
    assert adapter.calls == []


def test_normalized_content_bounds_apply_before_execution():
    app, adapter, _, _ = app_for()
    code_body = chat(kind="code")
    code_body["request"]["messages"][0]["content"] = "x" * 65_537
    assert post(app, code_body).status_code == 422
    assert (
        post(
            app,
            {
                "kind": "summarize",
                "local_only": True,
                "request": {"text": "x" * 65_537},
            },
        ).status_code
        == 422
    )
    assert (
        post(
            app,
            {
                "kind": "classify",
                "local_only": True,
                "request": {"text": SECRET, "labels": ["x" * 129, "other"]},
            },
        ).status_code
        == 422
    )
    assert adapter.calls == []


def test_active_permission_denial_is_terminal_without_remote():
    app, adapter, _, intervals = app_for()

    async def run():
        assert await intervals.try_enter()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.post(ROUTE, json=chat())
        await intervals.exit()
        return response

    account = asyncio.run(run()).json()
    assert account["status"] == "failed"
    assert account["result"] is None
    assert account["failure"] == {"status": "execution-permission-denied"}
    assert [fact["fact"] for fact in account["explanation"]["candidate_facts"]] == [
        "execution-permission-denied"
    ]
    assert account["explanation"]["continuations"] == []
    assert adapter.calls == []


def test_single_remote_after_local_denial_uses_active_permission():
    remote = ClusterResult(content="remote", adapter="remote", node_id="remote")
    app, adapter, transport, intervals = app_for(
        remotes=("remote",), outcomes={"remote": remote}
    )

    async def run():
        assert await intervals.try_enter()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.post(ROUTE, json=chat(local_only=False))
        await intervals.exit()
        return response

    account = asyncio.run(run()).json()
    assert account["status"] == "succeeded"
    assert account["result"]["content"] == "remote"
    assert [fact["fact"] for fact in account["explanation"]["candidate_facts"]] == [
        "execution-permission-denied",
        "transport-invoked",
    ]
    assert account["explanation"]["continuations"] == [
        {"node_id": "local", "reason": "local-execution-permission-denied"}
    ]
    assert adapter.calls == []
    assert len(transport.calls) == 1


def test_local_pretransmission_fallback_and_nonfallback_failure():
    remote = ClusterResult(content="remote", adapter="remote", node_id="remote")
    app, adapter, transport, _ = app_for(
        adapter=Adapter(RuntimeConnectionUnavailableBeforeRequestError("secret")),
        remotes=("remote",),
        outcomes={"remote": remote},
    )
    account = post(app, chat(local_only=False)).json()
    assert account["status"] == "succeeded"
    assert account["explanation"]["continuations"] == [
        {
            "node_id": "local",
            "reason": "local-runtime-connection-unavailable-before-request",
        }
    ]
    assert len(adapter.calls) == len(transport.calls) == 1

    app, adapter, transport, _ = app_for(
        adapter=Adapter(RuntimeError("secret raw error")),
        remotes=("remote",),
        outcomes={"remote": remote},
    )
    account = post(app, chat(local_only=False)).json()
    assert account["failure"] == {"status": "execution-failed"}
    assert account["explanation"]["continuations"] == []
    assert "secret raw error" not in str(account)
    assert len(adapter.calls) == 1
    assert transport.calls == []


def test_local_and_remote_families_remain_distinct_when_ids_match():
    app, _, transport, _ = app_for(
        adapter=Adapter(RuntimeConnectionUnavailableBeforeRequestError("unavailable")),
        remotes=("local",),
        outcomes={
            "local": ClusterResult(content="remote", adapter="remote", node_id="local")
        },
    )
    account = post(app, chat(local_only=False)).json()
    assert account["status"] == "succeeded"
    assert [fact["family"] for fact in account["explanation"]["candidate_facts"]] == [
        "local",
        "local",
        "declared-remote",
    ]
    assert len(transport.calls) == 1


def test_direct_and_ordered_remote_progression():
    remote = ClusterResult(content="second", adapter="remote", node_id="second")
    app, _, transport, _ = app_for(
        adapter=False,
        remotes=("first", "second"),
        outcomes={"first": RemoteExecutionPermissionDeniedError(), "second": remote},
    )
    account = post(app, chat(local_only=False)).json()
    assert account["status"] == "succeeded"
    assert account["explanation"]["initial_selection"] == {
        "kind": "declared_remote",
        "node_id": "first",
    }
    assert [fact["fact"] for fact in account["explanation"]["candidate_facts"]] == [
        "transport-invoked",
        "execution-permission-refused",
        "transport-invoked",
    ]
    assert account["explanation"]["continuations"] == [
        {"node_id": "first", "reason": "remote-execution-permission-refused"}
    ]
    assert account["explanation"]["final_node_id"] == "second"
    assert [item[0] for item in transport.calls] == ["first", "second"]


def test_final_remote_refusal_has_no_continuation():
    app, _, transport, _ = app_for(
        adapter=False,
        remotes=("remote",),
        outcomes={"remote": RemoteExecutionPermissionDeniedError()},
    )
    account = post(app, chat(local_only=False)).json()
    assert account["failure"] == {"status": "execution-permission-denied"}
    assert account["explanation"]["continuations"] == []
    assert [fact["fact"] for fact in account["explanation"]["candidate_facts"]] == [
        "transport-invoked",
        "execution-permission-refused",
    ]
    assert len(transport.calls) == 1


def test_local_only_never_contacts_remote():
    app, _, transport, _ = app_for(adapter=False, remotes=("remote",))
    account = post(app, chat(local_only=True)).json()
    assert account["failure"] == {"status": "no-selectable-candidate"}
    assert account["explanation"]["initial_selection"] is None
    assert transport.calls == []


def test_missing_or_ambiguous_composition_is_unavailable():
    assert post(create_app(), chat()).status_code == 503
    app, adapter, _, _ = app_for()
    app.state.static_remote_wiring = SimpleNamespace()
    app.state.static_remote_collection_wiring = SimpleNamespace()
    response = post(app, chat())
    assert response.status_code == 503
    assert adapter.calls == []


def test_public_projection_rejects_unrecognized_and_repeated_facts():
    request = ClusterRequest(
        messages=[{"role": "user", "content": SECRET}],
        capability=Capability(name="chat"),
        constraints=RequestConstraints(),
    )
    lifecycle = OrdinaryRequestLifecycle()
    lifecycle.selected_local()
    lifecycle.local_permission(True, "local")
    lifecycle.local_adapter_invoked("local")
    lifecycle.succeeded("local")
    lifecycle.candidates.append(dict(lifecycle.candidates[0]))
    with pytest.raises(ValueError):
        _explanation(request, lifecycle, succeeded=True)
    lifecycle.candidates.pop()
    lifecycle.candidates[0]["fact"] = "arbitrary"
    with pytest.raises(ValueError):
        _explanation(request, lifecycle, succeeded=True)


def test_route_is_owned_only_by_ordinary_app():
    app, _, _, _ = app_for()
    assert ROUTE in app.openapi()["paths"]
    alternatives = [
        create_receiver_app(local_app_composition=app.state.local_app_composition),
        create_trusted_lan_browser_app(app, host="127.0.0.1", port=25043),
        create_openai_compatibility_app(),
        create_app(include_static_routing_explanation=False),
    ]
    for alternative in alternatives:
        assert ROUTE not in alternative.openapi()["paths"]


def test_projection_failure_after_execution_is_500_without_replay(monkeypatch):
    from home_ai_cluster.api import actual_request_explanation as carrier

    app, adapter, _, _ = app_for()

    def broken(*args, **kwargs):
        raise ValueError("secret projection detail")

    monkeypatch.setattr(carrier, "_explanation", broken)
    response = post(app, chat())
    assert response.status_code == 500
    assert response.json() == {"detail": "Request explanation failed"}
    assert len(adapter.calls) == 1


def test_confirmed_disconnect_produces_no_completed_account():
    from home_ai_cluster.api.actual_request_explanation import (
        actual_request_explanation,
    )

    app, adapter, _, _ = app_for()
    body = chat()

    async def run():
        received = False

        async def receive():
            nonlocal received
            if not received:
                received = True
                import json

                return {
                    "type": "http.request",
                    "body": json.dumps(body).encode(),
                    "more_body": False,
                }
            return {"type": "http.disconnect"}

        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": ROUTE,
                "headers": [],
                "app": app,
            },
            receive=receive,
        )
        with pytest.raises(ConfirmedClientDisconnect):
            await actual_request_explanation(request)

    asyncio.run(run())
    assert adapter.calls == []


def test_ordered_remote_pretransmission_reason_and_exhaustion():
    unavailable = RuntimeConnectionUnavailableBeforeRequestError("secret remote")
    remote = ClusterResult(content="remote", adapter="remote", node_id="second")
    app, _, transport, _ = app_for(
        adapter=False,
        remotes=("first", "second"),
        outcomes={"first": unavailable, "second": remote},
    )
    account = post(app, chat(local_only=False)).json()
    assert account["status"] == "succeeded"
    assert account["explanation"]["continuations"] == [
        {
            "node_id": "first",
            "reason": "remote-runtime-connection-unavailable-before-request",
        }
    ]
    assert [item[0] for item in transport.calls] == ["first", "second"]

    app, _, transport, _ = app_for(
        adapter=False,
        remotes=("first", "second"),
        outcomes={
            "first": unavailable,
            "second": RemoteExecutionPermissionDeniedError(),
        },
    )
    account = post(app, chat(local_only=False)).json()
    assert account["failure"] == {"status": "runtime-unavailable"}
    assert account["explanation"]["continuations"] == [
        {
            "node_id": "first",
            "reason": "remote-runtime-connection-unavailable-before-request",
        }
    ]
    assert [item[0] for item in transport.calls] == ["first", "second"]


def test_projection_rejects_duplicate_and_arbitrary_continuation():
    request = ClusterRequest(
        messages=[{"role": "user", "content": SECRET}],
        capability=Capability(name="chat"),
        constraints=RequestConstraints(),
    )
    lifecycle = OrdinaryRequestLifecycle()
    lifecycle.selected_local()
    lifecycle.local_permission(False, "local")
    lifecycle.continued("local", "local-execution-permission-denied")
    lifecycle.remote_transport_invoked("remote")
    lifecycle.succeeded("remote")
    lifecycle.continued("local", "local-execution-permission-denied")
    with pytest.raises(ValueError):
        _explanation(request, lifecycle, succeeded=True)
    lifecycle.continuation_reasons[-1]["reason"] = "invented-reason"
    with pytest.raises(ValueError):
        _explanation(request, lifecycle, succeeded=True)


@pytest.mark.parametrize("recording_method", ["selected_local", "local_permission"])
def test_local_recording_failure_does_not_interrupt_execution_or_leak_interval(
    monkeypatch, recording_method
):
    intervals = CountingIntervals()
    app, adapter, _, _ = app_for(intervals=intervals)

    def broken(*args):
        raise RuntimeError("private recorder secret")

    monkeypatch.setattr(OrdinaryRequestLifecycle, recording_method, broken)
    response = post(app, chat())

    assert response.status_code == 500
    assert response.json() == {"detail": "Request explanation failed"}
    assert "private recorder secret" not in response.text
    assert intervals.enter_calls == 1
    assert intervals.value == 0
    assert len(adapter.calls) == 1


def test_direct_remote_recording_failure_does_not_suppress_transport(monkeypatch):
    remote = ClusterResult(content="remote", adapter="remote", node_id="remote")
    app, _, transport, _ = app_for(
        adapter=False, remotes=("remote",), outcomes={"remote": remote}
    )

    def broken(*args):
        raise RuntimeError("private recorder secret")

    monkeypatch.setattr(OrdinaryRequestLifecycle, "remote_transport_invoked", broken)
    response = post(app, chat(local_only=False))

    assert response.status_code == 500
    assert response.json() == {"detail": "Request explanation failed"}
    assert [node_id for node_id, _ in transport.calls] == ["remote"]


def test_ordered_continuation_recording_failure_preserves_progression(monkeypatch):
    remote = ClusterResult(content="second", adapter="remote", node_id="second")
    app, _, transport, _ = app_for(
        adapter=False,
        remotes=("first", "second"),
        outcomes={"first": RemoteExecutionPermissionDeniedError(), "second": remote},
    )

    def broken(*args):
        raise RuntimeError("private recorder secret")

    monkeypatch.setattr(OrdinaryRequestLifecycle, "continued", broken)
    response = post(app, chat(local_only=False))

    assert response.status_code == 500
    assert response.json() == {"detail": "Request explanation failed"}
    assert [node_id for node_id, _ in transport.calls] == ["first", "second"]


def test_ordinary_execution_failure_still_returns_completed_account():
    app, adapter, _, intervals = app_for(
        adapter=Adapter(RuntimeError("private execution secret")),
        intervals=CountingIntervals(),
    )
    response = post(app, chat())

    assert response.status_code == 200
    account = response.json()
    assert account["status"] == "failed"
    assert account["failure"] == {"status": "execution-failed"}
    assert account["result"] is None
    assert len(adapter.calls) == intervals.enter_calls == 1
    assert intervals.value == 0
    assert "private execution secret" not in response.text


def test_recording_failure_takes_precedence_over_ordinary_failure(monkeypatch):
    app, adapter, _, intervals = app_for(
        adapter=Adapter(RuntimeError("private execution secret")),
        intervals=CountingIntervals(),
    )

    def broken(*args):
        raise RuntimeError("private recorder secret")

    monkeypatch.setattr(OrdinaryRequestLifecycle, "selected_local", broken)
    response = post(app, chat())

    assert response.status_code == 500
    assert response.json() == {"detail": "Request explanation failed"}
    assert len(adapter.calls) == intervals.enter_calls == 1
    assert intervals.value == 0
    assert "private recorder secret" not in response.text
    assert "private execution secret" not in response.text


def test_projection_rejects_local_invocation_without_prior_grant():
    request = ClusterRequest(
        messages=[{"role": "user", "content": SECRET}],
        capability=Capability(name="chat"),
        constraints=RequestConstraints(),
    )
    lifecycle = OrdinaryRequestLifecycle()
    lifecycle.selected_local()
    lifecycle.local_adapter_invoked("local")
    lifecycle.succeeded("local")

    with pytest.raises(ValueError, match="prior permission"):
        _explanation(request, lifecycle, succeeded=True)
