# RFC-0098: Execution Availability Semantics

Status: Accepted

Date: 2026-09-04

Author: frian

## Summary

Home AI Cluster should recognize **execution availability** as a distinct
cluster concept.

Execution availability is a request-time fact about whether an otherwise
eligible routing candidate may begin a new independent execution when
a new request is being considered.

It is separate from static routing eligibility, health and status observation,
reachability, and the safety boundary for fallback of an already-existing
logical request. This RFC defines that semantic distinction only. It authorizes
no implementation, representation, observation mechanism, ownership model, or
routing-policy change.

## Context

Home AI Cluster 1.0 uses retained and static facts to determine routing
eligibility. Those facts include declared node availability, requested and
declared capabilities, adapter declarations and capability support, and the
accepted local/remote policy with static remote declaration order.

The operator-facing surfaces answer different, bounded questions:

```text
hac config show -> retained configuration
hac preflight  -> static/declaration coherence
hac health     -> direct bounded local runtime observation
hac status     -> bounded observation of an explicitly declared static cluster
```

These observations are informational. They are not retained as routing state,
do not guarantee a future request, and do not currently influence candidate
selection.

The current request path can process independent requests concurrently. Two
such requests may independently select the same statically eligible candidate
and each send work to it. HAC currently owns no execution-availability or
current-work state. That is not itself a 1.0 defect; it exposes a missing
architectural term for a different question:

> May this otherwise eligible candidate begin a new independent execution
> now?

Without an explicit term, later work could silently overload static
eligibility, health, reachability, or status to answer that question.

## Goals

This RFC should:

* define execution availability as a narrow request-time cluster concept;
* distinguish it from the existing static eligibility, health, status,
  reachability, and fallback-safety meanings;
* preserve deterministic, operator-controlled static routing as the current
  behavior;
* preserve the conservative anti-double-execution boundary; and
* create a conceptual seam for later RFC discussion without choosing an
  implementation.

## Non-goals

This RFC does not introduce or decide:

* source, owner, reporter, or transport for execution availability;
* a field, protocol, state machine, or pseudo-code representation, including
  `can_accept_work`, `max_concurrent_requests`, `in_flight`, slots,
  reservations, counters, queue length, admission flags, load percentages, or
  capacity scores;
* timestamps, TTLs, leases, heartbeats, retained last-known execution state,
  background polling, status caches, or a monitoring loop;
* a routing change, round robin, random choice, least-loaded selection,
  fairness, balancing, scheduling, weights, priorities, or parallel candidate
  attempts;
* discovery, dynamic membership, persistence, queues, or background workers;
* a success guarantee for a runtime, model, network, or later request; or
* an implementation or a 2.0 product commitment.

## Decision / Proposal

Home AI Cluster should use the term **execution availability** for this
separate semantic question:

> At the point a new independent request is considered, may an otherwise
> eligible routing candidate begin a new independent execution?

Static eligibility and execution availability are distinct concepts. This is
not a description or authorization of the current implementation. It introduces
no additional lifecycle states and does not alter existing selection.

### Static eligibility remains distinct

Static eligibility answers whether retained cluster facts permit a candidate to
participate in routing for the requested capability. It remains governed by
existing node availability, capability, adapter, local/remote, and declared
ordering contracts.

A candidate can be statically eligible without HAC making any claim that it
can begin additional work at that moment. This RFC does not change the existing
eligibility contract.

### Health, status, and reachability remain distinct

`AdapterHealth.available` and `hac health` are one-shot runtime observations;
they do not automatically establish execution availability. A runtime may
answer a health observation without proving spare ability to begin another
independent execution.

Likewise, `hac status` remains a bounded informational observation of an
explicitly declared static cluster. A reachable HAC receiver or a runtime
reported available by status does not automatically establish execution
availability. Network or application reachability is evidence about
communication with a process, not sufficient evidence that more work may
begin.

This RFC does not redefine health or status, make status a scheduler, add
execution-availability output to an existing command, or merge these surfaces.

### Independent work remains distinct from fallback

Execution availability concerns a new independent request. It is not a new
interpretation of the fallback behavior for one already-existing logical
request.

The accepted fallback safety boundary remains unchanged: an ineligible
candidate is not contacted; an eligible candidate that fails with affirmative
pre-transmission connection-unavailable evidence may permit advance to the
next accepted candidate; and once transmission or execution may have begun,
HAC does not speculatively launch the same logical request elsewhere.

No execution-availability fact promises that a later execution will succeed.
It does not guarantee model success, runtime success, network success, or
future availability.

### Authority and freshness remain open

Any future use of execution availability in routing would require truthful
authority and freshness semantics. This RFC deliberately does not decide which
component owns or reports the fact, how it is obtained, what scope it has, or
how its truth applies at an exact request boundary.

In particular, this RFC does not decide whether the relevant authority belongs
to a node, runtime adapter, runtime, capability, model, receiver process,
caller, or another component.

### Existing routing remains unchanged

The current deterministic static routing behavior remains implemented after
this RFC: fixed local precedence among eligible candidates and declared remote
order where existing accepted behavior reaches remote candidates. Execution
availability does not change ordinary candidate selection in this RFC.

A later RFC would be required before the concept can influence routing.

## Rationale

The motivation is demonstrated current behavior, not speculative optimization.
HAC has an explicit static answer to whether a candidate may participate in
routing, plus bounded operator observations and a conservative failure boundary.
It does not yet have a distinct concept for whether the candidate may begin
another independent execution now.

Naming that question protects existing contracts. It lets later capacity or
concurrency work be evaluated against a stable semantic boundary rather than
overloading a static declaration or an informational observation. The proposal
is therefore not a performance, load-balancing, or scheduler RFC.

It also preserves local-first, privacy-first, engine-independent operation:
it creates no network authority, runtime-specific core behavior, collection,
or retained observation.

## Alternatives considered

### Reuse static `NodeDescription.availability`

Rejected for this purpose. It represents retained/static routing eligibility;
changing its meaning would overload an accepted contract.

### Reuse runtime adapter health

Rejected. One-shot runtime health is not equivalent to the ability to begin
another independent execution.

### Reuse cluster status

Rejected. Status is an explicit informational observation and does not affect
routing.

### Jump directly to capacity accounting or load balancing

Deferred. Mechanisms such as counters, slots, reservations, queue length, or
load-based policy presuppose the semantic question they would answer. This RFC
defines that question but does not choose a mechanism.

### Leave the concept unnamed

Rejected. An unnamed gap risks silently conflating eligibility, health,
reachability, status, and execution state in later work.

## Trade-offs

This RFC adds vocabulary without immediate behavior. That is intentional: the
new term may make future design discussions more precise while leaving current
operators without a new control or observation surface.

Deferring ownership, representation, freshness, and routing consequences means
the proposal cannot itself improve concurrent-work handling. It avoids claiming
authority or correctness that the current architecture does not possess.

## Impact

This RFC changes no source code, tests, commands, configuration, request
or response contract, routing behavior, fallback behavior, or runtime behavior.

If accepted, it becomes a semantic reference for later architectural proposals.
Those proposals must remain separate and must not be silently decided by agents:
agents implement project-owned decisions; they do not own later architectural
decisions.

## Follow-up questions

* What component should own or authoritatively report execution availability?
* At what exact request boundary should it be evaluated?
* What scope should the fact describe?
* How fresh must it be to influence one routing decision?
* Should it be obtained locally, remotely, or both?
* What happens when the fact cannot be established?
* How can future routing consume it while preserving deterministic,
  operator-controlled behavior?
* How should future routing behave when multiple independent requests concern
  the same otherwise eligible candidate?
* How is the pre-transmission-only fallback invariant preserved?
* What is the smallest bounded proof that would justify a routing-behavior RFC?

## Decision

Accepted.
