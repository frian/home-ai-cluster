# RFC-0099: Execution Availability Authority Boundary

Status: Draft

Date: 2026-09-04

Author: frian

## Summary

Execution availability is a Home AI Cluster-owned decision about whether HAC
may begin a new independent execution through an HAC-controlled execution
boundary.

It does not describe, measure, infer, or guarantee the underlying runtime's
internal capacity. In particular, it does not mean that a runtime has spare
capacity, that a model is idle, that a machine has resources available, or
that a runtime will execute work immediately or successfully.

This Draft RFC narrows the semantic concept introduced by Draft RFC-0098. It
does not choose an owner component, representation, mechanism, or routing
effect, and it authorizes no implementation or behavior change.

## Problem

RFC-0098 identifies execution availability as distinct from static eligibility,
health, status, reachability, and fallback safety. That distinction alone does
not establish what truth HAC is entitled to claim when it uses the term.

Current adapters normalize capabilities, health, execution, results, and
failures, but expose no engine-independent truth about runtime queue depth,
concurrency, workload, or capacity. Current static routing uses declared
eligibility and deterministic ordering, not current-work state. Health and
status are bounded informational observations and do not influence routing.

Without an authority boundary, later work could accidentally label
runtime-specific internals, machine utilization, or a transient observation as
cluster execution availability. That would overstate what HAC knows and risk
making the core runtime-specific.

## Goals

This RFC should:

* define the truth HAC may own as a permission to begin a new independent
  execution at an HAC-controlled execution boundary;
* preserve engine independence by separating that truth from runtime internals;
* preserve the current distinction between independent requests and fallback
  attempts for one logical request; and
* make clear that current static routing and failure behavior remain unchanged.

## Non-goals

This RFC does not define:

* a concrete owner or component location, including a caller router, receiver,
  adapter, executor, middleware, or application composition;
* data representation, fields, counters, slots, reservations, active-request
  limits, concurrency limits, queue lengths, load scores, or capacity units;
* admission mechanisms, locks, semaphores, polling, timestamps, freshness,
  TTLs, leases, heartbeats, or multi-worker coordination;
* protocol, health, status, or configuration additions;
* routing policy, balancing, fairness, round robin, scheduling, or candidate
  selection changes;
* runtime-specific capacity APIs or facts about Ollama, llama-server, vLLM,
  or any other runtime;
* runtime lifecycle, process management, tuning, worker configuration, model
  scheduling, or hardware resource allocation; or
* discovery, dynamic membership, queues, databases, event buses, background
  monitoring, or a 2.0 feature commitment.

## Proposal

### HAC-owned execution permission

For execution availability, HAC may own this question:

```text
May HAC begin this new independent execution?
```

The answer is a cluster-owned permission or condition concerning whether HAC
may start a new independent execution through the relevant HAC-controlled
execution boundary.

It is not an assertion that the underlying runtime can accept arbitrary
additional work. HAC may therefore own a bounded decision at its own boundary
without knowing the runtime's theoretical or internal maximum capacity.

The distinct runtime-internal question remains outside this RFC:

```text
How much work can the runtime actually handle?
```

HAC does not claim to know runtime queue depth, load, concurrency limits,
worker counts, model concurrency, hardware utilization, internal scheduling,
or whether the runtime serializes, queues, parallelizes, rejects, or later
succeeds with work.

### Engine-independent boundary

The core must not require knowledge of runtime-specific concurrency or load
behavior to give execution availability this HAC-owned meaning. A future
adapter may expose additional normalized facts only after a separate
architectural decision. This RFC introduces no such facts.

The relevant execution boundary is controlled by HAC, not by runtime internals.
This RFC deliberately does not decide where an eventual state or mechanism
lives. That implementation and ownership-location question remains open.

### Independent requests and fallback

Execution availability concerns separate logical requests. It does not
reinterpret attempts made while handling one existing logical request.

The accepted anti-double-execution boundary remains unchanged. HAC may advance
only on affirmative pre-transmission connection-unavailable evidence. Once
transmission or execution may have begun, HAC does not speculatively execute
the same logical request elsewhere. Execution availability neither broadens
nor replaces that rule.

### No success or capacity claim

An affirmative HAC-owned permission to begin an execution is not a success
guarantee. Connection, receiver, runtime, or inference failure may still occur
after HAC begins work. Existing normalized failure behavior remains
authoritative.

The permission is not a numerical capacity and does not promise immediate
runtime execution. It says nothing about spare runtime capacity, model idleness,
machine resources, or internal runtime scheduling.

### Existing routing remains unchanged

Current deterministic, capability-centered static routing remains unchanged.
Execution availability does not influence ordinary candidate selection or
request execution under this RFC. A separate RFC is required before it can
affect routing or behavior.

External runtimes remain operator-owned processes. This RFC gives HAC no
responsibility for their lifecycle, process management, tuning, worker
configuration, model scheduling, or hardware allocation.

## Relationship to RFC-0098

RFC-0098 is Draft and Pending. It defines execution availability as a distinct
semantic concept; this RFC depends conceptually on that Draft and narrows the
authority boundary for its meaning.

This RFC cannot become Accepted before RFC-0098 is accepted. If RFC-0098
materially changes, this RFC must be reviewed again. Nothing here treats
RFC-0098 as settled accepted architecture.

## Rationale

HAC can truthfully own whether it begins work through its own execution
boundary without pretending to observe or control a runtime's internal ability
to handle work. That smaller claim is local-first, privacy-first, and
engine-independent: it introduces no new runtime probe, network authority,
collection, or infrastructure.

Keeping the boundary narrow protects capability-centered static routing from
being silently transformed into runtime-load routing. It also preserves the
operator's ownership of external runtime processes and avoids granting a
cluster term different meanings for different engines.

## Alternatives considered

### Treat runtime internal capacity as execution availability

Rejected. Current adapter and core contracts establish no engine-independent
way to know runtime capacity. Treating it as the truth would invite
runtime-specific core architecture.

### Treat runtime health as execution availability

Rejected. Health is a bounded one-shot runtime observation. It does not
establish whether HAC should begin another independent execution.

### Treat machine utilization as execution availability

Rejected. CPU, GPU, RAM, and load are implementation details. They do not
directly establish a cluster-owned permission to begin work.

### Let each runtime define execution-availability meaning

Rejected as the core meaning. The same cluster concept would mean different
things by engine and would violate engine independence.

### Leave the authority boundary undefined

Rejected. Future capacity or routing work could otherwise claim runtime
knowledge HAC does not possess.

## Trade-offs

This RFC provides no new routing behavior, operator control, observation, or
concurrent-work handling. It intentionally defers those outcomes until a
later RFC can establish an appropriate implementation-neutral contract.

The narrow boundary means HAC may know less than a runtime. That restraint is
intentional: it avoids false capacity claims and keeps runtime-specific facts
outside the core unless separately accepted.

## Impact

This Draft RFC changes no source code, tests, requests, responses, protocols,
configuration, routing, fallback, health, status, or runtime behavior.

If accepted, it supplies an authority reference for later execution-availability
work. A later RFC must decide representation, concrete component ownership,
concurrency accounting, freshness, and any routing effect before implementation.

## Open questions

* At which HAC-owned execution boundary should the condition eventually be
  represented?
* Which process must make or enforce the execution-start decision?
* What scope should the condition have?
* How can independent concurrent requests observe one coherent HAC-owned
  decision?
* What happens when the relevant HAC-owned state cannot be established?
* What process-scope assumptions are acceptable for a first proof?
* What freshness guarantees are necessary if the condition later influences
  routing?
* What is the smallest implementation-neutral proof of this authority boundary?
* When should a later RFC decide representation and concurrency accounting?
* When should a later RFC allow execution availability to influence routing?

## Decision

Pending.
