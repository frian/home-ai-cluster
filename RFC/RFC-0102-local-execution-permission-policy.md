# RFC-0102: Local Execution Permission Policy

Status: Draft

Date: 2026-09-04

Author: frian

## Summary

For an ordinary originating request, Home AI Cluster should permit a new
caller-local HAC execution only when the RFC-0101 process-local active
execution-interval cardinality is zero. The permission decision and entry to
that interval must be one coherent transition for simultaneous requests.

When the caller-local candidate is otherwise statically eligible but is not
permitted to begin, HAC does not attempt it. It may instead continue to the
next already-known, statically eligible, uncontacted candidate in the existing
deterministic order. If no such candidate may be considered, the request fails
immediately with a distinct HAC-owned execution-permission meaning.

This first policy applies only to the originating process considering its own
local candidate. It does not state runtime capacity, expose remote execution
availability, add receiver-side refusal, or change existing fallback rules.

## Problem

Draft RFC-0098 defines execution availability as distinct from static
eligibility, health, reachability, and fallback safety. Draft RFC-0099 limits
the truth to HAC-owned permission to begin an independent execution, not
runtime capacity. Draft RFC-0100 scopes the first proof to one ordinary
process-local adapter-dispatch boundary, and Draft RFC-0101 represents its
active intervals as one shared process-local cardinality.

Representation alone does not make a second explicitly declared,
same-capability node useful when the originating process is already executing
work locally. The project needs one bounded policy that consumes only the
truth the caller owns, without inventing remote availability or scheduling.

## Goals

This RFC should:

* define one fixed first permission rule for the originating process's local
  candidate;
* preserve static capability eligibility and deterministic candidate order;
* permit pre-attempt consideration of an existing remote candidate when local
  permission denies an execution that has not begun;
* preserve RFC-0028's anti-double-execution fallback boundary; and
* retain truthful routing explanation without specifying its concrete form.

## Non-goals

This RFC does not define:

* runtime capacity, runtime load, queue depth, slots, configurable
  concurrency, or a threshold other than the fixed zero/nonzero rule;
* waiting, queueing, fairness, cancellation while waiting, scheduling, generic
  dynamic routing, balancing, round robin, weights, scores, or random choice;
* remote execution-availability knowledge, polling, cached observations,
  receiver-side refusal, remote protocol additions, or remote state transport;
* exact failure classes, HTTP status codes, CLI wording, JSON fields, routing
  explanation fields, health/status changes, or configuration keys;
* persistence, databases, IPC, cross-process coordination, discovery,
  dynamic membership, or a 2.0 commitment; or
* an implementation, including a lock, semaphore, compare-and-swap,
  reservation, permit token, or separate reserved state.

## Proposal

### Scope and first permission rule

This policy applies only when the process handling an ordinary originating
request considers that process's own local routing candidate. It does not yet
consume interval cardinality when a receiver handles an already-transmitted
`/internal/cluster/request`.

For the scoped process-local RFC-0101 cardinality:

```text
active intervals == 0
    -> a new local HAC execution may begin

active intervals > 0
    -> this new local HAC execution is not permitted
```

This is an HAC-owned policy. It does not claim that the runtime supports only
one request, has capacity one, is busy, is saturated, or cannot execute more
work.

### Coherent permission and interval entry

For simultaneous independent requests, permission and beginning the new
HAC-owned local execution interval must form one coherent semantic transition:

```text
if current active interval cardinality is 0:
    permit this local execution and begin its interval coherently
else:
    do not begin it locally
```

The architecture must not allow two requests independently to observe zero,
both become permitted, and both begin local execution. This is a semantic
atomicity requirement only; it chooses no synchronization primitive and no
intermediate architectural reserved state.

### Static eligibility remains unchanged

A local candidate denied execution permission remains statically eligible.
Declared capabilities, health, and static selection facts do not change. The
denial is neither runtime unavailability nor a failed execution attempt.

The routing distinction is deliberately narrow:

```text
static candidate eligibility and order
        ->
local execution-permission decision for a caller-local candidate
        ->
begin execution or continue candidate consideration
        ->
existing execution and fallback behavior
```

This describes no scheduler, planner, queue, or general dynamic-routing layer.

### Permission-based continuation before an attempt

If the considered caller-local candidate is not permitted, HAC may consider
the next statically eligible, not-yet-contacted candidate in the existing
deterministic order. The skipped local candidate must not enter its adapter
invocation, contact its runtime, count as a failed execution attempt, or
trigger RFC-0028 fallback.

In the ordinary current topology, local retains first consideration. A denied
local execution may therefore lead to declared remote candidates in their
existing declaration order. No new selection or balancing algorithm is
introduced.

This continuation is not fallback. No execution or transport attempt occurred
at the skipped candidate, so no duplicate-execution risk has begun. Once HAC
attempts a subsequently selected remote candidate, RFC-0028 remains unchanged:
only affirmative pre-transmission connection unavailability may authorize its
existing fallback; post-transmission or ambiguous outcomes do not authorize
speculative execution elsewhere.

### No alternative means immediate distinct failure

If local execution is not permitted and no other candidate may be considered
under existing static constraints, HAC fails immediately. This includes a
`local_only` request, no statically eligible remote candidate, and static
policy that excludes remotes.

The failure has a distinct cluster-owned execution-permission meaning. It is
not no static candidate, invalid request, runtime adapter unavailable,
pre-transmission connection unavailable, or ambiguous remote transport
failure. Concrete exception, HTTP, CLI, JSON, and protocol representations are
intentionally deferred.

There is no waiting, retry delay, queue position, automatic retry, or fairness
behavior in this first policy.

### Remote availability remains opaque

After a denied caller-local execution, HAC considers remote candidates solely
from existing static eligibility and order. The caller does not inspect,
infer, or guess remote execution availability from status, runtime health,
request history, cached observations, or background polling.

When a request has been transmitted, the receiver continues existing local
execution behavior. Its RFC-0101 cardinality remains descriptive for received
internal requests in this first proof. There is no receiver-side refusal, new
remote response, or caller retry based on receiver cardinality.

### Explainability and determinism

A future implementation must preserve the conceptual distinction between a
statically eligible local candidate and HAC declining to permit its new local
execution at the current process-local state. It must not report that candidate
as statically ineligible.

The policy remains deterministic and explainable given the same static
candidate order, request constraints, and process-local active-interval state
at the decision boundary. Identical requests at different times need not
select the same node, because that local state intentionally changes over time.

## Example

```text
Node A: caller-local, declares code
Node B: explicit remote, declares code

Request 1: A cardinality is 0
    -> local permission is granted; A begins execution; A cardinality becomes 1

Request 2 arrives while Request 1 remains active
    -> A remains statically eligible
    -> local permission denies Request 2 at A
    -> A is not contacted for Request 2
    -> B is the next statically eligible candidate and may be attempted under
       existing remote execution rules
```

The example does not prove B is idle, has spare runtime capacity, or can accept
multiple requests. If B is affirmatively connection-unavailable before
transmission, existing fallback rules apply; receipt or an ambiguous outcome
does not authorize speculative execution elsewhere.

For a `local_only` request with a statically eligible local candidate and a
nonzero local cardinality, the result is immediate distinct HAC
execution-permission failure. No remote candidate is considered and no waiting
is introduced.

## Relationship to Draft RFC-0098 through RFC-0101

This RFC consumes Draft RFC-0098's execution-availability semantics, Draft
RFC-0099's HAC authority boundary, Draft RFC-0100's first process-local scope,
and Draft RFC-0101's active execution-interval cardinality.

It cannot become Accepted before all four prerequisites are accepted. If any
prerequisite materially changes, this RFC must be reviewed again. Draft PR
#654 may demonstrate that RFC-0101's representation is implementable, but it
is evidence only and is not an architectural prerequisite.

## Relationship to RFC-0028 fallback

RFC-0028 remains accepted without change. Permission-based continuation past a
local candidate that never began execution is not fallback. For a later
attempted remote candidate, its existing narrow pre-transmission
connection-unavailable rule remains the only accepted path that can advance;
post-transmission and ambiguous outcomes remain terminal for that logical
request.

## Alternatives considered

### Observation only

Rejected as the first useful policy because it proves state but does not let an
existing second same-capability node receive independent work while the
originating local process is executing. Observation remains valuable evidence.

### Allow unlimited local overlap

Rejected for the first policy because it leaves execution availability
informational only and does not prove bounded independent work sharing. It does
not claim runtime concurrency is unsafe.

### Wait locally

Rejected because waiting introduces queueing, timeout, fairness, ordering, and
cancellation semantics unnecessary for this first proof.

### Fail locally without considering another candidate

Rejected when a static eligible alternative exists, because the bounded goal is
to share independent work across existing explicit nodes. With `local_only` or
no alternative, immediate failure remains the decision.

### Treat denial as fallback or static ineligibility

Rejected because no execution/transport attempt occurred and declared
capability eligibility remains true. RFC-0028 has a narrower accepted meaning.

### Treat nonzero cardinality as runtime capacity exhaustion

Rejected because RFC-0099 prohibits turning HAC-owned process-local truth into
a runtime-capacity claim.

### Apply refusal at remote receivers now

Rejected for this first proof because receiver state becomes known only after
transmission and current protocol/failure semantics cannot express a distinct
refusal without new architecture.

### Caller-aware remote availability

Deferred. It needs separate authority, freshness, and protocol architecture
and is not needed for this local policy proof.

## Trade-offs

The first rule intentionally allows at most one originating-process local
HAC-owned adapter invocation at a time. This HAC policy may shift an
independent request to an explicit remote candidate, but cannot avoid a busy
remote receiver because the caller owns no truthful pre-transmission remote
availability fact. The asymmetry is intentional.

A request without an allowed alternative fails immediately rather than waits.
Node choice becomes request-time-state-sensitive, but remains explainable from
explicit local state and fixed static rules.

## Impact

This RFC changes no implementation. If accepted, a later implementation may
coherently consume local cardinality for permission and interval entry, continue
candidate consideration after denial, emit a distinct permission failure when
none remains, and explain the decision truthfully. That implementation still
requires its own review.

## Open questions

* What concrete normalized failure type should represent permission denial?
* How should public HTTP and CLI surfaces map that failure?
* How should actual-request routing explanation represent eligibility and
  permission denial?
* What implementation structure should combine permission and interval entry
  coherently?
* What deterministic concurrency tests prove that two simultaneous originating
  requests cannot both enter local execution from zero?
* What real two-node proof should demonstrate local-A to remote-B sharing?
* When should receiver-side execution permission be considered?
* What architecture would establish truthful caller-aware remote availability?
* When, if ever, should the fixed rule become configurable or finer-grained?

## Decision

Pending.
