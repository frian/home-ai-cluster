# RFC-0104: Remote Pre-Execution Permission Refusal

Status: Draft

Date: 2026-09-04

Author: frian

## Summary

Home AI Cluster should extend the first fixed HAC execution-permission policy
from Draft RFC-0102 to an ordinary receiver-side
`/internal/cluster/request` before that receiver begins adapter invocation.

When an incoming request reaches Remote A and A has one or more active
HAC-owned execution intervals, A must refuse that specific request before
adapter invocation. The refusal is a normal internal HTTP `409 Conflict`
response carrying the machine-readable cluster-owned semantic:

```text
execution-permission-denied
```

Caller C may consider the next already eligible, not-yet-contacted declared
remote candidate only after it validates both the expected internal HTTP
category and that exact internal semantic. This is a new safe continuation
category. It is distinct from RFC-0028's affirmative connection unavailability
before request transmission. A bare `409`, malformed response, timeout,
generic transport error, `503`, or any other ambiguous post-transmission
outcome remains terminal and must not cause speculative duplicate execution.

When every otherwise usable location considered under this permission policy
refuses before execution and no later attempted candidate produces an
authoritative terminal failure, the terminal cluster outcome reuses Draft
RFC-0103's `execution-permission-denied` semantic. This RFC adds no
pre-transmission availability observation, runtime-capacity claim, scheduler,
or implementation.

## Problem

The existing static composition already provides ordered, operator-declared
remote candidates. A caller can send a request to the first eligible remote,
but it cannot truthfully know in advance whether that remote will allow a new
HAC-owned adapter execution to begin. Static declaration, health, status,
preflight, request history, and a previous response are not an execution
permission fact for a later request; any such observation can become stale
before transmission or execution.

At the exact receiver-local boundary where adapter invocation would begin,
the receiver alone owns the relevant process-local HAC execution state. Draft
RFC-0100 and Draft RFC-0101 define the bounded process-local interval scope
and cardinality; Draft RFC-0102 deliberately applies its first zero/nonzero
permission rule only to originating-process local candidates. Current
receiver-side internal requests intentionally bypass that first policy.

After C sends to A, generic failure is unsafe as a reason to try B: HAC cannot
know whether A began execution. Yet A can make one narrow affirmative statement
when it receives a request and denies permission before it invokes the adapter.
That statement permits useful, deterministic remote work sharing without
distributing mutable availability state.

## Goals

This RFC should:

* apply the existing first HAC permission rule to an ordinary received
  `/internal/cluster/request` before receiver-local adapter invocation;
* require a coherent permission-and-interval-entry transition so simultaneous
  receiver requests cannot both observe zero and begin execution;
* require denial before adapter or runtime contact and a minimal explicit
  receiver response for that specific request;
* define validated `execution-permission-denied` as the only new
  post-transmission continuation condition;
* retain existing static candidate order and permit consideration only of the
  next not-yet-contacted candidate;
* keep RFC-0028's pre-transmission connection-unavailability continuation
  separate and unchanged;
* preserve terminal treatment of every ambiguous or generic post-transmission
  outcome;
* reuse Draft RFC-0103's terminal semantic for permission-refusal exhaustion;
* preserve later authoritative terminal failures; and
* require truthful, privacy-safe actual-request explanation without defining an
  explanation schema.

## Non-goals

This RFC does not define:

* pre-transmission remote availability, status-based routing, cached
  observations, freshness windows, polling, heartbeat, receiver push, or
  subscriptions;
* runtime capacity, runtime busy state, model saturation, queue depth,
  available slots, runtime metrics, or cardinality exposure;
* waiting, queueing, fairness, configurable concurrency, reservation, lease,
  permit-token lifecycle, synchronization primitive, scheduler, balancing,
  round robin, weights, randomization, or least-loaded routing;
* discovery, registration, dynamic membership, persistence, shared state,
  central coordination, or operator status fields;
* generic HTTP retry, generic retry middleware, an exact Python type, exact
  internal response field name, or implementation placement; or
* source code, tests, remote-protocol implementation, configuration, runtime
  behavior, user-facing documentation, or a 2.0 feature commitment.

## Proposal

### Receiver-side permission boundary

For an incoming ordinary `/internal/cluster/request`, the receiving HAC process
must apply the same first fixed HAC-owned execution-permission rule before its
local adapter invocation:

```text
active HAC execution intervals == 0
    -> grant receiver execution permission

active HAC execution intervals > 0
    -> deny receiver execution permission
```

This is HAC policy, not a claim about runtime capacity, runtime busy state,
model saturation, queue depth, or available slots. The receiver must not query
the runtime to decide it.

On grant, the test and beginning of the receiver-local HAC interval must form
one coherent transition, semantically equivalent to:

```text
if active interval cardinality == 0:
    permit this request and begin its HAC interval coherently
else:
    refuse before adapter invocation
```

Two concurrent received requests must not both observe zero and begin adapter
execution. This RFC intentionally does not prescribe a lock, semaphore,
reservation, or other synchronization primitive. Synchronization must not be
held across adapter execution, and this rule creates no queue or permit
lifecycle.

### Receiver refusal

If receiver execution permission is denied, the receiver must not invoke its
adapter, contact its runtime, or begin a receiver-local HAC execution interval
for that request. It must return a normal application response that
affirmatively means:

> The receiver received this request and did not begin its HAC-owned adapter
> execution because execution permission was denied.

The response maps the semantic `execution-permission-denied` to internal HTTP
`409 Conflict`, consistent with Draft RFC-0103. It does not mean runtime
unavailable, runtime busy, capacity exhausted, transport failure, or a general
HTTP conflict.

The response must disclose only the semantic required for routing safety. It
must not disclose active request identity, interval cardinality, prompt or
response contents beyond the request already sent, runtime/model details,
machine utilization, queue depth, or load information.

### Validated internal refusal contract

Caller C may classify a received response as a remote pre-execution permission
refusal only when both of these facts are established under the internal
protocol contract:

1. the response has the expected internal HTTP `409 Conflict` category; and
2. it validly carries the exact machine-readable
   `execution-permission-denied` semantic.

HTTP status alone is insufficient. In particular, a bare or unrecognized
`409` is terminal and ambiguous, as are malformed responses and responses with
an absent or unrecognized semantic.

The current internal request protocol returns one of the successful result
envelopes and current remote transport normalizes HTTP failures without an
established uniquely authoritative failure-semantic envelope or field. This
RFC therefore requires a machine-readable internal representation but does not
invent an exact envelope or field placement. A later implementation RFC or
implementation review must select the smallest protocol-consistent encoding and
validate it before permitting continuation.

### Candidate continuation

The caller continues to use existing deterministic static candidate order. If
A is the first statically eligible remote candidate, C sends the request to A;
it does not pre-screen A. After a validated remote pre-execution permission
refusal, C may consider only the next statically eligible, not-yet-contacted
remote candidate in that existing order. It does not re-order, rediscover,
score, balance, randomize, or retry A.

For example:

```text
C -> A
A receives request
A denies execution permission before adapter invocation
A returns valid HTTP 409 + execution-permission-denied
C -> considers B next
```

The receiver's affirmative statement makes this safe: A has established that
adapter execution did not begin for this request. It does not establish that A
was busy before C sent, that A lacks runtime capacity, or that B is available
before C contacts B.

### Distinct continuation boundaries

RFC-0028 remains unchanged:

```text
affirmative connection unavailability before request transmission
```

This RFC separately defines:

```text
request transmitted and received
-> receiver denied HAC execution permission
-> adapter invocation affirmatively did not begin
```

The latter must not be represented as
`RuntimeConnectionUnavailableBeforeRequestError` or generalized into an
existing fallback exception. Neither condition permits generic retry after an
ambiguous execution outcome.

After transmission, C may continue only for the validated refusal defined here.
Timeouts, connection loss after transmission may have begun, generic
`RemoteTransportError`, invalid result, HTTP `500`, generic HTTP `503` or
runtime unavailability, bare/unrecognized `409`, and every response that does
not affirmatively establish this semantic remain terminal. They must not cause
another candidate attempt.

### Terminal outcome and failure authority

When all otherwise usable execution locations considered under this policy deny
permission before execution and no later attempted candidate produces a
different authoritative terminal failure, the final request outcome is the
existing cluster-owned semantic:

```text
execution-permission-denied
```

This extends Draft RFC-0103's local no-alternative case to exhaustion caused by
validated remote pre-execution permission refusals. The native terminal mapping
remains HTTP `409`, CLI exit `1`, and structured failure status
`execution-permission-denied` where the existing native surfaces apply. It does
not expose cardinality or create a second public terminal semantic.

An earlier refusal must not mask a later authoritative failure. For example,
if A validly refuses permission and B then produces an existing remote
transport or runtime terminal failure, B's failure remains final. Likewise,
this RFC does not alter RFC-0028 exhaustion behavior merely because an earlier
candidate refused permission.

### Explainability and interval limitation

Future actual-request explanation must be able to preserve that A was
statically eligible, was contacted, affirmatively refused before adapter
execution, and was followed by consideration of B; B may then execute or also
refuse. A must not be relabeled statically ineligible or runtime unavailable.
This RFC defines no fields or presentation shape because current accepted
explanation architecture does not uniquely dictate them.

Draft RFC-0100 and Draft RFC-0101 remain authoritative for interval lifetime.
An HAC interval ends when HAC no longer awaits adapter invocation; it does not
prove that the underlying runtime stopped. A prior two-node proof observed an
HAC timeout end an interval while Ollama continued consuming CPU. Receiver
permission uses only HAC-owned state at this boundary and must not consult
runtime work, CPU, load, or capacity to compensate.

## Three-node example

```text
rasp = Caller C

debian-1 = Remote A
  capability: code

sat = Remote B
  capability: code
```

Assume `debian-1` already has one active HAC-owned execution interval. A new
independent `code` request arrives at `rasp`:

```text
rasp static order: A -> B

rasp sends request to A
A receives request
A active interval cardinality > 0
A denies receiver execution permission
A does not invoke adapter
A returns valid machine-readable execution-permission-denied HTTP 409

rasp validates the affirmative refusal
rasp considers B
rasp sends request to B
B decides only from its own receiver-local HAC permission state
```

If B also denies before execution and no candidate remains, the final outcome
is `execution-permission-denied`. If B begins execution or produces an
ambiguous/terminal failure, existing post-attempt semantics remain
authoritative.

## Relationship to existing RFCs

Draft RFC-0102 intentionally limited its first permission policy to
originating-process local candidates. This RFC is a later receiver-side
extension; it does not rewrite RFC-0102 or imply that RFC-0102 already covered
receivers.

Draft RFC-0103 defines the cluster-owned terminal semantic and native mappings
for first local no-alternative denial. This RFC reuses that semantic for
exhaustion attributable solely to explicit receiver pre-execution refusals and
requires an internal machine-readable form for safe caller interpretation. It
does not modify RFC-0103.

Draft RFC-0098 through Draft RFC-0101 remain prerequisites: they distinguish
availability from static eligibility and runtime capacity, define HAC authority,
bound the first proof to process-local state, and define active interval
cardinality. This RFC cannot become Accepted before those Draft RFCs and Draft
RFC-0102 and Draft RFC-0103 are accepted; material prerequisite changes require
review of this RFC.

RFC-0032 remains authoritative for actual-request routing explanation, and
RFC-0034 remains authoritative for structured actual-request failures. RFC-0041
status remains a read-only operator observation and must not become routing or
permission truth.

## Alternatives considered

### Pre-transmission status, availability observation, or cache

Rejected for this first remote proof. Such observations can become stale before
the receiver evaluates permission, while cached observations add freshness and
invalidation semantics without guaranteeing permission for this request.

### Periodic polling, receiver push, or heartbeat

Rejected and deferred. These add background network behavior, lifecycle,
reconnection, and lost-update state while still not guaranteeing permission at
the execution boundary.

### Runtime load or capacity

Rejected. HAC does not own runtime capacity truth, and runtime-specific load,
queue, or concurrency endpoints would violate engine independence.

### Reservation, claim, lease, or central coordinator

Deferred or rejected as a much larger distributed architecture. These require
expiry, cancellation, shared state, and scheduler-like lifecycle semantics not
needed for the first proof.

### Generic retry after HTTP 409

Rejected. HTTP status alone cannot prove that adapter invocation did not begin.

### Receiver pre-execution permission refusal

Accepted for this bounded proof. The receiver owns the decision at the exact
local execution boundary and can affirmatively refuse before adapter invocation
without distributing mutable state.

## Trade-offs

Remote work sharing requires one attempted request and response round trip to
an earlier remote candidate before another can be considered. That cost avoids
remote state distribution and freshness machinery. The receiver owns truth at
the execution boundary; safe continuation depends on its explicit affirmative
contract rather than generic HTTP errors.

Receiver-side overlap becomes bounded by the same first HAC permission policy,
but runtime capacity remains unknown. Candidate order remains static and
deterministic, and no background network activity is introduced.

## Impact

This Draft RFC changes no implementation.

If accepted, later implementation may coherently apply execution permission to
receiver-side internal requests, return a validated machine-readable
`execution-permission-denied` refusal before adapter invocation, map that
refusal to internal HTTP `409`, continue to the next static candidate only for
that refusal, reuse terminal `execution-permission-denied` for relevant
exhaustion, and minimally extend explanation. It must not introduce polling,
status routing, cache, scheduling, runtime capacity semantics, or speculative
fallback.

## Open questions

* What exact internal response envelope or field carries the semantic?
* What exact internal Python type represents affirmative refusal?
* Where does receiver permission gating belong in existing orchestration?
* What minimal transport parsing distinguishes valid refusal from bare `409`?
* What deterministic tests prove denial occurs before adapter invocation?
* What tests prove A refusal then B execution without duplicate execution,
  bare/invalid `409` terminality, and all-refusal terminal semantics?
* What minimal explanation extension is sufficient?
* What real `rasp`, `debian-1`, and `sat` three-node proof is appropriate?

## Decision

Pending.
