# Code-File Target-Creation Real-Model Proof

Status: Successful

Date: 2026-08-22

## Purpose

This record retains privacy-safe evidence from a completed real-model operator
proof of accepted RFC-0081's narrow amendment to the RFC-0080 `hac code-file`
caller edge:

```text
explicit absent target
  -> exclusive empty-leaf creation
  -> implemented one-request code-file path
  -> closed caller-local response accepted
  -> complete atomic replacement
```

It establishes that the intended practical workflow can begin with one
explicitly selected absent target. It is not a model benchmark and does not
expand the caller guarantee.

## Proof basis

The operator completed the proof manually after PR #510 merged at
`ceb62abf1cca3a5781a247a7fe7868c6eb3b4dfe`. An ordinary local HAC process
with `code` capability was already available.

Before the invocation, the operator removed the disposable target and verified
that it was absent. No `touch` or other target-creation command occurred before
the operator invoked `hac code-file` with that explicitly selected target, an
explicit 900-second timeout, and an operator request for a minimal
standard-library Python file. The request constrained the source to importing
only `sys` and printing the current Python version through
`sys.version.split()[0]`; the raw prompt is not retained.

The real-model invocation completed successfully and silently in approximately
19.6 seconds of wall-clock time.

## Observed caller result

RFC-0081 caller result: **PASS**.

After successful completion, manual inspection found that the previously absent
target existed as a regular 40-byte file with ordinary mode `0644`. Its
initially created empty content had been replaced by a minimal two-line Python
program that imported only `sys` and printed the requested version expression.
The generated program was not executed.

The successful command returned exit status zero and emitted no success output.
The observed final `0644` mode is consistent with RFC-0081's requested
non-executable `0o666` creation mode under an ordinary `0o022`-style umask,
followed by RFC-0080 ordinary-mode preservation. This proof observes the final
mode; controlled model-free tests establish the umask mechanism separately.

The merged implementation defines the bounded path traversed by this successful
invocation:

```text
prospective empty-content request validation
  -> exclusive target creation
  -> native capability=code request
  -> closed response validation
  -> atomic replacement
```

This record does not claim independently captured or counted wire traffic. Nor
does it claim direct observation of the raw response envelope; successful
replacement implies that the result passed the implemented strict caller-local
envelope validation.

## Model-quality observation

Instruction compliance was favorable for this single inspected sample: the
source used only the requested import, used the requested version expression,
and was minimal. The program was not executed, so this observation establishes
neither runtime correctness nor model correctness, reliability, security,
benchmark quality, or general code-generation suitability.

## Authority boundary

This proof exercises only authority accepted by RFC-0080 and RFC-0081. The
operator selected the exact target; the model did not choose a path, filename,
parent, sibling, or repository location. RFC-0081 adds only caller-edge
authority to create that exact selected missing leaf.

No parent-directory or sibling creation, repository discovery, multiple-file
editing, Git, shell, linting, testing, browser access, tool execution,
generated-code execution, retry, repair, reflection, Aider lifecycle, or agent
loop was involved.

## Privacy boundary

This record retains no machine hostname, username, absolute target path, raw
operator prompt, complete generated source, runtime or model identifier,
private runtime URL, authorization value, or raw server log.

## Relationship to RFC-0080 proof

This proof complements rather than replaces the
[RFC-0080 code-file real-model proof](code-file-real-model-proof.md). The
earlier proof established the real-model existing-target replacement path. This
record establishes RFC-0081's additional absent-target creation path without
changing the existing caller boundary.

## Conclusion

The real-model RFC-0081 missing-target proof passed: an explicitly selected
target was verified absent, `hac code-file` created and populated it without
manual preparation, and the resulting regular file had observed mode `0644`.
Generated code was not executed. The favorable source observation is one
inspected sample and remains separate from the caller guarantee.
