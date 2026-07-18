import json

import httpx
import pytest

from home_ai_cluster.chat_command import _REQUEST_TIMEOUT_SECONDS, main


def client_factory(handler: httpx.MockTransport):
    def create_client(**kwargs: object) -> httpx.Client:
        assert kwargs == {
            "timeout": _REQUEST_TIMEOUT_SECONDS,
            "follow_redirects": False,
        }
        return httpx.Client(transport=handler, **kwargs)

    return create_client


def run_command(
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    handler: httpx.MockTransport,
) -> tuple[int, str, str]:
    try:
        main(argv, _client_factory=client_factory(handler))
    except SystemExit as error:
        exit_code = error.code
    else:
        exit_code = 0
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def unused_client(**kwargs: object) -> httpx.Client:
    raise AssertionError("invalid input and --help must not send a request")


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--message", ""],
        ["--message", "   "],
        ["--unknown"],
        ["--message", "first", "--message", "second"],
    ],
)
def test_invalid_input_has_one_safe_error(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(argv, _client_factory=unused_client)

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert captured.out == ""
    assert captured.err == "error: invalid request input\n"


def test_help_does_not_send_a_request(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--help"], _client_factory=unused_client)

    captured = capsys.readouterr()
    assert raised.value.code == 0
    assert captured.out.startswith("usage: home-ai-cluster-chat")
    assert captured.err == ""


@pytest.mark.parametrize("model", ["cluster-model", None])
def test_success_posts_one_exact_native_request_and_emits_result(
    capsys: pytest.CaptureFixture[str], model: str | None
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "content": "response content",
                "adapter": "test-adapter",
                "model": model,
                "node_id": "cluster-node",
            },
        )

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "  preserved message  "],
        httpx.MockTransport(handler),
    )

    assert exit_code == 0
    assert stderr == ""
    assert json.loads(stdout) == {
        "content": "response content",
        "adapter": "test-adapter",
        "model": model,
        "node_id": "cluster-node",
    }
    assert stdout.count("\n") == 1
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert str(request.url) == "http://127.0.0.1:8000/v1/chat"
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {
        "messages": [{"role": "user", "content": "  preserved message  "}],
        "capability": "chat",
    }


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (422, "error: cluster rejected request"),
        (404, "error: no available chat capability"),
        (503, "error: runtime adapter unavailable"),
        (500, "error: ordinary request failed"),
    ],
)
def test_http_failures_are_safely_mapped(
    capsys: pytest.CaptureFixture[str], status_code: int, expected_error: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            text="private response body and generated response",
        )

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "private submitted prompt"],
        httpx.MockTransport(handler),
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == f"{expected_error}\n"
    assert "private" not in stderr
    assert "response body" not in stderr


@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectError("http://private-host token=secret"),
        httpx.TimeoutException("private timeout detail"),
    ],
)
def test_connection_and_timeout_failures_are_safely_mapped(
    capsys: pytest.CaptureFixture[str], error: Exception
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "private submitted prompt"],
        httpx.MockTransport(handler),
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: ordinary cluster unavailable\n"
    assert "private" not in stderr
    assert "secret" not in stderr


def test_other_httpx_request_failures_are_safely_mapped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ProtocolError("private protocol detail")

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "private submitted prompt"],
        httpx.MockTransport(handler),
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: ordinary request failed\n"
    assert "private" not in stderr
    assert "protocol" not in stderr


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"not-json"),
        httpx.Response(200, json={"content": "private generated response"}),
    ],
)
def test_invalid_success_responses_are_rejected(
    capsys: pytest.CaptureFixture[str], response: httpx.Response
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return response

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "private submitted prompt"],
        httpx.MockTransport(handler),
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: invalid cluster response\n"
    assert "private" not in stderr


def test_unexpected_client_failure_is_safely_mapped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise RuntimeError("private exception token=secret")

    exit_code, stdout, stderr = run_command(
        capsys,
        ["--message", "private submitted prompt"],
        httpx.MockTransport(handler),
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: ordinary request failed\n"
    assert "private" not in stderr
    assert "secret" not in stderr
