"""Bounded, process-local workspace namespace authority (RFC-0114)."""

import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

_MAX_PATH_BYTES = 4_096
_MAX_FILE_BYTES = 1_048_576
_MAX_LIST_ENTRIES = 1_024
_OPERATIONS = frozenset({"list", "read", "write"})


class WorkspaceAuthorityError(ValueError):
    """Raised when a request falls outside this authority's bounded contract."""


@dataclass(frozen=True)
class WorkspaceEntry:
    """One immediate workspace directory entry."""

    name: str
    kind: Literal["file", "directory", "redirection", "other"]


class WorkspaceAuthority:
    """One fixed root with an explicit subset of local workspace operations."""

    def __init__(self, root: str | Path, operations: set[str] | frozenset[str]) -> None:
        try:
            resolved_root = Path(root).resolve(strict=True)
        except (OSError, RuntimeError, TypeError):
            raise WorkspaceAuthorityError(
                "root must be an existing directory"
            ) from None
        if not resolved_root.is_dir():
            raise WorkspaceAuthorityError("root must be an existing directory")
        try:
            granted = frozenset(operations)
        except TypeError:
            raise WorkspaceAuthorityError(
                "operations must be a non-empty known subset"
            ) from None
        if not granted or not granted <= _OPERATIONS:
            raise WorkspaceAuthorityError("operations must be a non-empty known subset")
        self._root = resolved_root
        self._operations = granted

    def list(self, path: str) -> tuple[WorkspaceEntry, ...]:
        """Return a complete, bounded, sorted immediate directory listing."""
        self._require("list")
        target = self._target(path, allow_root=True)
        try:
            target_status = os.lstat(target)
            if self._is_redirection_status(target_status) or not stat.S_ISDIR(
                target_status.st_mode
            ):
                raise OSError
            entries: list[WorkspaceEntry] = []
            with os.scandir(target) as children:
                for child in children:
                    # Strict encoding rejects POSIX surrogate-escaped filenames.
                    child.name.encode("utf-8", errors="strict")
                    if len(entries) >= _MAX_LIST_ENTRIES:
                        raise WorkspaceAuthorityError("directory has too many entries")
                    child_status = os.lstat(child.path)
                    entries.append(WorkspaceEntry(child.name, self._kind(child_status)))
        except WorkspaceAuthorityError:
            raise
        except (OSError, UnicodeError):
            raise WorkspaceAuthorityError("invalid workspace directory") from None
        return tuple(sorted(entries, key=lambda entry: entry.name))

    def read(self, path: str) -> str:
        """Read one complete bounded regular UTF-8 file."""
        self._require("read")
        target = self._target(path, allow_root=False)
        try:
            target_status = os.lstat(target)
            if self._is_redirection_status(target_status) or not stat.S_ISREG(
                target_status.st_mode
            ):
                raise OSError
            with open(target, "rb") as source:
                if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                    raise OSError
                content = source.read(_MAX_FILE_BYTES + 1)
            if len(content) > _MAX_FILE_BYTES:
                raise WorkspaceAuthorityError("file exceeds byte bound")
            return content.decode("utf-8", errors="strict")
        except WorkspaceAuthorityError:
            raise
        except (OSError, UnicodeError):
            raise WorkspaceAuthorityError("invalid workspace file") from None

    def write(self, path: str, content: str) -> None:
        """Completely replace one existing regular UTF-8 file via a sibling."""
        self._require("write")
        target = self._target(path, allow_root=False)
        try:
            target_status = os.lstat(target)
            if self._is_redirection_status(target_status) or not stat.S_ISREG(
                target_status.st_mode
            ):
                raise OSError
            replacement = content.encode("utf-8", errors="strict")
        except (AttributeError, OSError, UnicodeError):
            raise WorkspaceAuthorityError(
                "invalid workspace file replacement"
            ) from None
        if len(replacement) > _MAX_FILE_BYTES:
            raise WorkspaceAuthorityError("replacement exceeds byte bound")

        temporary_name: str | None = None
        descriptor: int | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=".hac-workspace-", dir=target.parent
            )
            with os.fdopen(descriptor, "wb") as temporary:
                descriptor = None
                temporary.write(replacement)
                temporary.flush()
                os.fsync(temporary.fileno())
            # This is the sole publication operation, after all practical
            # fallible preparation has completed.
            os.replace(temporary_name, target)
            temporary_name = None
        except OSError:
            raise WorkspaceAuthorityError("workspace replacement failed") from None
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if temporary_name is not None:
                try:
                    os.unlink(temporary_name)
                except OSError:
                    pass

    def _require(self, operation: str) -> None:
        if operation not in self._operations:
            raise WorkspaceAuthorityError("operation is not granted")

    def _target(self, path: str, *, allow_root: bool) -> Path:
        segments = self._segments(path, allow_root=allow_root)
        target = self._root
        try:
            for segment in segments:
                target = target / segment
                if self._is_redirection_status(os.lstat(target)):
                    raise WorkspaceAuthorityError("redirection is not allowed")
        except WorkspaceAuthorityError:
            raise
        except OSError:
            # Later target validation gives every unavailable/nonexistent target
            # the same small internal error boundary.
            pass
        return target

    @staticmethod
    def _segments(path: str, *, allow_root: bool) -> tuple[str, ...]:
        if not isinstance(path, str):
            raise WorkspaceAuthorityError("path must be text")
        try:
            if len(path.encode("utf-8", errors="strict")) > _MAX_PATH_BYTES:
                raise WorkspaceAuthorityError("path exceeds byte bound")
        except UnicodeError:
            raise WorkspaceAuthorityError("path is not UTF-8 encodable") from None
        if path == ".":
            if allow_root:
                return ()
            raise WorkspaceAuthorityError("root is not a file target")
        if (
            not path
            or path.startswith("/")
            or path.endswith("/")
            or "\\" in path
            or ":" in path
            or "\0" in path
        ):
            raise WorkspaceAuthorityError("invalid logical workspace path")
        segments = tuple(path.split("/"))
        if any(segment in {"", ".", ".."} for segment in segments):
            raise WorkspaceAuthorityError("invalid logical workspace path")
        return segments

    @staticmethod
    def _is_redirection_status(status: os.stat_result) -> bool:
        attributes = getattr(status, "st_file_attributes", 0)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        return stat.S_ISLNK(status.st_mode) or bool(attributes & reparse)

    @classmethod
    def _kind(
        cls, status: os.stat_result
    ) -> Literal["file", "directory", "redirection", "other"]:
        if cls._is_redirection_status(status):
            return "redirection"
        if stat.S_ISREG(status.st_mode):
            return "file"
        if stat.S_ISDIR(status.st_mode):
            return "directory"
        return "other"
