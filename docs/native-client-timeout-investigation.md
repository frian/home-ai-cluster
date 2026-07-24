# Native Client Timeout Investigation

## Status and question

Investigation only. This document changes no RFC, timeout, error, client,
runtime, routing, transport, lifecycle, package, roadmap, or Phase 19 state.
It does not authorize implementation.

Question: does the ordinary native client timeout contract remain usable for
both one-shot `chat` and `summarize`, and what is the smallest durable
correction if it does not?

Recent local operator observations establish a real boundary problem. A short
chat completed in about 7.5 seconds, while a different chat timed out twice at
about 30.4 and 30.7 seconds. A full README summarization first timed out and
later warm executions completed in about 28 seconds. These observations do not
show an unavailable cluster. They show that a completed non-streaming result may
not arrive before the current client timeout.

## Current accepted and implemented contract

RFC-0045 owns the original ordinary chat client timeout and public failure
contract: one finite implementation-owned timeout, no timeout option, retry,
or client fallback, and one shared `error: ordinary cluster unavailable` result
for connection failure or timeout. RFC-0049 preserves that behavior while
changing chat success presentation only. RFC-0054 applies the same finite
client boundary and capability-neutral failures to summarize; it deliberately
uses different wording only for summarize's 404 capability outcome. RFC-0051
owns native summarization and its existing local/static-cluster routing, but not
a separate client timeout policy.

The implementation has one concrete timeout owner:

```python
# chat_command.py
_REQUEST_TIMEOUT_SECONDS = 30.0
```

`chat_command` passes that value to its synchronous `httpx.Client`. The small
`summarize_command` imports that exact constant and passes it to an equivalent
synchronous client. Both therefore use exactly 30.0 seconds today. The shared
value is an implementation seam, not yet a separately accepted generic client
framework.

Both commands make one non-streaming POST to an already-running loopback
ordinary process, then wait for one complete `ClusterResult`. The clients own
neither routing nor runtime execution. In contrast, both current local runtime
adapters use `httpx.AsyncClient(timeout=None)` for their runtime call. Thus the
ordinary client can time out while the accepted application has no adapter-side
model-response timeout.

## What `httpx.Client(timeout=30.0)` means here

The installed `httpx` version is 0.28.1. Its scalar `Timeout(30.0)` expands to
all four timeout fields:

```text
connect = 30.0
read    = 30.0
write   = 30.0
pool    = 30.0
```

It is therefore inaccurate to call the current scalar a strict 30-second total
command deadline. It supplies four per-operation limits:

| Phase | Current meaning for the ordinary client |
| --- | --- |
| Pool | At most 30 seconds waiting for a connection from the client pool. |
| Connect | At most 30 seconds establishing the loopback connection. |
| Write | At most 30 seconds for a request-body write operation. |
| Read | At most 30 seconds waiting for a response read operation. |

For these small JSON requests, upload is normally not the observed concern, but
the accepted 64 KiB summarize source bound still passes through the write
boundary. Response headers and response-body reads are read-boundary work. A
non-streaming runtime normally produces no useful response body until it has
completed the generation and the application has normalized its result. That
makes a read timeout a plausible outcome after the request was accepted and
while generation is still in progress.

None of the four limits is a total elapsed-command timer. Total elapsed time can
include pool, connect, write, and multiple read operations. Conversely, a
non-streaming request that produces no headers or body while the model works can
reach the read timeout near 30 seconds. Model loading and model generation are
server/runtime work, not separately timed client phases; their duration can be
observed indirectly only while the client waits for response data.

## Current failure translation and observability

Both clients catch `httpx.ConnectError` and every `httpx.TimeoutException`
together and translate either to:

```text
error: ordinary cluster unavailable
```

Both map other `httpx.RequestError` values and unexpected client exceptions to:

```text
error: ordinary request failed
```

They validate an HTTP-success body only after it arrives. Invalid JSON or an
invalid `ClusterResult` maps to `error: invalid cluster response`; 422, 404,
and 503 retain their existing command-specific mappings. No client error prints
request content, result content, response bodies, URLs, addresses, exceptions,
or credentials.

The current wording is accurate for a `ConnectError`, but a timeout does not by
itself prove that the cluster is unavailable. The observed near-30-second
outcomes are compatible with a successful connection, accepted request, and
runtime generation that has not yet yielded a complete response.

The application and adapters have no explicit client-disconnect check,
cancellation protocol, or cancellation propagation. The adapters have no model
response timeout. This means a server/runtime *may* continue after the client
has abandoned its HTTP request, but source inspection does not prove the exact
Uvicorn, ASGI, Ollama, or llama-server behavior for every disconnect. A
controlled runtime observation would be required to claim that it definitely
continues or is cancelled.

Current process logs do not close that evidence gap. `hac local` uses Uvicorn's
ordinary logging without a project-specific request-stage logger; no client,
route, orchestration, or adapter logging records connection state, request
acceptance, generation progress, timeout, or post-disconnect completion.
Uvicorn access output may record a completed HTTP response, but it does not
provide a privacy-safe, complete lifecycle account. The project must not add
prompt or response logging merely to diagnose this boundary.

Focused command tests prove deterministic exception translation: they inject
`ConnectError` and `TimeoutException`, assert the safe line and exit status,
and use immediate mocked success and HTTP responses. They do not model a slow
server, distinguish connect/read/write/pool timeout classes, measure response
duration, prove request transmission before a timeout, or observe server work
after a disconnect.

## Options

### A — Keep the current behavior

Keep one 30-second scalar timeout and the shared unavailable error. This is the
lowest-change option and preserves bounded one-shot completion. Its cost is
demonstrated operator ambiguity: an available ordinary process can be reported
as unavailable when a valid non-streaming result is simply slow. It also makes
warm results near the boundary unreliable.

### B — Increase the fixed timeout only

Keep one internal shared scalar for both clients but use a longer value. 60
seconds doubles the current allowance but offers little margin over observed
near-30-second completions and cold-model work. 120 seconds is a bounded,
simple middle value that materially separates ordinary model work from the
observed boundary without leaving a terminal blocked for five minutes. 300
seconds tolerates more cold or long generations but worsens feedback when a
runtime is stalled.

One shared value is appropriate for the current two native textual clients:
both await one complete non-streaming `ClusterResult` from the same ordinary
loopback process and neither exposes model/runtime selectors. This is not a
claim that chat and summarize have identical runtime cost. It is a deliberately
small operator boundary until evidence warrants a different contract.

Increasing the value alone avoids false unavailability more often, but it
retains the untruthful timeout wording and does not explain a genuine long wait.

### C — Distinguish timeout from unavailability only

Retain 30 seconds but map `TimeoutException` to a stable separate line such as:

```text
error: ordinary request timed out
```

This is more truthful than treating timeout as connection failure. It leaves the
demonstrated usability problem intact: a valid local generation near or above
30 seconds still cannot complete through either ordinary client.

### D — Increase the fixed timeout and distinguish the error

Use one longer finite shared per-operation timeout and map connection failure
and timeout separately. This keeps commands bounded, preserves a fixed
topology-blind client edge, and gives an operator a truthful next distinction
without exposing private details. It changes no routing, fallback, runtime, or
lifecycle authority.

This is the smallest durable correction supported by the observations. It does
not promise a strict total duration: the RFC and implementation would need to
describe the selected `httpx` timeout accurately as per-operation behavior.

### E — Add `--timeout`

Reject for the first correction. It adds a durable public option, parsing and
validation rules, scripting variance, documentation, and the risk that chat and
summarize drift. The observed issue is one project-owned default boundary, not
evidence that every invocation needs an operator-selected timeout.

### F — Remove the timeout

Reject. It prevents the demonstrated false failure but permits indefinitely
blocked commands for a stalled runtime or broken response path. A finite
operator boundary remains important even though it is not a strict total
deadline.

### G — Streaming

Out of scope. The current native clients, result model, endpoint behavior, and
RFCs are non-streaming. Streaming would introduce partial-result, disconnect,
and cancellation lifecycle decisions and is not justified as a timeout fix.

## Recommendation and required decision

Create a new narrow RFC before implementation. It should amend the observable
RFC-0045 timeout and failure contract and the RFC-0054 inherited summarize
contract, while preserving RFC-0049 presentation behavior. It should select:

1. one shared fixed, implementation-owned **per-operation** timeout for chat
   and summarize, with 120 seconds the recommended starting proposal;
2. `error: ordinary cluster unavailable` for connection failure; and
3. `error: ordinary request timed out` for `httpx.TimeoutException`.

The RFC should require focused mock tests for the distinct exception paths and
the shared constant, plus a bounded local operator verification covering a
slow-but-completing request. It should not add a timeout option, retry,
client-side fallback, streaming, cancellation protocol, runtime timeout,
logging, routing change, or configuration surface.

The numeric value requires explicit rationale at RFC review. The current local
observations show 30 seconds is too close to ordinary completion but do not
prove that 120 seconds is universally sufficient. That is acceptable for one
small, revisable fixed default; it is not a basis for per-model policy.

## Non-goals

This investigation does not implement or change a timeout, error text, client,
test, RFC status, package, environment variable, configuration file,
per-runtime/model policy, retry, fallback, streaming, cancellation protocol,
background job, persistence, history, runtime, routing, transport, lifecycle,
LAN exposure, authentication, dashboard, roadmap, or Phase 19.
