# RFC-0101: Process-Local Execution Interval Representation

Status: Draft

Date: 2026-09-04

Author: frian

## Summary

The first shared representation for the bounded execution-availability proof
defined by Draft RFC-0100 should be one non-negative, process-local quantity.
It represents the number of active HAC-owned execution intervals in one
ordinary composed HAC application process.

The quantity increases when an in-scope execution enters the existing local
adapter-dispatch boundary and decreases when HAC is no longer awaiting that
adapter invocation, whether it returned, produced a normalized failure, raised
an exception, or was cancelled. Concurrent transitions must be coherent.

This is descriptive information about HAC-owned intervals only. It is not
runtime capacity, an admission decision, a concurrency limit, or a routing or
fallback policy. This Draft chooses neither a concrete state container nor a
synchronization primitive.

## Problem

Draft RFC-0098 identifies execution availability as distinct from static
eligibility, health, status, reachability, and fallback safety. Draft RFC-0099
limits its semantic authority to whether HAC begins a new independent
execution, rather than claiming knowledge of runtime-internal capacity. Draft
RFC-0100 identifies the existing local adapter-dispatch seam and one ordinary
composed HAC application process as the first bounded scope in which HAC can
truthfully describe its own invocation intervals.

That scope requires one shared fact for simultaneous independent requests. A
request-local fact cannot establish a coherent process-wide truth. A binary
fact can distinguish no active interval from at least one active interval, but
it becomes ambiguous when intervals overlap and one of them ends: it cannot by
itself distinguish whether another interval remains active.

The smallest truthful representation for the first proof must preserve that
overlap information without importing runtime capacity semantics, identity
tracking, or execution policy.

## Goals

This RFC should:

* define one non-negative quantity as the cardinality of active HAC-owned
  execution intervals in the RFC-0100 scope;
* make that quantity shared by all in-scope executions for the lifetime of one
  ordinary composed HAC application process;
* define coherent entry and exit transitions at RFC-0100's existing boundary;
* preserve the distinction between HAC no longer awaiting an invocation and
  proof of downstream runtime termination; and
* keep representation separate from execution policy, routing, and fallback.

## Non-goals

This RFC does not define:

* runtime capacity, maximum concurrency, available capacity, slots, permits,
  reservations, runtime load, runtime queue depth, runtime worker counts, or
  machine utilization;
* waiting, rejection, serialization, fairness, scheduling, candidate skipping,
  routing changes, fallback changes, balancing, or round robin;
* request IDs, execution IDs, per-execution registries, or an identity
  collection;
* an exact Python class, field, dataclass, application-state property,
  registry, storage object, or synchronization primitive;
* protocol additions, caller/receiver state synchronization, health or status
  changes, configuration keys, persistence, databases, IPC, worker or
  cross-process coordination; or
* discovery, dynamic membership, queues, schedulers, event buses, heartbeats,
  leases, background monitoring, runtime-specific capacity semantics, machine
  resource monitoring, or a 2.0 feature commitment.

## Proposal

### One process-local quantity

Within one ordinary composed HAC application process, the first representation
is a non-negative quantity whose value is the number of currently active
RFC-0100 HAC-owned execution intervals in that scoped process:

```text
0 = no scoped HAC execution interval is active
1 = one scoped HAC execution interval is active
2 = two scoped HAC execution intervals are active
...
```

It represents HAC-owned invocation intervals only. In particular, a value of
two means only that two such intervals are active in this scoped HAC process.
It does not mean that a runtime has capacity two, that it can accept two more
requests, or that the process should refuse a third request.

The quantity makes no claim about another HAC process, another server worker,
another process using the same runtime, a direct runtime client, the machine,
the runtime as a whole, or the cluster as a whole.

### Shared composition lifetime and granularity

The quantity belongs to the lifetime of the ordinary shared HAC application
composition/process scope established by Draft RFC-0100. All in-scope
executions in that composition must share the same representation.

For this first proof, the quantity is process-global. It is not partitioned by
capability, node, adapter, model, or request type. Fallback and uncomposed
application paths excluded by Draft RFC-0100 remain outside this proof.

This RFC decides the shared lifetime and granularity, not the concrete object
that later implementation may use to carry the information.

### Entry and exit transitions

When an in-scope HAC execution interval begins at RFC-0100's existing local
adapter-dispatch boundary, the shared quantity transitions from `N` to `N + 1`.
This marks entry to the HAC-owned invocation interval; it does not prove that
runtime inference has begun.

When HAC's awaited adapter invocation ends from HAC's perspective, the shared
quantity transitions from `N` to `N - 1`. This exit transition applies after
successful return, normalized failure, unexpected exception, and cancellation.
The quantity must not remain elevated because an invocation exited
exceptionally, and it must never become negative.

As defined by Draft RFC-0100, the interval ends when the adapter await ends.
For classification, subsequent HAC-side validation of the returned label does
not keep the adapter-invocation interval active. An exit transition likewise
does not prove that runtime inference, runtime HTTP processing, downstream
receiver work, or runtime resource use has ended.

### Coherent simultaneous transitions

Concurrent in-scope requests must not lose or duplicate an entry or exit
transition. The quantity must therefore have coherent transition semantics for
simultaneous independent requests.

This is an architectural requirement, not a choice of implementation tool.
This RFC does not require an `asyncio.Lock`, threading lock, semaphore, queue,
atomic library, condition variable, or another specific primitive.

### Representation is not policy

The quantity is representation only. No request behavior changes because its
value is zero, one, two, or any other value. It defines neither a threshold nor
an execution limit.

It does not decide whether another request begins, waits, is rejected, selects
another candidate, changes routing, or changes fallback. A separate future RFC
must define any policy that consumes this representation.

### No identity tracking

The first proof records cardinality only. It does not require request IDs,
execution IDs, sets, maps, or per-execution records. Temporary request-local
bookkeeping that a later implementation might need solely to guarantee cleanup
must not silently turn this architectural representation into an identity
registry.

### Receiver-side remote scope

For a remote request, only the receiver HAC process updates its quantity, when
that receiver enters and exits its own RFC-0100 local adapter invocation
interval. The caller does not share or mirror the receiver's quantity. This
RFC introduces neither protocol synchronization nor a cluster-wide count.

## Relationship to Draft RFC-0098, RFC-0099, and RFC-0100

This RFC depends conceptually on Draft RFC-0098 for the execution-availability
semantic distinction, Draft RFC-0099 for HAC's authority boundary, and Draft
RFC-0100 for the existing execution seam and bounded process-local scope.

This RFC cannot become Accepted before all three prerequisites are accepted.
If any prerequisite materially changes, this RFC must be reviewed again.
Nothing in this Draft treats a prerequisite Draft as accepted architecture.

## Rationale

A quantity preserves the truthful cardinality of overlapping HAC-owned
intervals. It contains slightly more information than a binary active/inactive
fact, but only the information necessary to remain truthful when one of
multiple overlapping intervals ends. The first proof intentionally chooses
enough information to stay truthful under overlap, but no richer execution
identity or runtime state.

The process-local scope remains deliberately small. Existing ordinary
application composition already provides a shared process lifetime; this RFC
does not extend that truth to a runtime, machine, worker group, or cluster.
The representation remains engine-independent and adds no runtime probe,
network authority, collection, or infrastructure.

Keeping representation separate from policy prevents a bookkeeping decision
from silently becoming an admission, routing, or scheduling decision. It
preserves current deterministic static routing and the existing fallback safety
boundary until a later architectural decision explicitly changes them.

## Alternatives considered

### Request-local representation only

Rejected. It cannot establish one coherent fact across simultaneous independent
requests in the scoped process.

### Binary active/inactive representation

Rejected for the first shared representation. Overlapping intervals make a
correct transition back to inactive depend on knowing whether another interval
remains active. A quantity captures that truth directly without identity
tracking.

### Per-execution identity collection

Rejected for the first proof. Identity tracking adds bookkeeping and semantics
that are not required to represent the cardinality of scoped HAC intervals.
This does not claim that identities could never be useful later.

### Synchronization primitive as the representation

Rejected as the representation. A lock-like, semaphore-like, or permit-like
primitive used as the truth tends to combine representation with enforcement or
policy, such as waiting, serialization, refusal, fairness, a concurrency
bound, or acquisition-cancellation semantics. A future implementation may use
synchronization internally to preserve coherent transitions, but this RFC does
not prescribe how.

### Runtime-provided capacity or load

Rejected. Draft RFC-0099 limits execution availability to HAC-owned truth and
preserves engine independence; runtime capacity or load would exceed that
authority boundary.

### Capability-, adapter-, or model-scoped quantity from the first proof

Rejected for the first proof. Draft RFC-0100 deliberately establishes one
bounded process-local scope, and this RFC chooses process-global granularity
first. Finer granularity is not declared permanently wrong.

## Trade-offs

Cardinality carries slightly more information than a binary active/inactive
fact. That cost is accepted solely to preserve truthful overlap semantics. It
is not accepted as runtime capacity or as a future scheduling input.

The first proof also leaves concrete storage, synchronization, observation,
and policy unresolved. This restraint avoids prematurely adding infrastructure
or execution behavior before evidence and a separate architectural decision
justify them.

## Impact

This Draft RFC changes no implementation. It changes no source code, tests,
routing, fallback, request behavior, protocol, health, status, configuration,
runtime behavior, or application construction.

If accepted, it authorizes only a later implementation proof of this
process-local representation. A further implementation RFC or explicit
implementation authorization is required before source changes. Any policy
that consumes the quantity requires a separate architectural decision.

## Open questions

* How should the process-lifetime representation be materialized in the
  implementation?
* What implementation technique should guarantee coherent entry and exit
  transitions?
* What deterministic tests should prove overlap, success, failure, exception,
  and cancellation behavior?
* Should an operator-visible observation surface ever expose this quantity?
* What policy, if any, should later interpret the quantity as execution
  availability?
* If a policy is introduced, what threshold or rule should it use?
* How should a receiver communicate a future policy outcome to a remote caller?
* When, if ever, should this representation affect routing?

## Decision

Pending.
