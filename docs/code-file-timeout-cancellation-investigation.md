# Code-File Timeout Cancellation Investigation

Status: Investigation

Date: 2026-08-23

## Scope

This documentation-only investigation examines the current lifecycle after
`hac code-file` reports `error: ordinary request timed out`. It records
repository code, existing deterministic tests, installed dependency source, and
limited primary-source context. It selects no solution and changes no RFC-0080
or RFC-0081 contract.

The dated `deepseek-r1:8b` incident is bounded local evidence, not proof of
cause, a model judgment, or a general cancellation result. Generated code was
inspected but never executed.

## Terminology

- **Caller timeout**: the one-shot CLI's HTTPX wait ends and it reports its
  safe timeout error.
- **Server cancellation**: cancellation of HAC's ASGI request task.
- **Transport cancellation**: closure or cancellation of HAC's HTTP request to
  the runtime.
- **Runtime cancellation**: Ollama stops the active generation.
- **Model unloading**: Ollama releases an already-loaded model and resources;
  this is distinct from stopping one generation.

These are separate events. A caller timeout alone does not establish any later
event.

## Observed incident

In the local interoperability observation, `hac code-file` used a 900-second
timeout against HAC running Ollama with thinking disabled. Several invocations
reported `error: ordinary request timed out`; newly created targets stayed empty
and existing targets stayed unchanged. Ollama later consumed CPU, `ollama stop`
remained in `Stopping...`, and HAC shutdown displayed Uvicorn's wait-for-tasks
message before an operator forced a second interrupt. This document does not
attribute that behavior to HAC, Ollama, or the model without further evidence.

## Current request path

**Confirmed from repository code.** `code_file_command.main` validates one
target and request, creates an allowed missing leaf if applicable, then calls
`chat_command._post_native_request` once. That helper uses a fresh synchronous
HTTPX client for `POST http://127.0.0.1:8000/v1/chat` with
`follow_redirects=False`. The FastAPI route constructs `ClusterRequest` and
awaits `handle_chat_cluster_request`, which reaches `orchestrate_request`,
`execute_local_routing_decision`, and `OllamaAdapter.chat`. The adapter opens a
fresh `httpx.AsyncClient` and awaits `POST /api/chat`.

The adapter payload sets `stream: false`. [Ollama's streaming documentation](https://docs.ollama.com/api/streaming)
confirms that this requests one non-streaming JSON response rather than streamed
responses.

## Timeout ownership

**Confirmed from repository code and RFC-0060.** `--timeout-seconds` belongs to
the one-shot caller only. `chat_command._parse_timeout_seconds` accepts an
integer from 1 through 3600; `code-file` reuses it. The selected value becomes
HTTPX's scalar `timeout` on the caller's fresh synchronous client. It covers
HTTPX pool, connect, write, and read operations independently; it is not a
strict total command deadline, server deadline, adapter timeout, runtime
timeout, or cancellation contract.

The local Ollama adapter explicitly constructs its async client with
`timeout=None`; no HAC server-side or Ollama request deadline is configured.
`chat`, `code`, and `code-file` reuse `chat_command._post_native_request`.
`summarize` and the source-grounded `external-information` command define
equivalent helpers of their own, while `classify` configures its client inline;
each applies caller-owned timeout behavior separately. `code-file` additionally
has its bounded target-write stage after a successful response.

## Current cancellation propagation

**Confirmed from repository code.** No HAC route calls
`Request.is_disconnected()`, and the application has no disconnect middleware,
`CancelledError` handler, cancellation shield, background task, `create_task`,
or thread-offloaded work on this request path. The route and orchestrator simply
await down to the adapter. They do not convert cancellation into a cluster error.

**Unresolved.** The repository does not demonstrate what Uvicorn does to this
specific ASGI task when the caller closes its loopback connection. Starlette
1.6.0 provides `Request.is_disconnected()`, but availability is not detection:
HAC never calls it. No current test uses a real disconnecting ASGI client or
observes task cancellation.

**Inference, not a guarantee.** If an ASGI task is cancelled while awaiting the
adapter, ordinary coroutine unwinding reaches the adapter's `async with`
HTTPX-client scope. The repository does not demonstrate whether that closes the
particular Ollama connection soon enough, nor whether a closed connection stops
runtime work.

The current [Uvicorn server-behavior documentation](https://www.uvicorn.org/server-behavior/)
says graceful shutdown waits for connections and tasks to complete. Installed
Uvicorn 0.52.4 source contains the observed `Waiting for background tasks to
complete` message while its server task set is non-empty; it does not identify a
particular request, runtime operation, or generation as the cause. This makes
the message compatible with an in-flight request, but does not explain Ollama
CPU use.

## Runtime transport and Ollama boundary

**Confirmed from repository code.** HAC sends non-streaming `/api/chat` through
a fresh async HTTPX client with no timeout and does not retain the client,
stream partial output, call an Ollama cancellation endpoint, or invoke model
unloading. It catches `httpx.HTTPError` but not cancellation explicitly.

**Confirmed by authoritative external source.** Ollama documents `stream:false`
as a one-response mode. Its public streaming documentation does not define a
client-disconnect cancellation guarantee for a non-streaming chat request. The
current [official Ollama client source](https://github.com/ollama/ollama/blob/main/api/client.go)
uses Go contexts for client requests, but is not the version or configuration
used in the dated observation and does not establish HAC-to-Ollama cancellation
semantics.

**Unresolved.** This investigation cannot confirm that an HAC-side cancellation
closes the Ollama socket, that a closed socket requests generation cancellation,
that Ollama honors such a request, or that `ollama stop` unloads a model before
active generation finishes. The observed CPU use may be runtime behavior, may
reflect a still-running HAC request, or may involve another lifecycle detail not
captured here.

## Deterministic evidence

**Confirmed by existing deterministic tests.**

- `test_chat_command.py` verifies the finite caller client timeout and maps each
  HTTPX timeout category to `error: ordinary request timed out` without exposing
  private details.
- `test_ollama_adapter.py` verifies that `OllamaAdapter.chat` uses `timeout=None`.
- `test_code_file_command.py` verifies that a caller-side `httpx.TimeoutException`
  after missing-leaf creation leaves that leaf empty. It also verifies that
  invalid-envelope and other pre-replacement failures preserve an existing
  target.

**Confirmed from code.** A late server or runtime response cannot cause this
same timed-out `code-file` process to replace a target. The timeout exception
takes the caller directly to `_exit_with_failure`; response parsing and
`_atomic_replace` occur only after `_post_native_request` returns a successful
response. The caller's context-managed HTTPX client is then exited. This does
not claim that the server or runtime stopped; it establishes only that the
timed-out caller does not later process a response into a file replacement.

For an existing target, unchanged content on a caller timeout is an accepted
RFC-0080 guarantee before final replacement, not merely the local observation.
For an absent RFC-0081 target, successful exclusive creation occurs before the
native request and later timeout/failure deliberately does not delete it; an
empty leaf may therefore remain.

## Confirmed guarantees

- One invocation has one caller-owned finite HTTPX wait and no automatic retry.
- A caller timeout is reported as the stable safe error without private HTTPX
  details.
- HAC does not configure a server, adapter, or Ollama deadline from that option.
- A timed-out `code-file` caller does not replace an existing target, and an
  already-created missing leaf may remain empty by accepted RFC-0081 design.
- Generated text is never executed by this caller.

## Non-guarantees

- The timeout does not guarantee server-task cancellation, runtime-transport
  cancellation, Ollama generation cancellation, model unloading, CPU release,
  or prompt/result deletion from an external runtime.
- The timeout is not a total end-to-end execution deadline and does not prove
  work stopped elsewhere.
- HAC provides no late-result discard protocol beyond the caller exiting before
  it can validate and replace the target.
- No cancellation behavior is currently promised consistently across runtime
  adapters, capabilities, remote execution, or server shutdown.

## Unresolved questions

- Does the deployed Uvicorn/ASGI stack cancel this route on an ordinary client
  disconnect, or permit it to continue?
- If cancelled, does HTTPX close the active Ollama connection in the observed
  timing and does the installed Ollama version stop generation on that close?
- Which task produced the observed Uvicorn shutdown wait, and was Ollama CPU
  use the same request?
- What does `ollama stop` guarantee while a generation is active?

These questions cannot be answered by the existing tests or the bounded
interoperability observation.

## Future architectural decision questions

Any decision on a server-side deadline distinct from the caller deadline,
disconnect cancellation, a runtime-adapter cancellation guarantee, capability-
versus-transport cancellation semantics, late-result policy, or graceful
shutdown guarantees would require a future RFC. This investigation selects none.

## Smallest evidence-gathering next step

Add no production behavior. A focused, model-free, disposable local ASGI proof
with an existing delayed fake adapter could observe whether a client disconnect
cancels the route task and whether Uvicorn shutdown waits for it. A separate
version-pinned Ollama investigation would still be needed before claiming
runtime-generation cancellation or resource-release behavior.
