import os
import stat

import pytest

from home_ai_cluster.core.workspace_authority import (
    WorkspaceAuthority,
    WorkspaceAuthorityError,
)


def authority(tmp_path, operations=None):
    return WorkspaceAuthority(
        tmp_path, {"list", "read", "write"} if operations is None else operations
    )


def test_construction_requires_existing_directory_and_known_nonempty_grant(tmp_path):
    with pytest.raises(WorkspaceAuthorityError):
        WorkspaceAuthority(tmp_path / "missing", {"read"})
    (tmp_path / "file").write_text("not a directory", encoding="utf-8")
    with pytest.raises(WorkspaceAuthorityError):
        WorkspaceAuthority(tmp_path / "file", {"read"})
    with pytest.raises(WorkspaceAuthorityError):
        WorkspaceAuthority(tmp_path, set())
    with pytest.raises(WorkspaceAuthorityError):
        WorkspaceAuthority(tmp_path, {"read", "unknown"})


def test_ungranted_operation_fails_before_filesystem_action(tmp_path):
    workspace = authority(tmp_path, {"list"})
    with pytest.raises(WorkspaceAuthorityError):
        workspace.read("does-not-exist")
    with pytest.raises(WorkspaceAuthorityError):
        workspace.write("does-not-exist", "content")


def test_list_root_and_relative_paths(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "text.txt").write_text("hello", encoding="utf-8")
    workspace = authority(tmp_path)
    assert [entry.name for entry in workspace.list(".")] == ["nested"]
    assert workspace.read("nested/text.txt") == "hello"
    with pytest.raises(WorkspaceAuthorityError):
        workspace.read(".")


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/file",
        "file/",
        "a//b",
        "./file",
        "../file",
        "a/../b",
        "a\\b",
        "C:foo",
        "C:/foo",
        "\\foo",
        "\\\\server\\share",
        "\\\\?\\C:\\foo",
        "\\\\.\\device",
        "file:stream",
        "a\0b",
    ],
)
def test_closed_logical_path_grammar_fails_before_access(tmp_path, path):
    with pytest.raises(WorkspaceAuthorityError):
        authority(tmp_path).read(path)


def test_logical_path_utf8_bound_is_checked_before_host_access(tmp_path):
    permitted = "a" * 4_096
    with pytest.raises(WorkspaceAuthorityError, match="invalid workspace file"):
        authority(tmp_path).read(permitted)
    with pytest.raises(WorkspaceAuthorityError, match="path exceeds"):
        authority(tmp_path).read("a" * 4_097)
    with pytest.raises(WorkspaceAuthorityError, match="path exceeds"):
        authority(tmp_path).read("é" * 2_049)


def test_list_is_immediate_sorted_and_classifies_entries(tmp_path):
    (tmp_path / "z.txt").write_text("z", encoding="utf-8")
    (tmp_path / "adir").mkdir()
    (tmp_path / ".hidden").write_text("h", encoding="utf-8")
    link = tmp_path / "redirect"
    try:
        link.symlink_to(tmp_path / "z.txt")
    except OSError as error:
        pytest.skip(f"symlink fixture unavailable: {error}")
    entries = authority(tmp_path).list(".")
    assert [(entry.name, entry.kind) for entry in entries] == [
        (".hidden", "file"),
        ("adir", "directory"),
        ("redirect", "redirection"),
        ("z.txt", "file"),
    ]


def test_redirection_is_rejected_for_intermediate_and_final_targets(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "file").write_text("outside", encoding="utf-8")
    link = tmp_path / "redirect"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlink fixture unavailable: {error}")
    workspace = authority(tmp_path)
    for path in ("redirect", "redirect/file"):
        with pytest.raises(WorkspaceAuthorityError):
            workspace.read(path)
        with pytest.raises(WorkspaceAuthorityError):
            workspace.write(path, "replacement")


def test_list_entry_bound_is_complete_or_failure(tmp_path):
    for index in range(1_024):
        (tmp_path / f"entry-{index:04}").write_text("", encoding="utf-8")
    assert len(authority(tmp_path).list(".")) == 1_024
    (tmp_path / "one-more").write_text("", encoding="utf-8")
    with pytest.raises(WorkspaceAuthorityError, match="too many"):
        authority(tmp_path).list(".")


def test_posix_unrepresentable_listing_name_fails_closed(tmp_path):
    if os.name == "nt":
        pytest.skip("Windows filenames are textual")
    os.close(os.open(os.fsencode(tmp_path) + b"/bad-\xff", os.O_CREAT | os.O_WRONLY))
    with pytest.raises(WorkspaceAuthorityError):
        authority(tmp_path).list(".")


def test_regular_utf8_and_empty_reads(tmp_path):
    (tmp_path / "text").write_text("Grüße", encoding="utf-8")
    (tmp_path / "empty").write_bytes(b"")
    workspace = authority(tmp_path)
    assert workspace.read("text") == "Grüße"
    assert workspace.read("empty") == ""


def test_invalid_utf8_and_nonregular_read_targets_fail(tmp_path):
    (tmp_path / "binary").write_bytes(b"\xff")
    (tmp_path / "directory").mkdir()
    workspace = authority(tmp_path)
    for path in ("binary", "directory", "missing"):
        with pytest.raises(WorkspaceAuthorityError):
            workspace.read(path)


def test_read_actual_byte_bound_not_metadata_size(tmp_path, monkeypatch):
    target = tmp_path / "large"
    target.write_bytes(b"x" * (1_048_576 + 1))
    original_fstat = os.fstat

    def misleading_fstat(descriptor):
        actual = original_fstat(descriptor)
        return type("Status", (), {"st_mode": actual.st_mode, "st_size": 0})()

    monkeypatch.setattr(
        "home_ai_cluster.core.workspace_authority.os.fstat", misleading_fstat
    )
    with pytest.raises(WorkspaceAuthorityError, match="exceeds"):
        authority(tmp_path).read("large")


def test_read_exactly_one_mebibyte_succeeds(tmp_path):
    (tmp_path / "large").write_bytes(b"x" * 1_048_576)
    assert authority(tmp_path).read("large") == "x" * 1_048_576


def test_write_replaces_existing_regular_file_and_empty_content(tmp_path):
    target = tmp_path / "target"
    target.write_text("before", encoding="utf-8")
    workspace = authority(tmp_path)
    workspace.write("target", "after")
    assert target.read_text(encoding="utf-8") == "after"
    workspace.write("target", "")
    assert target.read_text(encoding="utf-8") == ""


def test_write_exact_bound_and_invalid_targets_do_not_mutate_or_create(tmp_path):
    target = tmp_path / "target"
    target.write_text("before", encoding="utf-8")
    workspace = authority(tmp_path)
    workspace.write("target", "x" * 1_048_576)
    assert target.stat().st_size == 1_048_576
    with pytest.raises(WorkspaceAuthorityError):
        workspace.write("target", "x" * 1_048_577)
    assert target.stat().st_size == 1_048_576
    with pytest.raises(WorkspaceAuthorityError):
        workspace.write("missing", "content")
    assert not (tmp_path / "missing").exists()


def test_write_rejects_special_file_where_supported(tmp_path):
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO fixture unavailable")
    fifo = tmp_path / "fifo"
    try:
        os.mkfifo(fifo)
    except OSError as error:
        pytest.skip(f"FIFO fixture unavailable: {error}")
    with pytest.raises(WorkspaceAuthorityError):
        authority(tmp_path).write("fifo", "content")


def test_prepublication_failure_preserves_content(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.write_text("before", encoding="utf-8")
    monkeypatch.setattr(
        "home_ai_cluster.core.workspace_authority.os.fsync",
        lambda _descriptor: (_ for _ in ()).throw(OSError("failed")),
    )
    with pytest.raises(WorkspaceAuthorityError):
        authority(tmp_path).write("target", "after")
    assert target.read_text(encoding="utf-8") == "before"


def test_write_uses_one_sibling_replacement_after_preparation(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.write_text("before", encoding="utf-8")
    calls = []
    original_replace = os.replace

    def replace(source, destination):
        calls.append((source, destination))
        original_replace(source, destination)

    monkeypatch.setattr("home_ai_cluster.core.workspace_authority.os.replace", replace)
    authority(tmp_path).write("target", "after")
    assert len(calls) == 1
    assert os.path.dirname(calls[0][0]) == str(tmp_path)
    assert target.read_text(encoding="utf-8") == "after"


def test_hard_link_replacement_has_namespace_semantics(tmp_path):
    selected = tmp_path / "selected"
    other = tmp_path / "other"
    selected.write_text("before", encoding="utf-8")
    try:
        os.link(selected, other)
    except OSError as error:
        pytest.skip(f"hard-link fixture unavailable: {error}")
    authority(tmp_path).write("selected", "after")
    assert selected.read_text(encoding="utf-8") == "after"
    assert other.read_text(encoding="utf-8") == "before"


def test_reparse_points_are_classified_as_redirections(tmp_path, monkeypatch):
    monkeypatch.setattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400, raising=False)
    status = type(
        "Status",
        (),
        {
            "st_mode": stat.S_IFREG,
            "st_file_attributes": 0x400,
        },
    )()
    assert WorkspaceAuthority._kind(status) == "redirection"
