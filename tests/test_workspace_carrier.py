"""Focused proof of the RFC-0115 one-shot workspace carrier."""

import json
import tomllib
from io import BytesIO, StringIO
from pathlib import Path

import pytest

from home_ai_cluster import workspace_carrier
from home_ai_cluster.core.workspace_authority import WorkspaceEntry


class UnreadableInput(BytesIO):
    def read(self, size=-1):
        raise AssertionError("request input must not be read")


class BrokenOutput(BytesIO):
    def __init__(self):
        super().__init__()
        self.write_attempts = 0

    def write(self, data):
        self.write_attempts += 1
        raise BrokenPipeError


def run(argv, request=b"", *, stdout=None):
    output = BytesIO() if stdout is None else stdout
    diagnostics = StringIO()
    status = workspace_carrier.main(
        argv,
        _stdin=BytesIO(request),
        _stdout=output,
        _stderr=diagnostics,
    )
    return status, output.getvalue(), diagnostics.getvalue()


def decoded(output):
    return json.loads(output.decode("utf-8"))


def arguments(root, *grants):
    return ["--root", str(root), *sum((["--grant", grant] for grant in grants), [])]


def test_exact_console_script_entry_exists():
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["scripts"]["home-ai-cluster-workspace-carrier"] == (
        "home_ai_cluster.workspace_carrier:main"
    )


def test_explicit_root_and_repeated_grants_construct_one_deduplicated_authority(
    tmp_path, monkeypatch
):
    seen = []

    class Authority:
        def __init__(self, root, grants):
            seen.append((root, grants))

        def list(self, path):
            return ()

    monkeypatch.setattr(workspace_carrier, "WorkspaceAuthority", Authority)
    status, output, error = run(
        arguments(tmp_path, "list", "list"),
        b'{"operation":"list","path":"."}',
    )
    assert (status, decoded(output), error) == (0, {"ok": True, "entries": []}, "")
    assert seen == [(str(tmp_path), frozenset({"list"}))]


def test_explicit_dot_root_is_accepted(monkeypatch):
    seen = []

    class Authority:
        def __init__(self, root, grants):
            seen.append((root, grants))

        def list(self, path):
            return ()

    monkeypatch.setattr(workspace_carrier, "WorkspaceAuthority", Authority)
    status, output, error = run(
        ["--root", ".", "--grant", "list"],
        b'{"operation":"list","path":"."}',
    )
    assert (status, decoded(output), error) == (0, {"ok": True, "entries": []}, "")
    assert seen == [(".", frozenset({"list"}))]


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--root", "", "--grant", "read"],
        ["--root", "missing", "--grant", "read"],
        ["--root", ".", "--root", ".", "--grant", "read"],
        ["--root", "."],
        ["--root", ".", "--grant", "unknown"],
        ["--root", ".", "--grant", "read", "--unknown"],
        ["--root", ".", "--grant", "read", "positional"],
        ["--roo", ".", "--grant", "read"],
        ["--help"],
    ],
)
def test_invalid_startup_fails_before_request_read(argv):
    output = BytesIO()
    diagnostics = StringIO()
    status = workspace_carrier.main(
        argv,
        _stdin=UnreadableInput(),
        _stdout=output,
        _stderr=diagnostics,
    )
    assert status != 0
    assert output.getvalue() == b""
    assert diagnostics.getvalue() == "error: invalid carrier startup\n"
    assert "missing" not in diagnostics.getvalue()


@pytest.mark.parametrize(
    "request_bytes",
    [
        b"",
        b" \r\n\t",
        b"{",
        b"\xff",
        b"[]",
        b'{"operation":"list","path":"."} {}',
        b'{"operation":"list","path":"."} garbage',
        b'{"operation":NaN,"path":"."}',
        b'{"operation":Infinity,"path":"."}',
        b'{"operation":-Infinity,"path":"."}',
    ],
)
def test_invalid_framing_returns_one_closed_failure(tmp_path, request_bytes):
    status, output, error = run(arguments(tmp_path, "list"), request_bytes)
    assert status != 0
    assert decoded(output) == {"ok": False, "error": "invalid request"}
    assert output.count(b"\n") == 1
    assert error == ""


def test_input_byte_bound_accepts_exact_limit_and_rejects_next_byte(tmp_path):
    request = b'{"operation":"list","path":"."}'
    exact = request + b" " * (workspace_carrier._MAX_INPUT_BYTES - len(request))
    status, output, error = run(arguments(tmp_path, "list"), exact)
    assert (status, decoded(output), error) == (0, {"ok": True, "entries": []}, "")

    status, output, error = run(arguments(tmp_path, "list"), exact + b" ")
    assert status != 0
    assert decoded(output) == {"ok": False, "error": "invalid request"}
    assert error == ""


@pytest.mark.parametrize(
    "request_bytes",
    [
        b'{"operation":"read","operation":"write","path":"target","content":"x"}',
        b'{"operation":"read","path":"a","path":"b"}',
        b'{"operation":"write","path":"target","content":"a","content":"b"}',
        b'{"operation":"read","oper\\u0061tion":"write","path":"target","content":"x"}',
        b'{"operation":"list","path":".","unknown":1,"unknown":2}',
    ],
)
def test_duplicate_decoded_members_fail_before_workspace_action(
    tmp_path, monkeypatch, request_bytes
):
    target = tmp_path / "target"
    target.write_text("before", encoding="utf-8")

    def forbidden(*args, **kwargs):
        raise AssertionError("workspace operation must not run")

    monkeypatch.setattr(workspace_carrier.WorkspaceAuthority, "list", forbidden)
    monkeypatch.setattr(workspace_carrier.WorkspaceAuthority, "read", forbidden)
    monkeypatch.setattr(workspace_carrier.WorkspaceAuthority, "write", forbidden)

    status, output, error = run(
        arguments(tmp_path, "read", "write", "list"), request_bytes
    )
    assert status != 0
    assert decoded(output) == {"ok": False, "error": "invalid request"}
    assert target.read_text(encoding="utf-8") == "before"
    assert error == ""


@pytest.mark.parametrize(
    "request_document",
    [
        {},
        {"operation": "unknown", "path": "."},
        {"operation": None, "path": "."},
        {"operation": True, "path": "."},
        {"operation": [], "path": "."},
        {"operation": {}, "path": "."},
        {"operation": "list"},
        {"operation": "list", "path": None},
        {"operation": "list", "path": 1},
        {"operation": "list", "path": False},
        {"operation": "list", "path": []},
        {"operation": "list", "path": {}},
        {"operation": "list", "path": ".", "content": ""},
        {"operation": "read", "path": "x", "content": ""},
        {"operation": "write", "path": "x"},
        {"operation": "write", "path": "x", "content": None},
        {"operation": "write", "path": "x", "content": 1},
        {"operation": "write", "path": "x", "content": False},
        {"operation": "write", "path": "x", "content": []},
        {"operation": "write", "path": "x", "content": {}},
        {"operation": "list", "path": ".", "root": "/outside"},
        {"operation": "list", "path": ".", "grant": "write"},
        {"operation": "list", "path": ".", "extra": True},
    ],
)
def test_closed_operation_specific_schemas_fail(tmp_path, request_document):
    status, output, error = run(
        arguments(tmp_path, "list", "read", "write"),
        json.dumps(request_document).encode(),
    )
    assert status != 0
    assert decoded(output) == {"ok": False, "error": "invalid request"}
    assert error == ""


def test_successful_list_has_exact_compact_shape(tmp_path):
    (tmp_path / "directory").mkdir()
    (tmp_path / "text").write_text("hello", encoding="utf-8")
    status, output, error = run(
        arguments(tmp_path, "list"),
        b'{"operation":"list","path":"."}',
    )
    assert status == 0
    assert output == (
        b'{"ok":true,"entries":[{"name":"directory","kind":"directory"},'
        b'{"name":"text","kind":"file"}]}\n'
    )
    assert error == ""


def test_successful_read_has_exact_utf8_shape(tmp_path):
    (tmp_path / "text").write_text("Grüße", encoding="utf-8")
    status, output, error = run(
        arguments(tmp_path, "read"),
        b'{"operation":"read","path":"text"}',
    )
    assert status == 0
    assert output == '{"ok":true,"content":"Grüße"}\n'.encode()
    assert error == ""


@pytest.mark.parametrize("content", ["after", ""])
def test_successful_write_replaces_existing_target_with_exact_shape(tmp_path, content):
    target = tmp_path / "target"
    target.write_text("before", encoding="utf-8")
    request = json.dumps(
        {"operation": "write", "path": "target", "content": content}
    ).encode()
    status, output, error = run(arguments(tmp_path, "write"), request)
    assert (status, output, error) == (0, b'{"ok":true}\n', "")
    assert target.read_text(encoding="utf-8") == content


@pytest.mark.parametrize(
    ("grant", "request_bytes"),
    [
        ("list", b'{"operation":"read","path":"missing"}'),
        (
            "read",
            b'{"operation":"write","path":"target","content":"changed"}',
        ),
        ("read", b'{"operation":"list","path":"missing"}'),
    ],
)
def test_authority_enforces_grants_before_filesystem_action(
    tmp_path, grant, request_bytes
):
    target = tmp_path / "target"
    target.write_text("before", encoding="utf-8")
    status, output, error = run(arguments(tmp_path, grant), request_bytes)
    assert status != 0
    assert decoded(output) == {"ok": False, "error": "workspace request refused"}
    assert target.read_text(encoding="utf-8") == "before"
    assert error == ""


@pytest.mark.parametrize(
    "request_bytes",
    [
        b'{"operation":"read","path":"../outside"}',
        b'{"operation":"read","path":"/outside"}',
        b'{"operation":"write","path":"missing","content":"x"}',
    ],
)
def test_rfc0114_path_and_missing_write_refusals_propagate(tmp_path, request_bytes):
    status, output, error = run(arguments(tmp_path, "read", "write"), request_bytes)
    assert status != 0
    assert decoded(output) == {"ok": False, "error": "workspace request refused"}
    assert not (tmp_path / "missing").exists()
    assert error == ""


def test_rfc0114_redirection_refusal_propagates(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "target"
    target.write_text("outside", encoding="utf-8")
    link = tmp_path / "redirect"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlink fixture unavailable: {error}")

    for path in ("redirect", "redirect/target"):
        for operation in ("read", "write"):
            request_document = {"operation": operation, "path": path}
            if operation == "write":
                request_document["content"] = "changed"
            status, output, error = run(
                arguments(tmp_path, operation),
                json.dumps(request_document).encode(),
            )
            assert status != 0
            assert decoded(output) == {
                "ok": False,
                "error": "workspace request refused",
            }
            assert target.read_text(encoding="utf-8") == "outside"
            assert error == ""


def test_oversized_list_success_becomes_complete_bounded_failure(tmp_path, monkeypatch):
    huge_name = "x" * workspace_carrier._MAX_OUTPUT_BYTES

    class Authority:
        def __init__(self, root, grants):
            pass

        def list(self, path):
            return (WorkspaceEntry(huge_name, "file"),)

    monkeypatch.setattr(workspace_carrier, "WorkspaceAuthority", Authority)
    status, output, error = run(
        arguments(tmp_path, "list"),
        b'{"operation":"list","path":"."}',
    )
    assert status != 0
    assert output == b'{"ok":false,"error":"workspace request refused"}\n'
    assert len(output) <= workspace_carrier._MAX_OUTPUT_BYTES
    assert error == ""


def test_serialized_output_bound_includes_trailing_newline():
    content_length = workspace_carrier._MAX_OUTPUT_BYTES - len(
        b'{"ok":true,"content":""}\n'
    )
    payload = workspace_carrier._serialize_response(
        {"ok": True, "content": "x" * content_length}
    )
    assert len(payload) == workspace_carrier._MAX_OUTPUT_BYTES

    with pytest.raises(workspace_carrier._ResponseError):
        workspace_carrier._serialize_response(
            {"ok": True, "content": "x" * (content_length + 1)}
        )


def test_write_delivery_failure_preserves_committed_write_without_second_response(
    tmp_path,
):
    target = tmp_path / "target"
    target.write_text("before", encoding="utf-8")
    output = BrokenOutput()
    status, _, error = run(
        arguments(tmp_path, "write"),
        b'{"operation":"write","path":"target","content":"after"}',
        stdout=output,
    )
    assert status != 0
    assert target.read_text(encoding="utf-8") == "after"
    assert output.write_attempts == 1
    assert output.getvalue() == b""
    assert error == "error: response delivery failed\n"


def test_failure_diagnostics_do_not_echo_private_values(tmp_path):
    secret_path = "private-path"
    secret_content = "private-content"
    output = BrokenOutput()
    status, _, error = run(
        arguments(tmp_path, "write"),
        json.dumps(
            {
                "operation": "write",
                "path": secret_path,
                "content": secret_content,
            }
        ).encode(),
        stdout=output,
    )
    assert status != 0
    assert secret_path not in error
    assert secret_content not in error
    assert str(tmp_path) not in error


def test_request_with_second_document_never_executes_first_operation(
    tmp_path, monkeypatch
):
    calls = []

    def forbidden(self, path):
        calls.append(path)

    monkeypatch.setattr(workspace_carrier.WorkspaceAuthority, "list", forbidden)
    status, output, error = run(
        arguments(tmp_path, "list"),
        b'{"operation":"list","path":"."} {"operation":"list","path":"."}',
    )
    assert status != 0
    assert decoded(output) == {"ok": False, "error": "invalid request"}
    assert calls == []
    assert error == ""
