# RFC-0100: Execution Availability First-Proof Scope

Status: Draft

Date: 2026-09-04

Author: frian

## Summary

The first bounded proof of Home AI Cluster execution-availability truth should
exist at the existing HAC-controlled local adapter-dispatch boundary, for one
ordinary composed HAC application process.

The execution interval begins when that process enters the selected local
adapter invocation through this boundary. It ends when HAC is no longer
awaiting that invocation through the boundary: after successful return,
normalized failure, exception, or cancellation. This is a fact about an
HAC-owned invocation; it is not a claim that runtime inference has begun, that
the runtime is idle, or that runtime work has definitely stopped.

For remote execution, the corresponding first-proof scope belongs to the
receiver HAC process that reaches its own local adapter dispatch after transport
and receiver routing. The remote caller does not own the receiver's
process-local execution truth.

This Draft RFC defines scope and boundaries only. It introduces no
representation, enforcement mechanism, routing effect, protocol behavior, or
implementation change.

## Problem

Draft RFC-0098 names execution availability as distinct from static routing
eligibility, health, status, reachability, and fallback safety. Draft RFC-0099
establishes that HAC may own the decision about whether it begins a new
independent execution without claiming runtime-internal capacity.

Those Draft RFCs do not yet establish where a first truthful proof can exist or
how broadly its truth applies. Current HAC execution has a narrow,
engine-independent seam: `execute_local_routing_decision()` dispatches an
already selected local decision to the selected adapter's normalized `chat`,
`summarize`, or `classify` invocation. Source-grounded Chat is projected through
the same existing capability execution. A local selected request reaches that
seam directly; a remote request reaches it in the receiver process only after
internal transport and independent receiver routing.

Ordinary supported application construction supplies shared process-local
composition, registries, and adapter instances. Some fallback or uncomposed
`create_app()` paths can reconstruct registries and adapters per request. The
ordinary composed path therefore supplies a bounded truthful scope that must
not be generalized to every construction path, another process, or the runtime
itself.

## Goals

This RFC should:

* identify the existing HAC-controlled local adapter dispatch as the first
  proof's execution seam;
* limit the truth to one ordinary composed HAC application process;
* define the HAC-owned invocation start and end of the execution interval;
* apply the same boundary to local execution and receiver-side remote
  execution; and
* preserve engine independence, static capability-centered routing, operator
  ownership of runtimes, and existing fallback safety.

## Non-goals

This RFC does not define:

* a state representation, field, active-work count, maximum concurrency, slot,
  reservation, token, permit, or other mechanism;
* a component location for future state, or locks, semaphores, queues, worker
  pools, scheduling, waiting, rejection, fairness, or balancing;
* runtime capacity, load, queue depth, theoretical concurrency, idleness, or
  runtime-specific capacity probes;
* adapter-protocol, internal-remote-protocol, health, status, configuration, or
  persistence additions;
* IPC, multi-worker or cross-process coordination, discovery, dynamic
  membership, databases, event buses, background monitoring, heartbeats, or
  leases;
* a routing, candidate-skipping, fallback, retry, or remote-preference change;
  or
* a 2.0 feature commitment.

## Proposal

### Existing execution seam

The first bounded proof should use the existing HAC-controlled transition from
selected local execution to invocation of the selected local runtime adapter.
Current code evidences this seam in
`execute_local_routing_decision()`; the function name is evidence of the
present implementation, not a requirement to change or preserve that name.

The proposal does not create a new dispatch abstraction. Future refactoring is
not ruled out, but another abstraction is not justified before evidence
requires it.

### One ordinary composed HAC process

The first proof's truth is limited to one HAC application process using one
shared ordinary application composition. Within that process, it concerns only
HAC-controlled adapter invocations that traverse the stated execution seam.

It makes no claim about another HAC OS process, another server worker, another
HAC process using the same runtime, direct runtime clients outside HAC, the
whole machine, a node in a cross-process sense, the cluster, or
runtime-internal work. It also does not generalize to fallback or uncomposed
application paths that construct registries or adapters per request.

This limited scope is deliberate. The current architecture establishes neither
shared memory between processes nor multi-process coordination, and this first
proof does not add either.

### HAC-owned invocation interval

For the bounded proof, an execution interval begins when HAC enters the
selected local adapter invocation through the existing execution seam. This
does not establish that the external runtime has started inference at that same
instant.

The interval ends when HAC's awaited adapter invocation completes from HAC's
perspective: successful return, normalized failure, exception, or
cancellation. At that point, the statement is only that HAC is no longer
awaiting that invocation through this boundary.

In particular, cancellation or an ambiguous failure does not prove that all
related runtime work stopped. Runtime termination, queue state, and resource
release remain runtime- and adapter-dependent facts outside this proof.

### Local and receiver-side remote symmetry

For a locally selected request, the in-scope process is the caller process
when its selected local execution reaches local adapter dispatch.

For a declared remote request, the caller's outbound transport attempt is a
different boundary. The receiver validates and routes the request independently;
the first-proof scope applies in the receiver process when that process reaches
its own selected local adapter dispatch:

```text
caller HAC
    -> remote transport
    -> receiver HAC
        -> local adapter dispatch
        -> runtime
```

The caller does not own or enforce the receiver's process-local execution truth
merely by selecting a remote candidate. This RFC introduces no synchronization
between these separate process-local facts.

### Static eligibility and fallback remain separate

Static candidate eligibility remains the accepted routing architecture. The
execution interval begins only after a candidate has already been selected for
local execution; it does not change capability matching, local precedence, or
declared remote order.

The accepted fallback safety boundary also remains unchanged: an ineligible
candidate is not contacted; affirmative pre-transmission connection
unavailability may permit advancement; and once transmission or execution may
have begun, HAC does not speculatively execute the same logical request
elsewhere. This RFC creates no new fallback interpretation.

## Relationship to RFC-0098 and RFC-0099

This RFC depends conceptually on Draft RFC-0098, which defines the semantic
concept, and Draft RFC-0099, which defines HAC's authority boundary. It further
narrows where and over what bounded scope the first proof may truthfully exist.

This RFC cannot become Accepted before both RFC-0098 and RFC-0099 are accepted.
If either materially changes, this RFC must be reviewed again. Neither Draft is
treated here as accepted architecture.

## Rationale

The existing local adapter dispatch is the smallest factual HAC-owned seam
common to local execution and receiver-side remote execution. It is
engine-independent and avoids inventing a layer before one is needed.

One ordinary composed process is a deliberately weaker claim than knowing all
activity that may reach a runtime. It is nevertheless truthful within its
explicit boundary. The project prefers this bounded fact over a broader false
claim about machine-wide, runtime-wide, or cluster-wide activity.

The proposal preserves local-first and privacy-first constraints: it adds no
network authority, data collection, runtime probe, or external coordination.
It also leaves static, operator-owned capability routing deterministic and does
not make runtime behavior a core concern.

## Alternatives considered

### Introduce a new execution abstraction first

Rejected for the first proof. Current architecture already has a narrow
HAC-controlled local adapter-dispatch seam. Adding another abstraction before
evidence requires it conflicts with boring-solutions-first. A later refactoring
remains possible if it becomes justified.

### Make caller-side remote transport the universal execution boundary

Rejected. Caller transport and receiver-side adapter invocation have different
process ownership. Caller transport does not encompass the receiver's local
adapter-execution truth.

### Define the truth as runtime-wide

Rejected. A process-local HAC boundary cannot account for work entering the
same external runtime through another HAC process or a direct external client.

### Require multi-process coordination from the first proof

Rejected. Current architecture establishes no shared cross-process execution
truth, and this first proof intentionally remains bounded.

### Treat cancellation as proof that runtime work ended

Rejected. Existing cancellation architecture shows that HAC can stop awaiting
its own work without proving a runtime or downstream process stopped related
work.

### Create runtime-specific capacity probes

Rejected. The proof concerns HAC-owned invocation boundaries, not
runtime-internal capacity, and runtime-specific probes would undermine engine
independence.

## Trade-offs

The first proof accepts that HAC can reason only about executions traversing
one ordinary composed HAC process. It cannot truthfully answer everything
currently using the same runtime. This weakness is intentional: a bounded
truth is more useful and reliable than a broader false claim.

The RFC provides no immediate control, observation surface, or changed request
handling. That restraint leaves representation, simultaneous-request behavior,
and any future policy to later RFCs rather than silently deciding them here.

## Impact

This Draft RFC changes no implementation. It changes no source code, tests,
routing, fallback, health, status, configuration, request or response contract,
internal protocol, runtime behavior, or user-facing documentation.

If accepted, it authorizes only the architectural scope for a later bounded
proof. A further RFC is required before implementation of a representation,
simultaneous-request accounting, enforcement, unknown or unavailable behavior,
or any interaction with routing.

## Open questions

* What minimal representation should express the process-local execution truth?
* What object should hold any future process-local state?
* How should simultaneous independent requests interact with that state?
* What initial execution policy, if any, should a later proof establish?
* How should cancellation affect later state accounting while preserving the
  distinction from runtime termination?
* Should all ordinary composed application construction paths use one shared
  execution state?
* How should unknown state be treated?
* What is the smallest deterministic test proving a later chosen mechanism?
* What real multi-node proof should follow?
* When, if ever, should execution availability affect candidate selection?

## Decision

Pending.
