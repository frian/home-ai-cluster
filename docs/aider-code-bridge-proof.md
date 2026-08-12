# Aider Code Bridge Proof

Status: Successful

Date: 2026-08-13

## Purpose

This record retains privacy-safe evidence from one bounded one-machine
execution of:

```text
operator
  -> Aider
  -> temporary caller-owned loopback bridge
  -> native HAC POST /v1/chat with capability=code
  -> textual ClusterResult
  -> Aider-owned disposable target-file edit
```

It is an observed caller-side composition, not implementation, a supported
integration, or an architectural decision.

## Proof base

HAC revision: `db1419effbe08f076cb9e6f7dfe29aea21a5e1b2`

Aider: `0.86.2`

The repository working tree was clean after proof cleanup. No model or runtime
identifier is retained.

## Topology

The proof used one physical machine:

```text
Aider
  -> loopback temporary bridge
  -> loopback native HAC process
```

The bridge was temporary, caller-owned, loopback-only, and outside project
implementation.

## Observed request path

Exactly one bridge request was accepted. The bridge forwarded exactly one
native HAC request with explicit `capability=code`; HAC returned one successful
textual result. The bridge emitted:

```text
bridge_observation accepted_request=1 capability=code outcome=success
```

The single-use bridge then stopped. No message or response content is retained.

## Caller-owned edit observation

Aider had one disposable target file in scope. The target changed, and the
workspace contained no other target files. No generated code was executed; no
automatic test or lint ran; no shell execution by Aider was observed; and no
automatic Git commit occurred. This observation does not claim semantic,
patch, or code correctness.

## Authority boundary

```text
HAC              -> semantic capability validation/routing and textual result
temporary bridge -> strict caller-side translation only
Aider            -> filesystem ownership and edit application
```

This observation gives HAC no filesystem, repository, shell, Git, testing,
lint, tool/function, or code-execution authority.

## Privacy and cleanup

No prompt, generated source, generated response, temporary path, machine name,
runtime/model identifier, authorization value, or raw transcript is retained.
Temporary proof material was removed, including the caller-side bridge and
disposable workspace.

## Scope preserved

This proof does not establish first-class or supported HAC/Aider integration,
a stable bridge API, general OpenAI compatibility for `code`, generic or safe
arbitrary file editing, patch or code correctness, code execution,
tools/function calling, agent authority, HAC repository access, HAC shell
access, or distributed code execution.

## Relationship to RFC-0067 physical proof

The separate physical two-machine RFC-0067 `code` proof remains pending. This
one-machine caller-side proof does not satisfy that requirement, and it does
not change the `Status: Partial` of the
[bounded textual code assistance proof](bounded-textual-code-assistance-proof.md).

## Conclusion

Aider 0.86.2 successfully consumed one textual result obtained through an
explicit native HAC `code` request and used that text to modify one disposable
caller-owned file, while HAC retained no filesystem or execution authority. The
observation does not generalize beyond this bounded configuration.
