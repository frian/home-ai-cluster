import json

import httpx
import pytest

from home_ai_cluster import external_information_command


class EntryPoints:
    def __init__(self, entries: list[object]) -> None:
        self.entries = entries
        self.groups: list[str] = []

    def select(self, *, group: str) -> list[object]:
        self.groups.append(group)
        return self.entries


class EntryPoint:
    def __init__(self, name: str, loaded: object) -> None:
        self.name = name
        self.loaded = loaded
        self.loads = 0

    def load(self) -> object:
        self.loads += 1
        if isinstance(self.loaded, Exception):
            raise self.loaded
        return self.loaded


class ListSubclass(list[object]):
    pass


class DictSubclass(dict[str, str]):
    pass


class AsyncCallable:
    def __init__(self) -> None:
        self.received: list[str] = []

    async def __call__(self, query: str) -> list[dict[str, str]]:
        self.received.append(query)
        return [valid_candidate()]


class SyncCallable:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, query: str) -> list[dict[str, str]]:
        self.calls += 1
        raise AssertionError("sync callable must not run")


def valid_candidate() -> dict[str, str]:
    return {
        "title": "Source title",
        "url": "https://example.test/source",
        "content": "Source content",
    }


def result_body() -> dict[str, object]:
    return {
        "content": "generated response",
        "sources": [valid_candidate()],
        "node_id": "cluster-node",
        "adapter": "test-adapter",
        "model": "test-model",
    }


def configure_entries(
    monkeypatch: pytest.MonkeyPatch, entries: list[object]
) -> EntryPoints:
    metadata = EntryPoints(entries)
    monkeypatch.setattr(
        external_information_command.importlib.metadata,
        "entry_points",
        lambda: metadata,
    )
    return metadata


def client_factory(handler: httpx.MockTransport):
    def create_client(**kwargs: object) -> httpx.Client:
        return httpx.Client(transport=handler, **kwargs)

    return create_client


def run_command(
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    handler: httpx.MockTransport | None = None,
) -> tuple[int, str, str]:
    try:
        external_information_command.main(
            argv,
            _client_factory=(
                client_factory(handler)
                if handler is not None
                else lambda **_: (_ for _ in ()).throw(AssertionError("no HTTP"))
            ),
        )
    except SystemExit as error:
        exit_code = error.code
    else:
        exit_code = 0
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def arguments(*, query: str = "operator query") -> list[str]:
    return [
        "--plugin",
        "selected",
        "--query",
        query,
        "--question",
        "operator question",
    ]


def short_arguments(
    *, query: str = "operator query", question: str = "operator question"
) -> list[str]:
    return ["--plugin", "selected", query, question]


def test_help_uses_public_positional_names_without_discovery(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    discovered = False

    def entry_points() -> object:
        nonlocal discovered
        discovered = True
        raise AssertionError("help must not discover plugins")

    monkeypatch.setattr(
        external_information_command.importlib.metadata, "entry_points", entry_points
    )

    with pytest.raises(SystemExit) as raised:
        external_information_command.main(["--help"])

    captured = capsys.readouterr()
    assert raised.value.code == 0
    assert "QUERY" in captured.out
    assert "QUESTION" in captured.out
    assert "query_positional" not in captured.out
    assert "question_positional" not in captured.out
    assert captured.err == ""
    assert not discovered


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--plugin", "selected", "--query", "query"],
        [
            "--plugin",
            "selected",
            "--plugin",
            "other",
            "--query",
            "query",
            "--question",
            "question",
        ],
        ["--plugin", "selected", "query"],
        ["--plugin", "selected", "query", "question", "extra"],
        ["--plugin", "selected", "query", "--question", "question"],
        ["--plugin", "selected", "--query", "query", "question"],
        [
            "--plugin",
            "selected",
            "--query",
            "query",
            "--query",
            "other",
            "--question",
            "question",
        ],
        [
            "--plugin",
            "selected",
            "--query",
            "query",
            "--question",
            "question",
            "--question",
            "other",
        ],
        ["--plugin", "selected", "", "question"],
        ["--plugin", "selected", "x" * 4_097, "question"],
        ["--plugin", "", "--query", "query", "--question", "question"],
        ["--plugin", "x" * 65, "--query", "query", "--question", "question"],
        ["--plugin", "selected", "--query", "", "--question", "question"],
        [
            "--plugin",
            "selected",
            "--query",
            "x" * 4_097,
            "--question",
            "question",
        ],
        [
            "--plugin",
            "selected",
            "--query",
            "query",
            "--question",
            "question",
            "--verbose",
            "--json",
        ],
        [
            "--plugin",
            "selected",
            "--query",
            "query",
            "--question",
            "question",
            "--timeout-seconds",
            "0",
        ],
    ],
)
def test_invalid_input_fails_before_discovery(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    discovered = False

    def entry_points() -> object:
        nonlocal discovered
        discovered = True
        raise AssertionError("input failure must not discover plugins")

    monkeypatch.setattr(
        external_information_command.importlib.metadata, "entry_points", entry_points
    )
    exit_code, stdout, stderr = run_command(capsys, argv)

    assert exit_code == 2
    assert stdout == ""
    assert stderr == "error: invalid request input\n"
    assert not discovered


@pytest.mark.parametrize("entry_count", [0, 2])
def test_missing_or_duplicate_selection_fails_without_loading_or_http(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entry_count: int,
) -> None:
    async def acquire(query: str) -> list[dict[str, str]]:
        raise AssertionError("must not invoke a duplicate plugin")

    entries = [EntryPoint("selected", acquire) for _ in range(entry_count)]
    metadata = configure_entries(monkeypatch, entries)
    exit_code, stdout, stderr = run_command(capsys, arguments())

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: external-information-acquisition-failed\n"
    assert metadata.groups == [external_information_command._ENTRY_POINT_GROUP]
    assert all(entry.loads == 0 for entry in entries)


def test_unselected_plugin_is_not_loaded_and_selected_plugin_runs_once(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    received: list[str] = []

    async def selected(query: str) -> list[dict[str, str]]:
        received.append(query)
        return [valid_candidate()]

    async def unselected(query: str) -> list[dict[str, str]]:
        raise AssertionError("unselected plugin must not be called")

    ignored = EntryPoint("ignored", unselected)
    chosen = EntryPoint("selected", selected)
    configure_entries(monkeypatch, [ignored, chosen])
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=result_body())

    exit_code, stdout, stderr = run_command(
        capsys, arguments(query="  exact query  "), httpx.MockTransport(handler)
    )

    assert exit_code == 0
    assert stdout == "generated response\n"
    assert stderr == ""
    assert ignored.loads == 0
    assert chosen.loads == 1
    assert received == ["  exact query  "]
    assert len(requests) == 1


def test_short_form_normalizes_to_the_existing_request_and_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    received: list[str] = []

    async def acquire(query: str) -> list[dict[str, str]]:
        received.append(query)
        return [valid_candidate()]

    configure_entries(monkeypatch, [EntryPoint("selected", acquire)])
    requests: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=result_body())

    handler_transport = httpx.MockTransport(handler)
    full_result = run_command(capsys, arguments(query="same query"), handler_transport)
    short_result = run_command(
        capsys, short_arguments(query="same query"), handler_transport
    )

    assert full_result == short_result == (0, "generated response\n", "")
    assert received == ["same query", "same query"]
    assert requests == [
        {"question": "operator question", "sources": [valid_candidate()]},
        {"question": "operator question", "sources": [valid_candidate()]},
    ]


@pytest.mark.parametrize(
    "arguments_suffix",
    [[], ["--verbose"], ["--json"], ["--timeout-seconds", "300"]],
)
def test_short_form_preserves_output_and_timeout_behavior(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    arguments_suffix: list[str],
) -> None:
    async def acquire(query: str) -> list[dict[str, str]]:
        return [valid_candidate()]

    configure_entries(monkeypatch, [EntryPoint("selected", acquire)])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body())

    transport = httpx.MockTransport(handler)
    full_result = run_command(capsys, [*arguments(), *arguments_suffix], transport)
    short_result = run_command(
        capsys, [*short_arguments(), *arguments_suffix], transport
    )

    assert full_result == short_result


@pytest.mark.parametrize("question", ["", "x" * 65_537])
def test_short_invalid_question_preserves_downstream_acquisition_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], question: str
) -> None:
    received: list[str] = []

    async def acquire(query: str) -> list[dict[str, str]]:
        received.append(query)
        return [valid_candidate()]

    configure_entries(monkeypatch, [EntryPoint("selected", acquire)])

    full = [
        "--plugin",
        "selected",
        "--query",
        "operator query",
        "--question",
        question,
    ]
    full_result = run_command(capsys, full)
    short_result = run_command(capsys, short_arguments(question=question))

    assert (
        full_result
        == short_result
        == (
            1,
            "",
            "error: external-information-acquisition-failed\n",
        )
    )
    assert received == ["operator query", "operator query"]


def test_async_callable_instance_is_selected_and_invoked_once(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    acquisition = AsyncCallable()
    configure_entries(monkeypatch, [EntryPoint("selected", acquisition)])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body())

    exit_code, stdout, stderr = run_command(
        capsys,
        arguments(query="exact instance query"),
        httpx.MockTransport(handler),
    )

    assert exit_code == 0
    assert stdout == "generated response\n"
    assert stderr == ""
    assert acquisition.received == ["exact instance query"]


def test_sync_callable_instance_is_rejected_without_invocation(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    acquisition = SyncCallable()
    configure_entries(monkeypatch, [EntryPoint("selected", acquisition)])

    exit_code, stdout, stderr = run_command(capsys, arguments())

    assert (exit_code, stdout, stderr) == (
        1,
        "",
        "error: external-information-acquisition-failed\n",
    )
    assert acquisition.calls == 0


def test_sync_load_import_exception_and_plugin_exception_fail_safely(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def synchronous(query: str) -> list[dict[str, str]]:
        raise AssertionError("sync plugin must not run")

    configure_entries(monkeypatch, [EntryPoint("selected", synchronous)])
    exit_code, stdout, stderr = run_command(capsys, arguments())
    assert (exit_code, stdout, stderr) == (
        1,
        "",
        "error: external-information-acquisition-failed\n",
    )

    configure_entries(monkeypatch, [EntryPoint("selected", RuntimeError("private"))])
    exit_code, stdout, stderr = run_command(capsys, arguments())
    assert (exit_code, stdout, stderr) == (
        1,
        "",
        "error: external-information-acquisition-failed\n",
    )

    async def broken(query: str) -> list[dict[str, str]]:
        raise RuntimeError("private provider failure")

    configure_entries(monkeypatch, [EntryPoint("selected", broken)])
    exit_code, stdout, stderr = run_command(capsys, arguments(query="private query"))
    assert (exit_code, stdout, stderr) == (
        1,
        "",
        "error: external-information-acquisition-failed\n",
    )
    assert "private" not in stderr


@pytest.mark.parametrize(
    "candidates",
    [
        (),
        (candidate for candidate in [valid_candidate()]),
        ListSubclass([valid_candidate()]),
        [valid_candidate()] * 6,
        [DictSubclass(valid_candidate())],
        [dict(valid_candidate(), extra="provider")],
        [{"title": "Title", "url": "https://example.test/source"}],
        [{"title": "Title", "url": "https://example.test/source", "content": 3}],
        [{"title": "", "url": "https://example.test/source", "content": "Body"}],
        [{"title": "Title", "url": "ftp://example.test/source", "content": "Body"}],
    ],
)
def test_invalid_candidate_representation_or_evidence_never_posts(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    candidates: object,
) -> None:
    async def acquire(query: str) -> object:
        return candidates

    configure_entries(monkeypatch, [EntryPoint("selected", acquire)])
    exit_code, stdout, stderr = run_command(capsys, arguments())

    assert (exit_code, stdout, stderr) == (
        1,
        "",
        "error: external-information-acquisition-failed\n",
    )


def test_complete_validation_precedes_exact_public_post_and_http_timeout(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    async def acquire(query: str) -> list[dict[str, str]]:
        return [valid_candidate()]

    configure_entries(monkeypatch, [EntryPoint("selected", acquire)])
    requests: list[httpx.Request] = []
    client_options: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=result_body())

    def create_client(**kwargs: object) -> httpx.Client:
        client_options.append(kwargs)
        return httpx.Client(transport=httpx.MockTransport(handler), **kwargs)

    # Use the injected factory directly so the assertion includes its exact options.
    try:
        external_information_command.main(
            [*arguments(), "--timeout-seconds", "300"],
            _client_factory=create_client,
        )
    except SystemExit as error:
        exit_code = error.code
    else:
        exit_code = 0
    captured = capsys.readouterr()
    stdout, stderr = captured.out, captured.err

    assert exit_code == 0
    assert stdout == "generated response\n"
    assert stderr == ""
    assert client_options == [
        {"timeout": 300.0, "follow_redirects": False, "trust_env": False}
    ]
    assert len(requests) == 1
    assert str(requests[0].url) == "http://127.0.0.1:25042/v1/chat/sources"
    assert json.loads(requests[0].content) == {
        "question": "operator question",
        "sources": [valid_candidate()],
    }


@pytest.mark.parametrize(
    ("arguments_suffix", "expected"),
    [
        (
            ["--verbose"],
            "Response:\ngenerated response\n\nExecution:\n  Node: cluster-node\n"
            "  Adapter: test-adapter\n  Model: test-model\n",
        ),
        (
            ["--json"],
            '{"content":"generated response","sources":[{"title":"Source title",'
            '"url":"https://example.test/source","content":"Source content"}],'
            '"adapter":"test-adapter","model":"test-model","node_id":"cluster-node"}\n',
        ),
    ],
)
def test_verbose_and_json_presentation_include_only_result_data(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    arguments_suffix: list[str],
    expected: str,
) -> None:
    async def acquire(query: str) -> list[dict[str, str]]:
        return [valid_candidate()]

    configure_entries(monkeypatch, [EntryPoint("selected", acquire)])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=result_body())

    exit_code, stdout, stderr = run_command(
        capsys, [*arguments(), *arguments_suffix], httpx.MockTransport(handler)
    )
    assert exit_code == 0
    assert stdout == expected
    assert stderr == ""


@pytest.mark.parametrize(
    ("response_or_error", "expected"),
    [
        (httpx.Response(404), "error: no available chat capability\n"),
        (httpx.Response(503), "error: runtime adapter unavailable\n"),
        (httpx.ConnectError("private server"), "error: ordinary cluster unavailable\n"),
    ],
)
def test_post_acquisition_http_failures_keep_native_failure_ownership(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    response_or_error: httpx.Response | Exception,
    expected: str,
) -> None:
    async def acquire(query: str) -> list[dict[str, str]]:
        return [valid_candidate()]

    configure_entries(monkeypatch, [EntryPoint("selected", acquire)])

    def handler(request: httpx.Request) -> httpx.Response:
        if isinstance(response_or_error, Exception):
            raise response_or_error
        return response_or_error

    exit_code, stdout, stderr = run_command(
        capsys, arguments(), httpx.MockTransport(handler)
    )
    assert exit_code == 1
    assert stdout == ""
    assert stderr == expected
