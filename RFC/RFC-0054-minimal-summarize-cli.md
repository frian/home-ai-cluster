# RFC-0054: Minimal Summarize CLI

Status: Draft

Date: 2026-07-24

Author: frian

## Summary

This RFC proposes one ordinary one-shot root subcommand for the already
accepted native `summarize` capability:

```sh
hac summarize --text <TEXT>
home-ai-cluster summarize --text <TEXT>
```

The command would be a thin, topology-blind client of an already-running
ordinary local-only or explicit static-cluster process. It would validate one
required `--text` source through the existing authoritative `SummarizeRequest`
model, make one fixed-loopback native request, validate the existing
`ClusterResult`, and present it with the established native chat CLI modes.

This is a proposal only. The accepted current state remains native API-only
summarize access. This RFC does not add a command, implementation, package
entry point, roadmap phase, or Phase 19.

## Problem

RFC-0051 accepted bounded native text summarization with a dedicated
`POST /v1/summarize` endpoint, a distinct normalized request, existing routing
and result attribution, and local as well as explicit static-cluster execution.
It deliberately excluded a root summarize command from that increment.

An operator who wants one ordinary bounded summary from a terminal must still
construct the native HTTP method, fixed target, JSON body, and response handling
manually. The existing `home-ai-cluster-chat` command demonstrates that one
small installed native client can remove that transport construction while
leaving the running cluster process authoritative.

The project needs a deliberately bounded decision if it chooses to make that
operator access ordinary. It must not turn source text into a chat message,
redefine the accepted native request, give a client topology or runtime
authority, or bundle file and document ingestion with text summarization.

## Goals

This RFC proposes to:

* add one discoverable root subcommand, `summarize`, through both existing
  installed root names;
* accept exactly one bounded source-text value through `--text`;
* reuse `SummarizeRequest` as the sole local source-text validation authority;
* make exactly one existing native request to the ordinary fixed loopback
  summarize endpoint;
* reuse the existing `ClusterResult` and native chat CLI presentation modes;
* preserve local-first, capability-centered routing, bounded fallback, and
  cluster-owned final node attribution in the already-running process; and
* retain prompt-free, topology-blind, privacy-safe client failures.

## Non-goals

This RFC does not add or accept:

* positional input, standard input, automatic pipe detection, file or directory
  input, URLs, clipboard input, PDF handling, or document extraction;
* batching, multiple documents, streaming, chunking, recursive summarization,
  history, persistence, sessions, interactive operation, multi-turn operation,
  prompt templates, summary-style controls, or summary-length controls;
* model, node, runtime, capability, routing, host, port, declaration, timeout,
  retry, or client-fallback options;
* a new native endpoint, an OpenAI-compatible summarize endpoint, LAN exposure,
  authentication, process lifecycle management, discovery, or a configuration
  framework;
* a wrapper, a new alias, a standalone `home-ai-cluster-summarize` package
  entry point, a generic request-client abstraction, a generalized output
  framework, or a CLI-framework rewrite;
* changes to `SummarizeRequest`, `ClusterResult`, native routing, transport,
  runtime adapters, static declarations, fallback policy, result attribution,
  application lifecycle, packaging outside the existing root entry points,
  the roadmap, or Phase 19; or
* implementation, tests, or unrelated cleanup in this RFC PR.

## Proposal

### Root command scope

After a later implementation, the existing shared root function would recognize
one additional exact subcommand:

```text
hac summarize --text <TEXT>
home-ai-cluster summarize --text <TEXT>
```

`hac` and `home-ai-cluster` already invoke the same root CLI function under
RFC-0052. This proposal adds no alias, wrapper, second parser, or standalone
console script. The existing root subcommands and standalone commands remain
unchanged.

The command is a finite one-shot client, not a process launcher, runtime
client, topology reader, static-declaration reader, status command, routing
explanation command, session, or interactive application. It does not start,
stop, configure, inspect, supervise, or otherwise own the cluster process.

### Input and authoritative validation

The sole accepted source is exactly one required option:

```text
--text <TEXT>
```

One `--text` value is valid only when construction of the existing
`SummarizeRequest(text=<TEXT>)` succeeds. The client must construct that model
before it constructs or invokes an HTTP client. It must not reproduce Pydantic
validation details or independently implement the 65,536-byte UTF-8 rule.

Consequently, the existing model remains authoritative: accepted source-text
whitespace is preserved unchanged, and an empty, whitespace-only, non-string,
or over-limit value is invalid. The client must send the validated model's text
value unchanged.

Missing `--text`, repeated `--text`, a positional token, unknown arguments, or
the mutually exclusive output options together are invalid local input. No
positional source, stdin, automatic pipe detection, file source, or source
precedence system exists. Multi-word source text uses ordinary shell quoting;
the client must not join surplus shell tokens.

Every invalid local input performs no request, writes no stdout, writes exactly
the existing safe local line below to stderr, and exits 2:

```text
error: invalid request input
```

That stable line does not reveal source text, validation internals, or the
numeric byte limit.

### Fixed native request boundary

For one valid input, the command makes exactly one request:

```text
POST http://127.0.0.1:8000/v1/summarize
```

Its JSON body is exactly:

```json
{"text":"<validated text>"}
```

The command accepts no host, port, declaration, node, adapter, runtime, model,
capability, routing, timeout, retry, or fallback option. It owns one finite,
implementation-owned timeout and performs no retry or client-side fallback.

The fixed loopback endpoint is the already-established ordinary process
boundary. It works without client changes against local-only and explicit
static-cluster composition. The client knows nothing of nodes, adapters,
models, declarations, addresses, routing candidates, or fallback execution.
The running process retains capability-centered eligibility, local-first
selection, bounded fallback, remote transport, and lifecycle authority.

### Validated success presentation

Before success output, the client must validate the HTTP success body as the
existing authoritative `ClusterResult`. It must not pass through arbitrary
JSON or create a summarize-specific response model or envelope.

After that validation, it uses the existing native chat CLI presentation modes
exactly:

* Without an output option, write only `ClusterResult.content` to stdout. Do
  not strip, wrap, escape, reindent, or normalize its internal whitespace.
  Follow the chat command's terminal-newline rule: add one final newline only
  when content does not already end in `\n`; empty content writes one newline.
* `-v` and `--verbose` are equivalent. Use the existing chat verbose structure,
  field order, labels, punctuation, stdout destination, and newline behavior:

  ```text
  Response:
  <content>

  Execution:
    Node: <node_id>
    Adapter: <adapter>
    Model: <model>
  ```

  Omit `Model` exactly when the existing chat formatter does: its value is
  `None` or empty. No summarize-specific verbose format is defined.
* `--json` writes the compact validated `ClusterResult` JSON representation,
  with the established field order and one final newline.

`--verbose`/`-v` and `--json` are mutually exclusive. Their combination uses
the same local invalid-input behavior and exit status 2; it makes no request.
Mode selection must not depend on TTY state, pipes, redirection, environment,
terminal properties, or color support.

`content`, `adapter`, optional `model`, and `node_id` retain their existing
meaning. In particular, `node_id` is cluster-owned final selected-candidate
attribution under RFC-0023, not a client-inferred machine identity.

### Failure and exit contract

On every failure, stdout is empty, stderr contains exactly one safe stable
line, and the command exits non-zero. The client must not emit source text,
summary content, request or response bodies, runtime or remote URLs, private
addresses, declarations, raw exceptions, tracebacks, authorization values,
credentials, or private machine details.

The proposed contract is:

| Condition | Standard error | Exit |
| --- | --- | --- |
| Invalid local input | `error: invalid request input` | 2 |
| Connection failure or timeout | `error: ordinary cluster unavailable` | 1 |
| HTTP 422 native rejection | `error: cluster rejected request` | 1 |
| HTTP 404 no summarize capability | `error: no available summarize capability` | 1 |
| HTTP 503 runtime or cluster unavailability | `error: runtime adapter unavailable` | 1 |
| Invalid or malformed successful response | `error: invalid cluster response` | 1 |
| Unexpected HTTP status or other client failure | `error: ordinary request failed` | 1 |

The connection, timeout, native rejection, runtime-unavailability, invalid
response, and unexpected-failure terms reuse existing native chat client
behavior because they are capability-neutral. The 404 line is deliberately
summarize-specific rather than mechanically retaining the untruthful
chat-capability wording. This adds no generic error taxonomy.

### Privacy and compatibility boundary

The command must not log, persist, cache, retain, or add history for source
text, summaries, requests, or responses. Standard output is direct operator
output; shell history, process inspection, terminal scrollback, and redirection
are external to project-controlled retention. As with the native chat command,
command-line source text is not secure secret input and this limitation must be
documented with an eventual implementation.

The accepted native API remains available and unchanged. OpenAI-compatible
access remains chat-only. The proposed client does not make local-only and
static-cluster operation distinguishable at its edge, and it introduces no
engine-specific behavior.

## Rationale

One root subcommand with an explicit one-value option is the smallest durable
operator contract if the project chooses to add a summarize CLI. It removes
manual construction of the already-accepted native request while keeping the
purpose of the value visible in shells and scripts. It reuses the root namespace
that operators already discover through both installed names and avoids a new
executable or parallel command tree.

An explicit option is smaller and safer than broader input forms. It keeps one
visible source boundary, preserves shell argument boundaries, and lets the
existing normalized request model determine validity without a second byte-limit
implementation. A fixed loopback target preserves the established process
boundary: the cluster, rather than the client, selects an allowed local or
declared remote candidate.

The existing chat presentation modes fit because summarize returns the same
validated textual result and truthful attribution shape. Reusing them avoids a
new output vocabulary while preserving direct terminal readability, deliberate
human attribution, and compact automation output.

## Alternatives considered

### Keep native API-only access

This remains the lowest-scope alternative and preserves the current accepted
state. It is sufficient for operators comfortable with HTTP, but leaves each
ordinary terminal use to construct the method, loopback URL, JSON, and response
handling manually. This RFC proposes a small client only if the project accepts
that demonstrated operator friction warrants it.

### Root subcommand with required `--text`

Selected in this draft. It is explicit, discoverable through the existing root,
script-friendly, and one-source bounded. It requires one additive root contract
but no new executable, configuration, or topology authority.

### Positional text

Rejected for the first increment. Although chat now accepts one positional
message, source text is not a chat message and an explicit `--text` better
expresses its distinct semantic role. Positional input also creates a second
durable spelling and sharper shell-quoting and surplus-token questions without
evidence that the additional ergonomics is needed.

### Standalone `home-ai-cluster-summarize` command

Rejected. It would add a package entry point and a separate discoverability
surface when both installed root names already dispatch through one function.
There is no evidence that an ordinary summarize action should be excluded from
that namespace.

### Standard input

Rejected. It introduces blocking, TTY, empty-input, source-precedence, and
automatic-pipe-detection semantics beyond the one-value contract. It is not
needed to make the first bounded terminal request ordinary.

### File input

Rejected. It introduces paths, encoding, file privacy, size-enforcement timing,
filesystem errors, and a strong pull toward document ingestion. Those are
separate decisions from bounded supplied-text summarization.

## Trade-offs

The proposal makes an existing native capability easier to use interactively
and from small scripts while preserving direct API access. It adds one durable
root subcommand and a focused client contract, including a parallel truthful
404 error line. That cost is bounded by one source, one request, existing
models, existing output modes, a fixed target, and no client topology or
lifecycle authority.

Command-line source text remains visible to local shell and process mechanisms.
This matches the accepted chat-client limitation and is explicitly not presented
as secret input. Operators needing file or secret-input behavior retain the
native API and may pursue a separate RFC if evidence justifies it.

## Impact

If accepted, a later implementation PR may add only the smallest necessary
command-specific client and root forwarding integration, focused tests, and
operator documentation. It should reuse existing native chat client seams where
they genuinely apply: one-request `httpx` construction, finite timeout, result
validation, safe failure handling, and presentation. It must reuse
`SummarizeRequest` directly for source validation.

That implementation is not authorized by this RFC PR. This RFC also does not
authorize a generic request-client abstraction, a generalized output framework,
a CLI-framework rewrite, packaging changes beyond the existing root entry
points, or unrelated refactoring.

A later implementation proof should cover successful request construction and
each presentation mode; local rejection before HTTP client construction;
authoritative whitespace and byte-bound validation reuse; output-mode
exclusivity; safe failure mapping; response validation; root forwarding through
both installed names; and topology blindness. Request-capture tests are
sufficient; no live runtime, LAN, or two-machine proof is required for this
client-edge change.

## Open questions

None for this narrow proposed contract.

## Decision

Pending.
