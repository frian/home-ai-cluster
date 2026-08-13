# Aider Caller Edge Proof

Status: Successful

Date: 2026-08-13

## Purpose

This record retains privacy-safe evidence from one successful supported
one-machine implementation proof of the accepted RFC-0068 and RFC-0069 caller
edge:

```text
operator
  -> hac aider
  -> external Aider
  -> private ephemeral loopback translator
  -> one native HAC capability=code request
  -> textual result
  -> Aider-owned edit
```

It records one bounded composition only. It is not a general developer-tool
integration, a persistent service, or a compatibility expansion.

## Proof basis

The operator completed the proof manually against HAC revision
`cb7254a1d76f014c5cd686343dc56b262c7c7894`. The repository was clean before
the proof and clean after cleanup. External Aider reported exactly version
0.86.2. An already-running ordinary native HAC process was locally available
and declared `code`.

## Observed result

The caller selected one missing target. `hac aider` returned exit status zero;
afterward the target existed and was non-empty, and Aider reported applying the
edit. The disposable workspace contained exactly that one file.

HAC observed exactly one successful native `POST /v1/chat` request with
explicit `capability=code`; no second native request was observed. Generated
code was not executed, and Aider performed no Git, test, lint, or shell
automation.

The private caller-edge temporary integration material was not retained. A
local untracked `uv.lock` created by `uv run` during cleanup was removed; final
repository status was clean.

## Authority boundary

HAC core remained text-only. The one missing-target creation was the bounded
caller-edge authority accepted by RFC-0069. Target-content reading and editing
remained Aider authority. This proof grants HAC no filesystem, repository,
shell, Git, test, lint, tool, or execution authority.

## Privacy boundary

This record retains no prompt, generated source, target path, temporary path,
machine identity, runtime/model/adapter identity, authorization value, or raw
log/transcript.

## Scope preserved

This proves only the supported one-machine caller-edge composition. It does not
establish generic developer-tool support, interactive or multi-request Aider,
OpenAI compatibility expansion, shell or tool execution, autonomous coding,
safe arbitrary editing, or code correctness.

The physical two-machine RFC-0067 `code` proof remains pending. This proof does
not establish distributed execution and does not close that independent
requirement.
