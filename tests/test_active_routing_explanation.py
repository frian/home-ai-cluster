"""RFC-0148 root client contract over the RFC-0147 loopback carrier."""

import json
from collections.abc import Callable

import httpx
import pytest

from home_ai_cluster import command
from home_ai_cluster.commands import active_routing_explanation as client

URL = "http://127.0.0.1:25042/diagnostics/static-routing-explanation"
RESULT = {
    "capability": "chat",
    "local_only": False,
    "local_eligible": False,
    "eligible_remote_node_ids": [],
    "remotes_excluded_by_local_only": False,
    "initial_selection": None,
}


def _run(
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    handler: Callable[[httpx.Request], httpx.Response],
) -> tuple[int, str, str, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    def factory(**kwargs: object) -> httpx.Client:
        assert kwargs == {
            "timeout": client._TIMEOUT_SECONDS,
            "follow_redirects": False,
            "trust_env": False,
        }
        return httpx.Client(transport=httpx.MockTransport(record), **kwargs)

    original = command._COMMANDS["explain-active-routing"]
    command._COMMANDS["explain-active-routing"] = lambda args: client.main(
        args, _client_factory=factory
    )
    try:
        try:
            command.main(["explain-active-routing", *argv])
        except SystemExit as error:
            code = error.code
        else:
            code = 0
    finally:
        command._COMMANDS["explain-active-routing"] = original
    output = capsys.readouterr()
    return code, output.out, output.err, requests


@pytest.mark.parametrize("local_only", [False, True])
def test_one_post_exact_body_and_compact_complete_result(
    capsys: pytest.CaptureFixture[str], local_only: bool
) -> None:
    result = {**RESULT, "local_only": local_only}
    argv = ["--capability", "chat", *(["--local-only"] if local_only else [])]
    code, out, err, requests = _run(
        capsys, argv, lambda request: httpx.Response(200, json=result)
    )

    assert (code, out, err) == (0, json.dumps(result, separators=(",", ":")) + "\n", "")
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert str(requests[0].url) == URL
    assert json.loads(requests[0].content) == {
        "capability": "chat",
        "local_only": local_only,
    }


@pytest.mark.parametrize(
    "selection", [{"kind": "local"}, {"kind": "declared_remote", "node_id": "remote-a"}]
)
def test_valid_selection_variants(
    capsys: pytest.CaptureFixture[str], selection: dict[str, str]
) -> None:
    result = {
        **RESULT,
        "local_eligible": selection["kind"] == "local",
        "eligible_remote_node_ids": ["remote-a"],
        "initial_selection": selection,
    }
    code, out, err, requests = _run(
        capsys,
        ["--capability", "chat"],
        lambda request: httpx.Response(200, json=result),
    )
    assert code == 0 and err == "" and len(requests) == 1
    assert json.loads(out) == result


@pytest.mark.parametrize(
    "changes",
    [
        {"local_eligible": True},
        {
            "local_eligible": True,
            "eligible_remote_node_ids": ["remote-a"],
            "initial_selection": {"kind": "declared_remote", "node_id": "remote-a"},
        },
        {"eligible_remote_node_ids": ["remote-a"]},
        {
            "eligible_remote_node_ids": ["remote-a", "remote-b"],
            "initial_selection": {"kind": "declared_remote", "node_id": "remote-b"},
        },
        {
            "eligible_remote_node_ids": ["remote-a"],
            "initial_selection": {"kind": "declared_remote", "node_id": "other"},
        },
        {"local_only": True, "eligible_remote_node_ids": ["remote-a"]},
        {
            "eligible_remote_node_ids": ["remote-a"],
            "remotes_excluded_by_local_only": True,
            "initial_selection": {"kind": "declared_remote", "node_id": "remote-a"},
        },
        {"remotes_excluded_by_local_only": True},
        {"eligible_remote_node_ids": [""]},
    ],
)
def test_semantically_invalid_success_is_rejected(
    capsys: pytest.CaptureFixture[str], changes: dict[str, object]
) -> None:
    result = {**RESULT, **changes}
    argv = ["--capability", "chat", *(["--local-only"] if result["local_only"] else [])]
    code, out, err, requests = _run(
        capsys, argv, lambda request: httpx.Response(200, json=result)
    )
    assert (code, out, err, len(requests)) == (
        1,
        "",
        "error: invalid routing explanation response\n",
        1,
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"local_eligible": True, "initial_selection": {"kind": "local"}},
        {
            "local_eligible": True,
            "eligible_remote_node_ids": ["remote-a"],
            "initial_selection": {"kind": "local"},
        },
        {
            "local_only": True,
            "local_eligible": True,
            "eligible_remote_node_ids": ["remote-a"],
            "remotes_excluded_by_local_only": True,
            "initial_selection": {"kind": "local"},
        },
        {
            "eligible_remote_node_ids": ["remote-a", "remote-b"],
            "initial_selection": {"kind": "declared_remote", "node_id": "remote-a"},
        },
        {
            "local_only": True,
            "eligible_remote_node_ids": ["remote-a"],
            "remotes_excluded_by_local_only": True,
        },
        {},
    ],
)
def test_valid_selection_relationships_remain_accepted(
    capsys: pytest.CaptureFixture[str], changes: dict[str, object]
) -> None:
    result = {**RESULT, **changes}
    argv = ["--capability", "chat", *(["--local-only"] if result["local_only"] else [])]
    code, out, err, requests = _run(
        capsys, argv, lambda request: httpx.Response(200, json=result)
    )
    assert (code, out, err, len(requests)) == (
        0,
        json.dumps(result, separators=(",", ":")) + "\n",
        "",
        1,
    )


@pytest.mark.parametrize(
    "argv",
    [[], ["--capability", "unknown"], ["--capability", "chat", "--host", "remote"]],
)
def test_invalid_input_prevents_http(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    assert _run(capsys, argv, lambda request: pytest.fail("unexpected HTTP")) == (
        2,
        "",
        "error: invalid routing explanation input\n",
        [],
    )


@pytest.mark.parametrize(
    "capability", ["chat", "summarize", "classify", "code", "image-generation"]
)
def test_every_accepted_capability_passes_local_validation(
    capsys: pytest.CaptureFixture[str], capability: str
) -> None:
    code, out, err, requests = _run(
        capsys,
        ["--capability", capability],
        lambda request: httpx.Response(200, json={**RESULT, "capability": capability}),
    )
    assert code == 0 and err == "" and len(requests) == 1
    assert json.loads(out)["capability"] == capability


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (httpx.Response(422, text="private body"), "routing explanation rejected"),
        (httpx.Response(503, text="private body"), "routing explanation unavailable"),
        (
            httpx.Response(302, headers={"location": "http://private"}),
            "routing explanation failed",
        ),
        (httpx.Response(500, text="private body"), "routing explanation failed"),
        (httpx.Response(200, text="not json"), "invalid routing explanation response"),
        (
            httpx.Response(200, json={"capability": "chat"}),
            "invalid routing explanation response",
        ),
        (
            httpx.Response(200, json={**RESULT, "capability": "code"}),
            "invalid routing explanation response",
        ),
        (
            httpx.Response(200, json={**RESULT, "local_eligible": "false"}),
            "invalid routing explanation response",
        ),
        (
            httpx.Response(
                200,
                json={
                    **RESULT,
                    "initial_selection": {
                        "kind": "declared_remote",
                        "node_id": "missing",
                    },
                },
            ),
            "invalid routing explanation response",
        ),
        (
            httpx.Response(
                200, json={**RESULT, "initial_selection": {"kind": "local"}}
            ),
            "invalid routing explanation response",
        ),
        (
            httpx.Response(200, json={**RESULT, "extra": "private"}),
            "invalid routing explanation response",
        ),
    ],
)
def test_http_and_response_failures_are_bounded(
    capsys: pytest.CaptureFixture[str], response: httpx.Response, expected: str
) -> None:
    code, out, err, requests = _run(
        capsys, ["--capability", "chat"], lambda request: response
    )
    assert (code, out, err, len(requests)) == (1, "", f"error: {expected}\n", 1)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (httpx.ConnectError("private address"), "ordinary cluster unavailable"),
        (httpx.ReadTimeout("private address"), "ordinary cluster unavailable"),
        (httpx.RemoteProtocolError("private address"), "routing explanation failed"),
        (RuntimeError("private address"), "routing explanation failed"),
    ],
)
def test_transport_failure_has_no_retry_or_leak(
    capsys: pytest.CaptureFixture[str], error: Exception, expected: str
) -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise error

    code, out, err, requests = _run(capsys, ["--capability", "chat"], fail)
    assert (code, out, err, len(requests)) == (1, "", f"error: {expected}\n", 1)
