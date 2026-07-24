# RFC-0055: Ordinary Native Client Timeout

Status: Accepted

Date: 2026-07-24

Author: frian

## Summary

The ordinary native `chat` and `summarize` clients should share one fixed,
implementation-owned `httpx` scalar timeout of **120.0 seconds**. The contract
applies identically through both installed root names:

```sh
hac chat "Hello"
home-ai-cluster chat "Hello"
hac summarize --text "Source text"
home-ai-cluster summarize --text "Source text"
```

Connection failure remains `error: ordinary cluster unavailable`. Every
`httpx.TimeoutException` instead becomes `error: ordinary request timed out`.
Both outcomes write no standard output, write exactly one safe stable line to
standard error, and exit 1.

This is a client waiting-boundary correction only. It does not add an operator
timeout option, configuration, retries, streaming, cancellation, runtime or
server timeout, routing change, or implementation in this RFC PR.

## Problem

RFC-0045 established a finite, implementation-owned ordinary chat-client
timeout and grouped connection failure with timeout under `error: ordinary
cluster unavailable`. RFC-0054 applied that same capability-neutral client
failure behavior to the ordinary summarize client. RFC-0049 changes chat
success presentation only and remains authoritative for it.

The current shared scalar is 30.0 seconds. The merged native-client-timeout
investigation records valid local non-streaming work that did not complete in
that interval: ordinary chat generation exceeded 30 seconds, and a full README
summarization first timed out while warm executions later completed near 28
seconds. Those observations do not show that the ordinary cluster was
unavailable. They show that a connected request can wait longer than the
current client boundary before a complete result is available.

The project needs one small correction that preserves finite commands while
giving an operator a truthful, privacy-safe distinction between an unavailable
ordinary process and a request that exceeded the client wait boundary.

## Goals

This RFC proposes to:

* use one shared fixed 120.0-second scalar `httpx` timeout for ordinary chat
  and summarize clients;
* keep that value internal, implementation-owned, finite, and bounded;
* distinguish `httpx.ConnectError` from every `httpx.TimeoutException` with
  stable safe error lines;
* preserve all other existing native-client failure mappings and success
  behavior; and
* authorize only the smallest truthful internal seam needed to share the
  constant and, if useful, timeout translation.

## Non-goals

This RFC does not add or change:

* `--timeout`, environment variables, configuration files, or per-model,
  per-runtime, or per-capability timeout policy;
* retries, client-side fallback, streaming, partial results, cancellation
  protocols, background jobs, persistence, history, or prompt/response logging;
* adapter, server, Uvicorn, ASGI, Ollama, llama-server, routing, fallback,
  transport, attribution, lifecycle, static-cluster, LAN-exposure,
  authentication, dashboard, packaging, roadmap, or Phase 19 behavior; or
* implementation, tests, or unrelated cleanup in this RFC PR.

## Proposal

### Shared ordinary timeout

After a separate implementation PR, each ordinary native request made by
`chat` and `summarize` will construct its HTTPX client with the same internal
scalar timeout:

```python
120.0
```

This scalar is shared by the standalone `home-ai-cluster-chat` command and the
two root entry-point forms, `hac` and `home-ai-cluster`, which already delegate
to the same ordinary command behavior. It applies identically to the ordinary
native `chat` and `summarize` clients; executable identity does not change it.

An HTTPX scalar timeout expands to equal pool, connect, write, and read timeout
values. It is therefore **not** a strict 120-second total command deadline.
Total elapsed time can include those distinct operations and multiple reads.
For the existing non-streaming request boundary, the response wait is commonly
the relevant limit, but this RFC does not create a separate read-only policy.

No operator option, environment variable, or configuration file exposes the
value. The clients remain finite and bounded, but 120 seconds is not a
guarantee that every model, prompt, runtime state, or cold load will complete.

### Failure translation

The ordinary clients will own these exception translations:

| Exception | Standard error | Exit |
| --- | --- | --- |
| `httpx.ConnectError` | `error: ordinary cluster unavailable` | 1 |
| Any `httpx.TimeoutException` | `error: ordinary request timed out` | 1 |
| Other `httpx.RequestError` | `error: ordinary request failed` | 1 |

Every listed client failure writes nothing to stdout and exactly its one stable
line to stderr. It exposes no raw exception, URL, address, request, response,
prompt, source text, generated text, credential, or machine detail. Existing
HTTP status, parsing, local-input, and successful-output mappings remain
unchanged. This is not a broad generic error taxonomy.

`httpx.TimeoutException` includes its timeout subtypes. A timeout does not by
itself establish that the ordinary process is unavailable, so it must not use
the connection-failure wording.

### Small shared implementation seam

The later implementation may use the smallest truthful shared seam for the
120.0 constant, the timeout error string if useful, and timeout exception
translation. The existing arrangement may remain simple: one command module may
own a narrowly shared internal constant/helper, or a tiny capability-neutral
internal module may be used if that is demonstrably smaller and clearer.

This RFC does not authorize a general HTTP-client abstraction, command
inheritance, a plugin system, a configurable timeout framework, or broad
refactoring.

### Runtime and server boundary

This proposal changes only the ordinary CLI client's waiting boundary. It does
not add or change adapter timeouts, request cancellation, server timeouts, or
runtime behavior. It does not change Uvicorn, ASGI, Ollama, llama-server,
routing, fallback, transport, attribution, lifecycle, or static-cluster
behavior.

After a client timeout, a request may or may not continue server-side. That
behavior remains unspecified; this RFC does not promise server or runtime
cancellation and does not infer it from a client-side timeout.

## Rationale

Thirty seconds has been demonstrated too short for ordinary local,
non-streaming generation. A successful warm summarize execution was observed
near 28 seconds, ordinary chat generation exceeded 30 seconds, and cold model
loading adds further delay. Sixty seconds leaves limited margin over those
observations. Three hundred seconds delays operator feedback excessively when a
runtime is stalled. One shared 120-second scalar is a boring middle value: long
enough to move the ordinary boundary materially beyond the evidence, yet still
finite. It is not a universal performance promise.

Chat and summarize each send one bounded native request to the same ordinary
process and wait for one complete non-streaming `ClusterResult`. They do not
expose runtime, model, or capability performance selectors. One shared client
value is therefore smaller and more coherent than per-model, per-runtime, or
per-capability policy.

Separating a connection error from a timeout gives an operator a truthful next
distinction without revealing private details. Keeping the value internal
preserves the project-owned ordinary contract and avoids a public configuration
surface before evidence justifies one.

## Alternatives considered

### Keep 30 seconds and the current shared error

Rejected. It keeps commands finite but retains the demonstrated false
unavailability outcome and an unreliable boundary for valid ordinary work.

### Increase the timeout only

Rejected. It reduces premature failure but still reports a timeout as cluster
unavailability.

### Distinguish timeout only

Rejected. It improves truthfulness but leaves 30 seconds too short for the
observed ordinary requests.

### Increase the timeout and distinguish the error

Selected. One shared 120-second scalar plus a distinct timeout line is the
smallest durable correction: finite, topology-blind, privacy-safe, and limited
to the ordinary client edge.

### Add `--timeout`

Rejected. It creates a durable public option, validation and documentation
rules, scripting variance, and a path for chat and summarize to drift. The
evidence supports one project-owned default, not per-invocation policy.

### Remove the timeout

Rejected. It avoids the observed premature result but permits indefinitely
blocked commands for a stalled runtime or broken response path.

### Use separate chat and summarize values

Rejected. The clients share the same non-streaming ordinary process boundary,
and current evidence does not justify capability-specific policy.

### Streaming

Rejected. Streaming would add partial-result, disconnect, and cancellation
lifecycle decisions; it is not required for this waiting-boundary correction.

### Runtime-side timeout or cancellation

Rejected. Adapter/server timeout and cancellation behavior are distinct
runtime and lifecycle decisions. This RFC changes neither.

## Trade-offs

The selected value can leave an operator waiting longer before feedback when a
request is stalled. That is the cost of giving ordinary local generation enough
margin beyond the demonstrated 30-second boundary. The commands nevertheless
remain finite, and the new timeout line makes the result more accurate without
leaking details.

One shared scalar deliberately does not optimize for every model or prompt. It
keeps the first correction understandable and revisable rather than turning two
small clients into a policy system.

## Impact

This RFC amends the observable ordinary-client timeout and failure portions of
RFC-0045 for chat and RFC-0054 for summarize. It preserves RFC-0049 success
presentation, the native endpoints, request and result models, every HTTP
status mapping other than timeout-exception translation, topology blindness,
and engine independence.

After acceptance, a separate implementation PR may make only the smallest
necessary client-edge change and add focused tests. It must not treat this RFC
as authority for a generalized client framework or unrelated refactoring.

### Later implementation evidence

The implementation PR must prove at minimum that:

1. both clients use the same 120.0-second timeout;
2. HTTPX client construction receives that value;
3. `ConnectError` retains the unavailable message;
4. each `TimeoutException` subtype maps to the timeout message;
5. other `RequestError` retains `error: ordinary request failed`;
6. stdout remains empty on failures and raw exception details do not leak; and
7. existing success, HTTP-status, parsing, and output behavior remains
   unchanged.

Focused mock tests are sufficient for those implementation checks. A bounded
operator verification should additionally include both chat and summarize: one
slow-but-completing request that exceeds 30 seconds but completes under 120,
and, if feasible without waiting 120 real seconds, one synthetic or controlled
timeout-path verification. A live timeout test is not required in the normal
automated suite.

## Open questions

None for this narrow proposed contract. Internal module and helper placement
remain implementation details within the small shared-seam boundary above.

## Decision

Accepted.

Ordinary native `chat` and `summarize` clients share one fixed internal HTTPX
scalar timeout of 120.0 seconds. The scalar applies independently to HTTPX
pool, connect, write, and read operations; it is not a strict total command
deadline. `httpx.ConnectError` maps to `error: ordinary cluster unavailable`,
and every `httpx.TimeoutException` maps to `error: ordinary request timed out`.
Both errors write no stdout, one safe stderr line, and exit 1.

No `--timeout`, environment variable, configuration, retry, streaming,
cancellation, runtime timeout, routing, lifecycle, roadmap, or Phase 19 change
is accepted.
