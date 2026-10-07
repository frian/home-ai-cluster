"""RFC-0150's one-request client and public-account validation contract."""

import io
import json
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path

import httpx
import pytest

from home_ai_cluster.commands import active_request_explanation as client


def _account(kind: str = "chat", *, local_only: bool = False) -> dict:
    result = (
        {"selected_label": "A", "node_id": "local-1"}
        if kind == "classify"
        else {
            "content": "answer",
            "adapter": "adapter",
            "model": None,
            "node_id": "local-1",
        }
    )
    return {
        "status": "succeeded",
        "result": result,
        "failure": None,
        "explanation": {
            "requested_capability": kind,
            "local_only": local_only,
            "initial_selection": {"kind": "local"},
            "candidate_facts": [
                {
                    "family": "local",
                    "node_id": "local-1",
                    "fact": "execution-permission-granted",
                },
                {"family": "local", "node_id": "local-1", "fact": "adapter-invoked"},
            ],
            "continuations": [],
            "final_node_id": "local-1",
        },
    }


def _run(
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    response: httpx.Response
    | Exception
    | Callable[[httpx.Request], httpx.Response]
    | None = None,
    *,
    stdin: bytes = b"",
) -> tuple[int, str, str, list[httpx.Request], list[dict]]:
    requests: list[httpx.Request] = []
    options: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if isinstance(response, Exception):
            raise response
        if callable(response):
            return response(request)
        return response or httpx.Response(200, json=_account())

    def factory(**kwargs: object) -> httpx.Client:
        options.append(kwargs)
        return httpx.Client(transport=httpx.MockTransport(handler), **kwargs)

    try:
        client.main(argv, _client_factory=factory, _stdin=io.BytesIO(stdin))
    except SystemExit as error:
        code = error.code
    else:
        code = 0
    captured = capsys.readouterr()
    return code, captured.out, captured.err, requests, options


def test_root_help_lists_exactly_four_capability_subcommands(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as raised:
        client.main(["--help"])
    output = capsys.readouterr()
    assert raised.value.code == 0
    assert "{chat,code,summarize,classify}" in output.out
    assert "image-generation" not in output.out
    assert output.err == ""


@pytest.mark.parametrize("kind", ["chat", "code", "summarize", "classify"])
def test_exact_body_one_post_and_success_output(
    capsys: pytest.CaptureFixture[str], kind: str
) -> None:
    argv = [kind]
    if kind in {"chat", "code"}:
        argv.append("hello")
        payload = {
            "capability": kind,
            "messages": [{"role": "user", "content": "hello"}],
        }
    else:
        argv.extend(["--text", "hello"])
        payload = {"text": "hello"}
        if kind == "classify":
            argv.extend(["--label", "A", "--label", "B"])
            payload["labels"] = ["A", "B"]
    account = _account(kind)
    code, out, err, requests, options = _run(
        capsys, argv, httpx.Response(200, json=account)
    )
    assert (code, out, err) == (
        0,
        json.dumps(account, separators=(",", ":")) + "\n",
        "",
    )
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert str(requests[0].url) == client._URL
    assert json.loads(requests[0].content) == {
        "kind": kind,
        "local_only": False,
        "request": payload,
    }
    assert options == [
        {"timeout": 120.0, "follow_redirects": False, "trust_env": False}
    ]


@pytest.mark.parametrize("kind", ["chat", "code"])
def test_message_option_and_local_only(
    capsys: pytest.CaptureFixture[str], kind: str
) -> None:
    account = _account(kind, local_only=True)
    code, _, err, requests, _ = _run(
        capsys,
        [kind, "--message", "one", "--local-only", "--timeout-seconds", "9"],
        httpx.Response(200, json=account),
    )
    assert code == 0 and err == "" and len(requests) == 1
    assert json.loads(requests[0].content) == {
        "kind": kind,
        "local_only": True,
        "request": {
            "capability": kind,
            "messages": [{"role": "user", "content": "one"}],
        },
    }


def test_explicit_timeout_is_scalar(capsys: pytest.CaptureFixture[str]) -> None:
    result = _run(
        capsys,
        ["chat", "x", "--timeout-seconds", "9"],
        httpx.Response(200, json=_account()),
    )
    assert result[0] == 0
    assert result[4] == [
        {"timeout": 9.0, "follow_redirects": False, "trust_env": False}
    ]


@pytest.mark.parametrize("kind", ["summarize", "classify"])
@pytest.mark.parametrize("source", ["text", "file", "stdin"])
def test_text_sources(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, kind: str, source: str
) -> None:
    path = tmp_path / "source.txt"
    path.write_text("source", encoding="utf-8")
    argv = [kind]
    if source == "text":
        argv += ["--text", "source"]
    elif source == "file":
        argv += ["--file", str(path)]
    if kind == "classify":
        argv += ["--label", "A", "--label", "B"]
    result = _run(
        capsys, argv, httpx.Response(200, json=_account(kind)), stdin=b"source"
    )
    assert result[0] == 0
    assert json.loads(result[3][0].content)["request"]["text"] == "source"


def test_explicit_source_ignores_stdin_and_exact_byte_bound(
    capsys: pytest.CaptureFixture[str],
) -> None:
    account = _account("summarize")
    good = _run(
        capsys,
        ["summarize", "--text", "x"],
        httpx.Response(200, json=account),
        stdin=b"\xff",
    )
    assert good[0] == 0
    good = _run(
        capsys, ["summarize"], httpx.Response(200, json=account), stdin=b"x" * 65_536
    )
    assert good[0] == 0
    for data in (b"x" * 65_537, b"\xff"):
        code, out, err, requests, _ = _run(capsys, ["summarize"], stdin=data)
        assert (code, out, err, requests) == (2, "", client._INVALID_INPUT + "\n", [])


def test_classify_accepts_32_ordered_labels_and_rejects_33(
    capsys: pytest.CaptureFixture[str],
) -> None:
    labels = [f"label-{index}" for index in range(32)]
    argv = ["classify", "--text", "text"]
    for label in labels:
        argv += ["--label", label]
    account = _account("classify")
    account["result"]["selected_label"] = labels[-1]
    result = _run(capsys, argv, httpx.Response(200, json=account))
    assert result[0] == 0
    assert json.loads(result[3][0].content)["request"]["labels"] == labels
    result = _run(capsys, argv + ["--label", "extra"])
    assert result[:3] == (2, "", client._INVALID_INPUT + "\n")
    assert result[3] == []


@pytest.mark.parametrize(
    "argv",
    [
        ["chat"],
        ["chat", " "],
        ["chat", "one", "--message", "two"],
        ["chat", "--message", "one", "--message", "two"],
        ["code", "x" * 65_537],
        ["classify", "--text", "x", "--label", "A"],
        ["classify", "--text", "x", "--label", "A", "--label", "A"],
        ["classify", "--text", "x", "--label", "", "--label", "B"],
        ["classify", "--text", "x", "--label", "A" * 129, "--label", "B"],
        ["summarize", "--text", "x", "--text", "y"],
        ["chat", "x", "--timeout-seconds", "0"],
        ["chat", "x", "--timeout-seconds", "3601"],
        ["chat", "x", "--timeout-seconds", "1.0"],
        ["chat", "x", "--timeout-seconds", "1", "--timeout-seconds", "2"],
        ["image-generation"],
        ["chat", "x", "--body", "{}"],
    ],
)
def test_invalid_inputs_prevent_http(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    code, out, err, requests, options = _run(capsys, argv)
    assert (code, out, err, requests, options) == (
        2,
        "",
        client._INVALID_INPUT + "\n",
        [],
        [],
    )


@pytest.mark.parametrize(
    "status,message",
    [
        (422, client._REJECTED),
        (503, client._EXPLANATION_UNAVAILABLE),
        (500, client._FAILED),
        (302, client._FAILED),
    ],
)
def test_http_failures_are_safe_and_not_retried(
    capsys: pytest.CaptureFixture[str], status: int, message: str
) -> None:
    code, out, err, requests, _ = _run(
        capsys, ["chat", "private"], httpx.Response(status, text="secret")
    )
    assert (code, out, err) == (1, "", message + "\n")
    assert len(requests) == 1


@pytest.mark.parametrize(
    "error,message",
    [
        (httpx.ConnectError("secret"), client._UNAVAILABLE),
        (httpx.ReadTimeout("secret"), client._TIMED_OUT),
        (RuntimeError("secret"), client._FAILED),
    ],
)
def test_client_failures_are_safe_and_not_retried(
    capsys: pytest.CaptureFixture[str], error: Exception, message: str
) -> None:
    code, out, err, requests, _ = _run(capsys, ["chat", "private"], error)
    assert (code, out, err) == (1, "", message + "\n")
    assert len(requests) == 1


def test_valid_failed_business_account_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    account = _account()
    account.update(status="failed", result=None, failure={"status": "execution-failed"})
    account["explanation"]["final_node_id"] = None
    code, out, err, requests, _ = _run(
        capsys, ["chat", "x"], httpx.Response(200, json=account)
    )
    assert (code, out, err) == (
        0,
        json.dumps(account, separators=(",", ":")) + "\n",
        "",
    )
    assert len(requests) == 1


def _invalid(capsys: pytest.CaptureFixture[str], account: dict) -> None:
    code, out, err, requests, _ = _run(
        capsys, ["chat", "private"], httpx.Response(200, json=account)
    )
    assert (code, out, err) == (1, "", client._INVALID_RESPONSE + "\n")
    assert len(requests) == 1


def test_malformed_json_is_invalid_response(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err, _, _ = _run(capsys, ["chat", "x"], httpx.Response(200, text="{"))
    assert (code, out, err) == (1, "", client._INVALID_RESPONSE + "\n")


@pytest.mark.parametrize(
    "change",
    [
        lambda a: a.pop("failure"),
        lambda a: a.update(extra="x"),
        lambda a: a.update(status="failed"),
        lambda a: a["result"].update(extra="x"),
        lambda a: a["result"].update(adapter=""),
        lambda a: a["result"].update(node_id="wrong"),
        lambda a: a["explanation"].update(requested_capability="code"),
        lambda a: a["explanation"].update(local_only=True),
        lambda a: a["explanation"].update(final_node_id="other"),
        lambda a: a["explanation"].update(extra="x"),
        lambda a: a["explanation"].update(initial_selection=None),
        lambda a: a["explanation"]["candidate_facts"].append(
            {"family": "local", "node_id": "local-1", "fact": "adapter-invoked"}
        ),
        lambda a: a["explanation"]["candidate_facts"][0].update(family="unknown"),
        lambda a: a["explanation"]["candidate_facts"][0].update(fact="unknown"),
        lambda a: a["explanation"]["candidate_facts"][0].update(
            fact="transport-invoked"
        ),
        lambda a: a["explanation"]["candidate_facts"].reverse(),
    ],
)
def test_invalid_account_shapes_and_facts(
    capsys: pytest.CaptureFixture[str], change: Callable[[dict], object]
) -> None:
    account = _account()
    change(account)
    _invalid(capsys, account)


@pytest.mark.parametrize(
    "facts",
    [
        ["adapter-invoked"],
        ["adapter-invoked", "execution-permission-granted"],
        ["execution-permission-denied", "adapter-invoked"],
        ["execution-permission-granted", "execution-permission-denied"],
    ],
)
def test_local_permission_contradictions(
    capsys: pytest.CaptureFixture[str], facts: list[str]
) -> None:
    account = _account()
    account["explanation"]["candidate_facts"] = [
        {"family": "local", "node_id": "local-1", "fact": fact} for fact in facts
    ]
    _invalid(capsys, account)


def test_candidate_resumption(capsys: pytest.CaptureFixture[str]) -> None:
    account = _account()
    facts = account["explanation"]["candidate_facts"]
    facts.insert(
        1,
        {"family": "declared-remote", "node_id": "remote", "fact": "transport-invoked"},
    )
    _invalid(capsys, account)


def test_remote_refusal_requires_prior_transport(
    capsys: pytest.CaptureFixture[str],
) -> None:
    account = _account()
    account["explanation"].update(
        initial_selection={"kind": "declared_remote", "node_id": "remote"},
        candidate_facts=[
            {
                "family": "declared-remote",
                "node_id": "remote",
                "fact": "execution-permission-refused",
            }
        ],
    )
    _invalid(capsys, account)


def test_remote_transport_then_refusal_is_valid(
    capsys: pytest.CaptureFixture[str],
) -> None:
    account = _account()
    account["explanation"].update(
        initial_selection={"kind": "declared_remote", "node_id": "remote"},
        candidate_facts=[
            {
                "family": "declared-remote",
                "node_id": "remote",
                "fact": "transport-invoked",
            },
            {
                "family": "declared-remote",
                "node_id": "remote",
                "fact": "execution-permission-refused",
            },
        ],
        final_node_id="remote",
    )
    account["result"]["node_id"] = "remote"
    assert _run(capsys, ["chat", "x"], httpx.Response(200, json=account))[0] == 0


def test_local_runtime_continuation_and_same_node_id_across_families(
    capsys: pytest.CaptureFixture[str],
) -> None:
    account = _account()
    explanation = account["explanation"]
    explanation["candidate_facts"].append(
        {"family": "declared-remote", "node_id": "local-1", "fact": "transport-invoked"}
    )
    explanation["continuations"] = [
        {
            "node_id": "local-1",
            "reason": "local-runtime-connection-unavailable-before-request",
        }
    ]
    assert _run(capsys, ["chat", "x"], httpx.Response(200, json=account))[0] == 0
    for facts in (
        explanation["candidate_facts"][1:],
        explanation["candidate_facts"][:1] + explanation["candidate_facts"][2:],
        explanation["candidate_facts"][:2],
    ):
        invalid = deepcopy(account)
        invalid["explanation"]["candidate_facts"] = facts
        _invalid(capsys, invalid)


@pytest.mark.parametrize(
    ("family", "facts", "reason"),
    [
        (
            "local",
            ["execution-permission-denied"],
            "local-execution-permission-denied",
        ),
        (
            "declared-remote",
            ["transport-invoked", "execution-permission-refused"],
            "remote-execution-permission-refused",
        ),
    ],
)
def test_permission_continuation_has_establishing_fact_and_later_candidate(
    capsys: pytest.CaptureFixture[str], family: str, facts: list[str], reason: str
) -> None:
    account = _account()
    explanation = account["explanation"]
    node_id = "first"
    explanation["initial_selection"] = (
        {"kind": "local"}
        if family == "local"
        else {"kind": "declared_remote", "node_id": node_id}
    )
    explanation["candidate_facts"] = [
        {"family": family, "node_id": node_id, "fact": fact} for fact in facts
    ] + explanation["candidate_facts"]
    explanation["continuations"] = [{"node_id": node_id, "reason": reason}]
    assert _run(capsys, ["chat", "x"], httpx.Response(200, json=account))[0] == 0
    invalid = deepcopy(account)
    invalid["explanation"]["candidate_facts"] = invalid["explanation"][
        "candidate_facts"
    ][:-2]
    invalid["explanation"]["final_node_id"] = None
    invalid["result"] = None
    invalid["status"] = "failed"
    invalid["failure"] = {"status": "runtime-unavailable"}
    _invalid(capsys, invalid)
    invalid = deepcopy(account)
    invalid["explanation"]["candidate_facts"].pop(0)
    _invalid(capsys, invalid)


def test_continuation_validation(capsys: pytest.CaptureFixture[str]) -> None:
    account = _account()
    explanation = account["explanation"]
    explanation["candidate_facts"].extend(
        [
            {
                "family": "declared-remote",
                "node_id": "remote",
                "fact": "transport-invoked",
            },
            {
                "family": "local",
                "node_id": "local-2",
                "fact": "execution-permission-granted",
            },
        ]
    )
    explanation["continuations"] = [
        {
            "node_id": "local-1",
            "reason": "local-runtime-connection-unavailable-before-request",
        },
        {
            "node_id": "remote",
            "reason": "remote-runtime-connection-unavailable-before-request",
        },
    ]
    assert _run(capsys, ["chat", "x"], httpx.Response(200, json=account))[0] == 0
    changes = [
        lambda e: e["continuations"][0].update(reason="unknown"),
        lambda e: e["continuations"].append(e["continuations"][0]),
        lambda e: e["continuations"].reverse(),
        lambda e: e["continuations"].append(
            {"node_id": "local-2", "reason": "local-execution-permission-denied"}
        ),
        lambda e: e["candidate_facts"].pop(2),
    ]
    for change in changes:
        invalid = deepcopy(account)
        change(invalid["explanation"])
        _invalid(capsys, invalid)


def test_classification_result_must_match_supplied_label(
    capsys: pytest.CaptureFixture[str],
) -> None:
    account = _account("classify")
    account["result"]["selected_label"] = "C"
    code, out, err, _, _ = _run(
        capsys,
        ["classify", "--text", "private", "--label", "A", "--label", "B"],
        httpx.Response(200, json=account),
    )
    assert (code, out, err) == (1, "", client._INVALID_RESPONSE + "\n")
