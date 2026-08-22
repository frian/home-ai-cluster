# Code-File Real-Model Proof

Status: Successful

Date: 2026-08-22

## Purpose

This record retains privacy-safe evidence from a completed real-model operator
proof of the accepted RFC-0080 `hac code-file` caller edge:

```text
explicit existing target
  -> exactly one native capability=code request
  -> closed caller-local response envelope accepted
  -> complete atomic target replacement
```

The caller/protocol/filesystem proof succeeded. The sampled generated code did
not establish model instruction compliance or code quality.

## Proof basis

The operator completed two separate manual invocations after refreshing the
checkout at `ed3c617fbdca75b7f0cc3282adad63a23398497a`, the merge commit for
PR #507. The ordinary local HAC process declared `code`; each invocation used
one explicitly selected, already-existing disposable regular UTF-8 Python text
file outside the repository.

Each invocation used the accepted `hac code-file` surface with one selected
target, one operator-supplied message, and an explicit 900-second timeout. The
two observed wall-clock durations were approximately 46.2 seconds and 61.9
seconds. No prompt, target path, runtime/model identifier, generated source,
or raw server output is retained.

## Observed caller result

Both invocations returned exit status zero and emitted no success output. In
each case, the caller completely replaced only the selected target, preserved
its ordinary `0644` mode, and did not execute the generated content.

Because each real-model invocation completed successfully, the result passed
the implemented RFC-0080 caller boundary: one valid native `ClusterResult`,
one exactly accepted caller-local JSON document with `version = 1`, string
`content`, the generated-content bound, and successful atomic replacement.
This record does not claim direct observation or retention of the raw response
envelope.

The second invocation was a separate explicit operator action, not an automatic
HAC retry, correction, or continuation. No Aider lifecycle was involved, and
no visible caller retry or corrective request occurred.

## Model-quality observations

The first request explicitly required standard-library-only code. Its generated
replacement nevertheless imported `psutil`.

The separate second request narrowed the allowed implementation substantially.
Manual source inspection found that its generated replacement referenced
`re.search()` without importing `re`, used `MemFree` rather than the requested
`MemAvailable`, and assumed a `.percent` attribute on the value returned by
`shutil.disk_usage("/")`.

These are model instruction-compliance and apparent code-quality defects. The
generated files were not executed, so this proof does not establish syntax,
runtime, security, usefulness, or model suitability. It is not a code-quality
benchmark.

## Authority boundary

The operator selected the exact existing target. The model did not select a
path, and the caller wrote only the validated complete result to that selected
target. This proof grants no authority beyond accepted RFC-0080.

No repository discovery, multiple-file editing, missing-target creation, Git,
shell, tools, browser access, generated-code execution, lint/test execution,
Aider lifecycle, or model-directed filesystem authority was involved.

## Privacy boundary

This record retains no machine or user identity, absolute path, prompt,
generated source, runtime/model identifier, private runtime URL, authorization
value, or raw server log. The concise model-quality observations above are
retained only to distinguish caller behavior from generated-code quality.

## Conclusion

The real-model RFC-0080 caller proof succeeded: each invocation used one
explicit existing target, traversed one native `capability=code` request, passed
the closed caller-local response boundary, and atomically replaced that target
with ordinary mode preservation.

Both sampled generations showed instruction/code-quality defects. Those defects
are outside the caller guarantee and did not trigger retry, repair, execution,
or broader HAC authority. RFC-0080 therefore keeps deterministic caller
behavior separate from model quality without adding semantic inspection or an
agent loop.
