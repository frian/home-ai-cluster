# RFC-0104: Remote Pre-Execution Permission Refusal

Status: Draft

Date: 2026-09-04

Author: frian

## Summary

Home AI Cluster should extend the fixed HAC execution-permission policy from
Accepted RFC-0102 to ordinary receiver-side `/internal/cluster/request`
handling, before the receiver begins adapter invocation.

When a receiver has no permission to begin a new HAC-owned execution, it must
refuse that specific request before adapter invocation and return the exact
internal response:

```text
HTTP 409 Conflict
```

```json
{
  "detail": "execution-permission-denied"
}
```

A caller may continue to the next statically eligible, not-yet-contacted remote
candidate in the existing deterministic order only after validating both the
HTTP `409` category and that exact machine-readable semantic. This is a new,
narrow safe-continuation condition because the receiver affirmatively states
that HAC-owned adapter execution did not begin for this request.

This condition remains distinct from Accepted RFC-0028's safe continuation
after affirmative connection unavailability before request transmission. A
bare `409`, malformed response, timeout, generic transport failure, `503`, or
any other ambiguous post-transmission outcome remains terminal and must not
authorize speculative duplicate execution.

If all remaining outcomes are execution-permission denials and no later
candidate produces a different authoritative failure, the terminal cluster
semantic is Accepted RFC-0103's `execution-permission-denied`. A later
runtime/transport failure remains authoritative. Existing RFC-0028 exhaustion
semantics also remain authoritative when a candidate sequence contains its
affirmative pre-transmission connection-unavailability condition and no later
failure supersedes it.

This RFC adds no pre-transmission remote-availability observation, polling,
cache, shared state, runtime-capacity claim, scheduler, queue, load balancing,
or multi-candidate actual-request explanation.

## Problem

The current static cluster composition already provides ordered,
operator-declared remote candidates. A caller can send a request to the first
eligible remote, but it cannot truthfully know in advance whether that receiver
will allow a new HAC-owned adapter execution to begin.

Static declaration, health, status, preflight, request history, and previous
responses are not current execution-permission facts for a future request. Any
such observation can become stale before the receiver reaches its local
execution boundary.

Accepted RFC-0098 distinguishes execution availability from static eligibility,
health, reachability, and fallback safety. Accepted RFC-0099 bounds the truth to
HAC-owned permission rather than runtime capacity. Accepted RFC-0100 and
Accepted RFC-0101 define the first process-local execution boundary and active
interval representation. Accepted RFC-0102 applies the first zero/nonzero
permission rule to originating-process local candidates. Accepted RFC-0103
provides the terminal `execution-permission-denied` semantic and native failure
mapping.

After a caller transmits a request to a remote receiver, generic failure is not
safe evidence for trying another remote because execution may already have
begun. The receiver can, however, make one narrow affirmative statement at the
exact boundary it owns: it received this request and refused permission before
adapter invocation.

The project needs to decide whether that affirmative refusal is sufficient to
continue deterministically to an already-known remote candidate without
weakening the anti-double-execution boundary.

## Goals

This RFC should:

* apply the existing fixed HAC execution-permission rule to an ordinary received
  `/internal/cluster/request` before receiver-local adapter invocation;
* require permission and interval entry to be one coherent transition;
* require refusal before adapter or runtime contact;
* define one exact machine-readable receiver refusal contract;
* allow continuation only after that exact refusal is validated;
* preserve existing static candidate order and at-most-once contact per
  candidate;
* keep this continuation distinct from RFC-0028 pre-transmission connection
  unavailability;
* preserve terminal treatment of ambiguous post-transmission outcomes;
* preserve later authoritative runtime or transport failures;
* reuse Accepted RFC-0103's terminal semantic only for permission-refusal
  exhaustion; and
* preserve current bounded observability contracts without introducing a
  multi-candidate explanation timeline.

## Non-goals

This RFC does not define:

* pre-transmission remote execution availability;
* status-based routing, cached observations, freshness windows, polling,
  heartbeat, receiver push, or subscriptions;
* runtime capacity, runtime busy state, model saturation, queue depth,
  available slots, runtime metrics, machine utilization, or cardinality
  exposure;
* waiting, queueing, fairness, reservation, lease, permit tokens, scheduling,
  balancing, round robin, weights, scores, or random choice;
* discovery, registration, dynamic membership, persistence, shared mutable
  cluster state, central coordination, or background workers;
* generic HTTP retry or generic retry middleware;
* a new public HTTP failure taxonomy beyond the already accepted terminal
  `execution-permission-denied` semantic;
* reselection, fallback attribution, or multi-candidate timelines in the
  RFC-0032/RFC-0034 actual-request explanation surface;
* an exact Python exception type, concrete synchronization primitive, or
  implementation placement; or
* configuration, health/status additions, runtime-specific behavior, or a 2.0
  product commitment.

## Proposal

### Receiver-side permission boundary

For an incoming ordinary `/internal/cluster/request`, the receiver applies the
same fixed HAC-owned execution-permission rule before local adapter invocation:

```text
active HAC execution intervals == 0
    -> grant receiver execution permission

active HAC execution intervals > 0
    -> deny receiver execution permission
```

This is HAC policy. It does not state that the runtime is busy, saturated, out
of capacity, or unable to execute more work.

On grant, the permission decision and entry into the receiver-local HAC
execution interval must be coherent. Two simultaneous received requests must
not both observe zero and begin execution.

This RFC intentionally does not prescribe a lock, semaphore, reservation, or
other synchronization primitive. Synchronization must not span adapter
execution, and the rule creates no queue or permit lifecycle.

### Receiver refusal contract

If receiver execution permission is denied, the receiver must not invoke the
adapter, contact the runtime, or begin a receiver-local HAC execution interval
for that request.

It returns exactly:

```text
HTTP 409 Conflict
```

with:

```json
{
  "detail": "execution-permission-denied"
}
```

The response means only:

> The receiver received this request and did not begin its HAC-owned adapter
> execution because HAC execution permission was denied.

It does not mean runtime unavailable, runtime busy, capacity exhausted,
transport failure, or a generic HTTP conflict.

The response must not expose interval cardinality, active request identity,
runtime/model details, queue depth, load information, or machine utilization.

### Exact validation is required

The caller classifies a response as a remote pre-execution permission refusal
only when both are true:

1. the response status is HTTP `409 Conflict`; and
2. the JSON `detail` value is exactly `execution-permission-denied`.

HTTP status alone is insufficient. A bare `409`, malformed JSON, missing or
different `detail`, generic error response, or otherwise invalid response is
not safe continuation evidence.

This uses the existing internal FastAPI-style `detail` convention for one
bounded semantic. It does not establish a generic internal error-envelope
architecture.

### Deterministic candidate continuation

The caller does not pre-screen a receiver. It contacts the first eligible
remote according to the existing static order.

After a validated pre-execution permission refusal, the caller may consider the
next statically eligible, not-yet-contacted declared remote candidate in that
same order.

For example:

```text
Caller C -> Remote A
A receives request
A denies permission before adapter invocation
A returns exact 409 + execution-permission-denied
C validates the refusal
C considers Remote B next
```

The caller must not:

* retry A;
* reorder candidates;
* rediscover candidates;
* score or balance candidates;
* contact candidates in parallel; or
* infer future availability for A or B.

Each receiver decides only from its own HAC-owned process-local permission
state when the request reaches its execution boundary.

### Distinction from RFC-0028

Accepted RFC-0028 permits narrow continuation when HAC has affirmative evidence
that the selected candidate was unavailable before request transmission could
begin.

This RFC defines a separate safe continuation fact:

```text
request transmission occurred
receiver received the request
receiver affirmatively refused before adapter invocation
adapter execution did not begin for that request
```

The refusal must not be represented as
`RuntimeConnectionUnavailableBeforeRequestError` or folded into RFC-0028.

Both rules protect the same anti-double-execution invariant from different
sides of the transmission boundary: continuation is permitted only when HAC has
affirmative evidence that useful execution did not begin at the skipped
candidate.

### Ambiguous post-transmission outcomes remain terminal

Once transmission may have occurred, continuation is authorized only by the
exact validated refusal defined here.

The following remain terminal and must not cause another candidate attempt:

* timeout;
* connection loss after transmission may have begun;
* generic `RemoteTransportError`;
* runtime or adapter failure;
* invalid result;
* HTTP `500`;
* generic HTTP `503`;
* bare or unrecognized `409`;
* malformed refusal payload; or
* any other outcome that does not affirmatively establish that adapter
  execution did not begin.

This preserves the conservative anti-double-execution boundary.

### Terminal outcome and failure authority

If candidate exhaustion is attributable only to caller-local execution
permission denial, if any, and/or validated remote pre-execution permission
refusals, the terminal outcome is:

```text
execution-permission-denied
```

The existing Accepted RFC-0103 native mappings remain authoritative:

```text
native HTTP -> 409 Conflict
native CLI  -> exit 1
```

No second public terminal semantic is introduced.

A permission refusal never masks a later authoritative failure. For example:

```text
Remote A -> validated execution-permission-denied refusal
Remote B -> authoritative runtime or transport failure

final outcome -> Remote B failure
```

Likewise, this RFC does not rewrite RFC-0028 exhaustion semantics. If the
candidate sequence contains affirmative RFC-0028 pre-transmission connection
unavailability and no later authoritative execution or transport failure
supersedes it, that existing exhaustion outcome remains authoritative rather
than being rewritten as `execution-permission-denied`.

For example:

```text
Remote A -> connection unavailable before transmission
Remote B -> validated execution-permission-denied refusal
no candidate remains

final outcome -> existing RFC-0028 exhaustion outcome
```

This ordering rule prevents a later permission refusal from masking an earlier
accepted connection-unavailability exhaustion cause while still allowing safe
candidate continuation during the sequence.

### Actual-request explanation remains bounded

Accepted RFC-0032 and RFC-0034 remain authoritative for the explicit
`home-ai-cluster-explain-request` surface: one automatic selection, local-only
execution, and at most one selected-candidate execution attempt.

This RFC does not extend that surface to record the complete sequence
`A refused -> B considered -> B executed/refused`.

Ordinary cluster routing must preserve the semantic distinction internally: a
remote that returned the exact refusal was statically eligible, was contacted,
and affirmatively did not begin adapter execution. It must not be treated as
statically ineligible, runtime unavailable, or an RFC-0028 connection failure.

If the project later wants operator-visible multi-candidate request timelines,
reselection, or fallback attribution, that requires a separate RFC.

### Interval limitation remains unchanged

Accepted RFC-0100 and RFC-0101 remain authoritative for HAC execution interval
lifetime. An interval ends when HAC no longer awaits adapter invocation; this
does not prove that downstream runtime work has stopped.

Receiver execution permission therefore uses only HAC-owned interval state. It
must not consult CPU load, runtime queues, runtime worker state, model state, or
other runtime-specific facts to compensate for that bounded truth.

## Example

```text
rasp = caller

debian-1 = first declared remote for code
sat      = second declared remote for code
```

Assume `debian-1` already has one active HAC-owned execution interval. A new
independent `code` request arrives at `rasp`:

```text
rasp static order: debian-1 -> sat

rasp sends to debian-1
debian-1 receives the request
debian-1 denies permission before adapter invocation
debian-1 returns exact 409 + execution-permission-denied

rasp validates the refusal
rasp considers sat
rasp sends to sat
sat decides from its own receiver-local HAC permission state
```

If `sat` also refuses before execution and no candidate remains, the terminal
outcome is `execution-permission-denied`, unless an earlier RFC-0028
connection-unavailability outcome remains authoritative under the rule above.
If `sat` begins execution and later fails ambiguously, that later failure is
terminal and no further candidate is attempted.

## Relationship to existing RFCs

Accepted RFC-0098 defines execution-availability semantics. Accepted RFC-0099
defines HAC's authority boundary. Accepted RFC-0100 defines the first bounded
process-local execution scope. Accepted RFC-0101 defines active HAC execution
interval cardinality. Accepted RFC-0102 defines the first local execution
permission policy. Accepted RFC-0103 defines the terminal
`execution-permission-denied` semantic and native mappings.

This RFC extends that policy only to the receiver-local pre-adapter boundary and
defines the exact affirmative refusal needed for safe remote continuation.

Accepted RFC-0028 remains unchanged and separate. Accepted RFC-0032 and
RFC-0034 remain unchanged in their bounded actual-request explanation scope.
RFC-0041 status remains a read-only operator observation and must not become
routing or permission truth.

If any prerequisite is later superseded or materially changed, this RFC must be
reviewed again.

## Alternatives considered

### Pre-transmission status or availability observation

Rejected for this proof. Such observations can become stale before the receiver
evaluates permission and cannot guarantee permission for this request.

### Polling, receiver push, or heartbeat

Rejected. These add background network behavior, freshness, reconnection, and
state-management semantics without being necessary for the bounded proof.

### Runtime load or capacity

Rejected. HAC does not own runtime-capacity truth, and runtime-specific load or
queue APIs would violate engine independence.

### Reservation, lease, or central coordinator

Deferred as substantially larger distributed architecture with expiry,
cancellation, shared-state, and scheduler-like lifecycle semantics.

### Generic retry after HTTP 409

Rejected. HTTP status alone does not prove adapter execution did not begin.

### Generic retry after any receiver error

Rejected. It would violate the anti-double-execution boundary whenever useful
execution may already have begun.

### Extend actual-request explanation now

Rejected. The existing RFC-0032/RFC-0034 operator surface is intentionally
select-once and execute-at-most-one. Remote continuation does not require
changing that observability architecture in the same RFC.

### Receiver pre-execution permission refusal

Proposed. The receiver owns the relevant HAC permission truth at the exact local
execution boundary and can affirmatively refuse before adapter invocation
without distributing mutable availability state.

## Trade-offs

Remote work sharing requires one request/response round trip to an earlier
remote candidate before the caller can consider the next candidate. That is
accepted because it avoids remote state distribution and freshness machinery.

The receiver owns the truth at the execution boundary. Safe continuation
therefore depends on a narrow affirmative response rather than generic HTTP
errors.

The approach remains deterministic and comprehensible, but it intentionally
does not optimize for minimum latency, fairness, utilization, or throughput.

## Impact

This Draft RFC changes no implementation by itself.

If accepted, it authorizes one bounded implementation that:

* applies HAC execution permission to receiver-side internal requests before
  adapter invocation;
* returns the exact internal `409` + `execution-permission-denied` refusal;
* validates that exact refusal at the caller;
* continues only to the next existing static remote candidate after validated
  refusal;
* preserves terminal ambiguous outcomes and later authoritative failures;
* reuses Accepted RFC-0103's terminal semantic for pure permission-refusal
  exhaustion; and
* preserves RFC-0028 and RFC-0032/RFC-0034 boundaries.

It does not authorize polling, caches, remote availability state, runtime
capacity semantics, scheduling, queueing, balancing, configuration, or
multi-candidate explanation.

## Open questions

* What exact internal Python type should represent validated remote refusal?
* Where should receiver permission gating live in existing orchestration?
* What minimal transport parsing should distinguish the exact refusal from a
  bare or malformed `409`?
* What deterministic tests should prove refusal occurs before adapter
  invocation?
* What tests should prove refusal followed by remote execution, malformed `409`
  terminality, pure-refusal exhaustion, and preservation of later authoritative
  failure?
* What real three-node proof is sufficient after implementation?

## Decision

Pending.
