import json
from io import BytesIO

import httpx
import pytest

from home_ai_cluster.commands import classify_command


def result(label: str = "invoice") -> dict[str, str]:
    return {"selected_label": label, "node_id": "selected-node"}


def run(capsys, argv, handler, stdin=b"source"):
    try:
        classify_command.main(
            argv,
            _stdin=BytesIO(stdin),
            _client_factory=lambda **kw: httpx.Client(
                transport=httpx.MockTransport(handler), **kw
            ),
        )
    except SystemExit as error:
        code = error.code
    else:
        code = 0
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_posts_exact_body_with_default_timeout_and_preserved_order(capsys):
    requests = []
    options = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=result())

    def factory(**kwargs):
        options.append(kwargs)
        return httpx.Client(transport=httpx.MockTransport(handler), **kwargs)

    classify_command.main(
        ["--text", "  Source  ", "--label", " A ", "--label", "Résumé"],
        _stdin=BytesIO(),
        _client_factory=factory,
    )
    assert capsys.readouterr().out == "invoice\n"
    assert options == [
        {"timeout": 120.0, "follow_redirects": False, "trust_env": False}
    ]
    assert str(requests[0].url) == "http://127.0.0.1:25042/v1/classify"
    assert json.loads(requests[0].content) == {
        "text": "  Source  ",
        "labels": [" A ", "Résumé"],
    }


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--text", "source", "--file", "x"],
        ["--text", "a", "--text", "b"],
        ["--file", "a", "--file", "b"],
        ["--text", " ", "--label", "a", "--label", "b"],
        ["--text", "x", "--label", "a"],
        ["--text", "x", "--label", "", "--label", "b"],
        ["--text", "x", "--label", "a", "--label", "a"],
        ["--text", "x", "--label", "a", "--label", "b", "--timeout-seconds", "01"],
        ["--text", "x", "--label", "a", "--label", "b", "--timeout-seconds", "0"],
        [
            "--text",
            "source",
            "--label",
            "a",
            "--label",
            "b",
            "--timeout-seconds",
            "10",
            "--timeout-seconds",
            "20",
        ],
        ["--text", "x", "--label", "a", "--label", "b", "--timeout-seconds", "1.5"],
    ],
)
def test_invalid_input_is_safe(capsys, argv):
    code, out, err = run(
        capsys, argv, lambda _: (_ for _ in ()).throw(AssertionError())
    )
    assert (code, out, err) == (2, "", "error: invalid request input\n")


@pytest.mark.parametrize(
    "labels",
    [
        ["a", "b"],
        [str(i) for i in range(32)],
        ["A", "a"],
        ["x", " x"],
        ["é", "ü"],
        ["x" * 128, "b"],
    ],
)
def test_accepted_labels_are_sent_exactly(capsys, labels):
    seen = []
    code, out, err = run(
        capsys,
        ["--text", "source", *sum((["--label", x] for x in labels), [])],
        lambda request: (
            seen.append(json.loads(request.content))
            or httpx.Response(200, json=result())
        ),
    )
    assert (code, out, err) == (0, "invoice\n", "")
    assert seen[0]["labels"] == labels


@pytest.mark.parametrize(
    "status,message",
    [
        (422, "error: cluster rejected request\n"),
        (404, "error: no available classify capability\n"),
        (503, "error: runtime adapter unavailable\n"),
        (500, "error: ordinary request failed\n"),
        (418, "error: ordinary request failed\n"),
    ],
)
def test_status_failures_are_safe(capsys, status, message):
    code, out, err = run(
        capsys,
        ["--label", "a", "--label", "b"],
        lambda _: httpx.Response(status, text="private body"),
    )
    assert (code, out, err) == (1, "", message)


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"selected_label": "a"},
        {"node_id": "n"},
        {"content": "x", "adapter": "a", "node_id": "n"},
    ],
)
def test_malformed_success_response_is_safe(capsys, body):
    code, out, err = run(
        capsys,
        ["--label", "a", "--label", "b"],
        lambda _: httpx.Response(200, json=body),
    )
    assert (code, out, err) == (1, "", "error: invalid cluster response\n")


@pytest.mark.parametrize(
    "argv,expected",
    [
        ([], "invoice\n"),
        (
            ["--verbose"],
            "Classification:\n  Label: invoice\n\nExecution:\n  Node: selected-node\n",
        ),
        (["--json"], '{"selected_label":"invoice","node_id":"selected-node"}\n'),
    ],
)
def test_output_modes(capsys, argv, expected):
    code, out, err = run(
        capsys,
        [*argv, "--label", "a", "--label", "b"],
        lambda _: httpx.Response(200, json=result()),
    )
    assert (code, out, err) == (0, expected, "")


def test_file_and_stdin_boundaries(capsys, tmp_path):
    path = tmp_path / "source"
    path.write_bytes(b"x" * 65_536)
    code, _, _ = run(
        capsys,
        ["--file", str(path), "--label", "a", "--label", "b"],
        lambda _: httpx.Response(200, json=result()),
    )
    assert code == 0
    code, out, err = run(
        capsys,
        ["--label", "a", "--label", "b"],
        lambda _: httpx.Response(200),
        stdin=b"x" * 65_537,
    )
    assert (code, out, err) == (2, "", "error: invalid request input\n")


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (
            httpx.ConnectError("private connection"),
            "error: ordinary cluster unavailable\n",
        ),
        (
            httpx.TimeoutException("private timeout"),
            "error: ordinary request timed out\n",
        ),
        (httpx.ReadError("private request"), "error: ordinary request failed\n"),
        (RuntimeError("private unexpected"), "error: ordinary request failed\n"),
    ],
)
def test_client_exceptions_are_safe(capsys, error, message):
    def factory(**_):
        raise error

    try:
        classify_command.main(
            ["--label", "a", "--label", "b"],
            _stdin=BytesIO(b"source"),
            _client_factory=factory,
        )
    except SystemExit as raised:
        code = raised.code
    captured = capsys.readouterr()
    assert (code, captured.out, captured.err) == (1, "", message)
    assert "private" not in captured.err
