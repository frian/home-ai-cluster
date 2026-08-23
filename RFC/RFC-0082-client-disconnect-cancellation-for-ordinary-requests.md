# RFC-0082: Client-Disconnect Cancellation for Ordinary Requests

Status: Accepted

Date: 2026-08-23

Author: frian

## Summary

Home AI Cluster should treat a confirmed client disconnect as the narrow
cancellation boundary for an in-flight ordinary HTTP request. When the HTTP
edge confirms that its client has disconnected while routable execution is
still pending, HAC should cancel the HAC-owned pending execution task and
discard every later result. Once the covered route owns a terminal HAC result,
normal completion wins even if later response serialization or delivery fails.

This proposal preserves RFC-0060 caller-owned `--timeout-seconds` semantics.
It adds no server execution deadline, request field, cancellation endpoint,
job system, retry, fallback, runtime-specific stop operation, or model-unload
guarantee. Runtime and transport resource release remain best-effort and
adapter-dependent.

The factual basis is the retained [Code-File Timeout Cancellation
Investigation](../docs/code-file-timeout-cancellation-investigation.md). That
investigation establishes the current missing boundary; it does not establish
that ASGI automatically cancels handlers or that a runtime stops generation
when a connection closes.

## Problem

An ordinary caller can stop waiting because of its own HTTP timeout, an
operator interrupt, a closed browser, or transport loss. Current HAC routes
await routing and adapter work directly and do not observe request disconnects.
The investigation records a bounded local observation in which a caller timed
out while later runtime activity and shutdown waiting were observed. It makes
no causal attribution to HAC, Ollama, or a model.

Without an explicit HAC boundary, an abandoned connected-client request may
remain awaited by HAC even though it no longer has a consumer. The project
needs the smallest engine-independent rule for HAC-owned work, without
pretending to control downstream runtime execution.

## Goals

This RFC should:

* make confirmed client disconnect a cancellation boundary for an in-flight
  ordinary request;
* stop HAC from deliberately awaiting or completing an abandoned request;
* propagate ordinary asynchronous cancellation through HAC-owned route,
  orchestration, adapter, and remote-transport coroutines;
* deterministically discard late success and failure results;
* preserve fail-closed routing, privacy, authority, and caller-edge behavior;
* avoid keeping graceful shutdown blocked by work already detected and
  cancelled as abandoned; and
* remain local-first, engine-independent, small, and understandable.

## Non-goals

This RFC does not redefine `--timeout-seconds`. It remains a caller-owned HTTP
timeout, not a strict wall-clock execution deadline, server deadline,
cluster-wide deadline, runtime termination guarantee, or model-unload
guarantee. It adds no request field or wire-level deadline.

This RFC also does not introduce:

* a request ID, `hac cancel` command, cancellation endpoint, durable job,
  task database, queue, dashboard, process supervision, or distributed
  deadline propagation;
* a new capability, runtime-specific kill command, Ollama `stop` operation,
  process kill, or model unloading rule;
* retry, corrective prompting, another candidate selection, response salvage,
  or fallback after ambiguous transmission or cancellation;
* a new public failure category for a client that is no longer connected;
* changes to RFC-0080 or RFC-0081, including their caller-owned file authority
  and failure rules; or
* prompt/result logging, automatic request history, or a request lifecycle
  database.

An independent server execution budget may be considered only by a future RFC
if disconnect cancellation proves insufficient.

## Proposal

### Scope and confirmed disconnect

This rule applies only after accepted input begins existing routable inference
execution at one of these current HAC HTTP route families:

* native chat: `POST /v1/chat`;
* source-grounded chat: `POST /v1/chat/sources`;
* summarize: `POST /v1/summarize`;
* classify: `POST /v1/classify`;
* the internal static-cluster request receiver:
  `POST /internal/cluster/request`; and
* OpenAI-compatible chat: `POST /v1/chat/completions`.

The internal receiver is included so an upstream coordinator disconnect can
cancel pending execution at the receiving HAC node. This does not guarantee
that the receiving node's downstream runtime stops.

These routes share this proposed architectural policy; they do not currently
share one HTTP helper or route implementation. A later implementation must
apply the policy at each covered HTTP boundary or through an implementation
seam proven to cover all six families. Health and status endpoints, model-list
or metadata endpoints, browser assets, non-inference control surfaces, and any
future route not explicitly added by a later decision are excluded.

The rule does not change a covered request's capability, routing, response
schema, caller timeout, or compatibility contract.

A disconnect is **confirmed** only when the HAC ASGI edge observes the
framework-supported disconnect indication for that specific request while its
response is still incomplete. Availability of a framework method alone is not
confirmation, and this RFC does not assume that an ASGI server automatically
cancels a request handler. The implementation must use the ordinary supported
ASGI boundary and test the resulting behavior deterministically.

### Completion-versus-disconnect rule

The normal-completion commitment point is reached when a covered route's
existing routable execution has produced its terminal HAC result—either success
or an existing structured failure—and that result has returned to the covered
HTTP route's ownership. This occurs before response serialization or ASGI
transmission need succeed.

If that terminal result is already available when a confirmed disconnect is
observed, normal completion wins. A later disconnect does not retroactively
cancel or reverse completed HAC execution. HAC may attempt its normal response
path, but response delivery is not guaranteed and no retry is authorized.

If confirmed disconnect is observed while routable execution is still pending,
disconnect wins. HAC must then cancel its HAC-owned pending execution task,
stop awaiting its result, and discard every later success or failure. If
completion and disconnect become observable in the same scheduling opportunity,
HAC must re-check whether the execution task has already reached its terminal
result: completion wins if it has; otherwise disconnect wins.

Exactly one HAC-side terminal outcome wins. The implementation must not send a
second response, restart the request, retry, fall back, or select another
candidate. It must not infer the winner from a late result, adapter exception,
or runtime activity after cancellation.

### HAC-owned cancellation

Each covered HTTP boundary, or a seam proven to cover it, owns the cancellable
task representing one accepted ordinary request's HAC work. After confirmed
disconnect it must propagate ordinary asynchronous cancellation through the
existing awaited route, orchestration, executor, local-adapter, and
declared-remote-transport chain. HAC must stop deliberately awaiting the normal
inference result after disconnect wins; it may await cancellation unwinding and
HAC-owned cleanup required for correctness before relinquishing the abandoned
request.

Here, bounded cleanup means bounded HAC ownership and authority, not a
guaranteed number of seconds. This RFC introduces no cleanup timeout and does
not guarantee finite shutdown if a library, adapter, blocking operation, remote
process, or external runtime fails to cooperate with cancellation.

Cancellation is not an execution failure to be converted into an ordinary
completed result. If cancellation itself exposes an error, HAC must contain it
at the abandoned-request boundary rather than emit a result, retry, fallback,
or expose a new response contract to the disconnected client.

The existing structured-failure contract remains unchanged: it describes the
explicit completed operator request accounts that it already owns. This RFC
adds no disconnected-client failure status. RFC-0035 local history remains
limited to its explicit explain-request command and gains no automatic record
for ordinary HTTP traffic or abandoned requests.

### Routing and authority boundaries

Cancellation must not alter capability admission, selection, local-only
constraints, result attribution, or request privacy. RFC-0028's fallback is
not eligible after cancellation: cancellation is neither a classified
pre-execution unavailability result nor permission for another attempt.

For `code-file`, the target remains wholly caller-owned. The server gains no
filesystem authority. A caller that has timed out cannot later receive and
apply a result; RFC-0080's unchanged-existing-target rule and RFC-0081's
possible empty already-created leaf remain unchanged.

### Local, remote, and runtime boundary

For a local adapter, HAC cancellation reaches the adapter's awaited coroutine.
For a declared remote request, it reaches HAC's awaited remote-transport
coroutine. In both cases HAC must discard any later normalized result.

Coordinator-side cancellation of an outbound remote request is not a
pre-transmission failure and cannot authorize RFC-0028 fallback, another
candidate, or a retry. A remote node may continue processing if it does not
observe or honor its own upstream disconnect; its result is still discarded by
the cancelling coordinator. The covered internal receiver likewise applies this
policy when its upstream coordinator disconnects.

This is a best-effort propagation rule, not a downstream termination promise.
This RFC does not guarantee that cancelling HAC work promptly closes a
particular runtime connection, stops external generation, releases CPU or GPU,
unloads a model, kills a remote process, or has identical transport effects
across engines. Those effects remain adapter- and runtime-dependent unless a
later RFC establishes a stronger engine-independent contract.

### Graceful shutdown

Graceful HAC shutdown remains governed by its server and runtime environment.
Once HAC has confirmed a client disconnect and cancelled its owned request
task, it must not deliberately retain that abandoned request as work that
blocks graceful shutdown. This does not promise that Uvicorn never waits for
tasks, that shutdown is finite when cancellation is not cooperatively handled,
or that shutdown can terminate external runtime work or every connection
outside HAC ownership.

## Rationale

Disconnect is the smallest truthful signal that a request has no connected
consumer. It is narrower than adding a server deadline and more useful than
leaving caller-only timeout behavior with no edge observation. The rule is
engine-independent because it governs HAC's own awaiting and result handling,
not an engine-specific cancellation API.

The proposal preserves the existing simple shape: one request follows existing
routing once; a confirmed abandoned request cancels once; no late result is
published. It adds no persistent lifecycle, operator-control surface, or
runtime command.

## Alternatives considered

### Keep caller-only timeout behavior with no disconnect observation

Rejected. A caller can leave while HAC continues awaiting work without a
consumer. The investigation demonstrates that this is an important unresolved
lifecycle boundary.

### Add a server execution deadline now

Deferred. A connected client may legitimately wait according to its own policy.
A server budget has different semantics and needs a separate RFC.

### Add a wire-level deadline

Rejected. It expands request and compatibility contracts without being needed
to cancel work after a confirmed disconnect.

### Add a cancellation endpoint, job ID, or durable job system

Rejected. These add public lifecycle ownership, persistence, and concurrency
decisions beyond an abandoned HTTP request.

### Issue runtime-specific stop commands or kill/unload processes

Rejected. Such behavior is engine-specific and cannot truthfully promise safe
or uniform downstream effects.

### Retry, fall back, or repair after cancellation

Rejected. Transmission or execution may already have begun. RFC-0028 permits
only its narrow pre-execution fallback, not cancellation-driven attempts.

### Do nothing beyond documentation

Rejected. The investigation is sufficient to define HAC's bounded ownership
rule, while intentionally leaving upstream behavior unresolved.

## Trade-offs

The covered HTTP boundaries gain a small cancellation race and bounded cleanup
obligation.
An external runtime may continue work after HAC stops awaiting it, so this is
not a resource-termination solution. Those costs are acceptable because the
rule makes HAC behavior truthful, prevents deliberate late completion, and
does not add engine-specific infrastructure.

## Impact

If accepted, a later implementation should apply this shared policy at the six
covered HTTP boundaries or a demonstrated common seam, then use the existing
cancellable call chain. It must not refactor unrelated routing, introduce a
new concurrency framework, alter request/result schemas, or broaden runtime
authority.

The first implementation should proceed in small stages:

1. add deterministic delayed-fake tests proving completion-versus-disconnect
   races;
2. add a disconnect watcher at each covered HTTP boundary or a seam proven to
   cover all six route families;
3. propagate cancellation through existing HAC-owned awaited work;
4. add focused local and declared-remote path tests; and
5. document the resulting bounded guarantee.

No real model is required. Required deterministic coverage includes proof that
every covered route family is protected directly or through a proven shared
seam; normal terminal execution completion before disconnect; disconnect before
terminal execution completion; the same-scheduling-opportunity re-check with
completion precedence for an already terminal task; response-delivery failure
after completion without restart or cancellation; discarded late success and
late failure; no retry or fallback; cancellation reaching a fake cancellable
local adapter; a fake internal remote receiver honoring upstream disconnect;
outbound remote cancellation not triggering fallback; unchanged existing
`code-file` targets after caller timeout; an RFC-0081-created empty leaf
remaining after later timeout; shutdown assertions limited to HAC-side behavior
after cooperative cancellation; and no assertion of runtime resource
termination.

## Open questions

The exact supported ASGI disconnect observation mechanism and its test harness
must be established by the later implementation proof. The investigation does
not establish the deployed server's current disconnect timing, whether
cancellation closes a particular runtime socket promptly, or what any runtime
does after transport closure. Those questions do not change the bounded HAC
contract proposed here.

## Decision

Pending.
