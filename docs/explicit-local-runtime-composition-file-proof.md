# Explicit Local Runtime Composition File Proof

Status: Successful

Date: 2026-08-17

## Purpose

This record retains one privacy-safe real-local observation of the accepted and
implemented RFC-0074 explicit local runtime-composition file path.

## Setup

- One ordinary local HAC process was started using only one explicitly selected
  RFC-0074 runtime-composition TOML file.
- No equivalent runtime-composition CLI argument was supplied. The retained
  file selected one already-installed local Ollama model and set the accepted
  `disable_thinking` field.
- One real native HAC `code` request was sent to that running process.

## Observed evidence

- The `code` request completed successfully with a normal textual response in
  approximately 19 seconds of wall-clock time. This is an observation only,
  not a benchmark or performance guarantee.
- A separate boundary probe supplied both `--runtime-config <PATH>` and
  `--runtime ollama`. It failed immediately through ordinary CLI validation
  with an error equivalent to: `--runtime-config cannot be combined with
  explicitly supplied runtime composition arguments`.
- That conflicting invocation did not proceed to ordinary server startup.

## Interpretation

The explicit runtime-composition file works on one real local Ollama path. The
existing implicit CLI defaults do not conflict with file mode, while an
equivalent runtime argument explicitly supplied by the operator is rejected as
a second composition source. The retained file reaches the already-existing
runtime, model, and thinking composition behavior. This operator path is
therefore not covered only by deterministic unit tests.

## What this does not establish

This is not a universal performance claim, a claim that every model or runtime
behaves similarly, or a comparison of TOML and CLI startup. It does not change
routing or select models per request or capability. It does not configure
static-cluster topology, expose runtime configuration through status, prove a
llama-server real-local run, or require separate physical proofs for every
deterministic RFC-0074 case.

## Privacy and scope boundary

This record excludes temporary-file contents and paths, model identifiers,
prompts, generated output, raw HTTP traffic, process identifiers, machine or
user identity, home-directory paths, addresses, credentials, and unnecessary
environment details. Temporary proof material is not retained.

This is implementation evidence only. It authorizes no new architecture or
change to code, tests, RFCs, routing, topology, status, lifecycle, discovery,
or runtime boundaries.
