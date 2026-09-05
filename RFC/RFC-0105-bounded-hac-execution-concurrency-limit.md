# RFC-0105: Bounded HAC Execution Concurrency Limit

Status: Accepted

Date: 2026-09-04

Author: frian

## Summary

Home AI Cluster should generalize the first fixed execution-permission policy of Accepted RFC-0102 and Accepted RFC-0104 into one finite, positive, process-local **HAC execution concurrency limit**.

The limit applies only to the Accepted RFC-0101 cardinality of active HAC-owned execution intervals in one ordinary composed HAC application process. It answers only this HAC-owned policy question:

> How many simultaneous HAC-owned execution intervals does this composed HAC
> application process permit itself to engage?

It does not answer, observe, or imply how much concurrent work an underlying runtime can actually perform. It is not runtime capacity, runtime concurrency, GPU capacity, model capacity, worker count, queue depth, available runtime slots, machine utilization, or a success guarantee.

A limit of `1` is semantically equivalent to the accepted fixed zero/nonzero policy already defined by RFC-0102 and applied receiver-side by RFC-0104. This RFC proposes no operator configuration surface, status output, protocol disclosure, scheduler, queue, or routing algorithm.

## Problem

Accepted RFC-0101 provides one truthful, process-local cardinality for overlapping HAC-owned execution intervals. Accepted RFC-0102 and RFC-0104 use that cardinality in the first bounded policy:

```text
active intervals == 0 -> permit
active intervals > 0  -> deny
```

That policy has bounded real-machine evidence for both originating-process local execution and receiver-side pre-adapter refusal. It deliberately proves only one HAC-owned interval at a time.

The next narrow question is whether that fixed threshold can become one finite positive HAC-owned policy without claiming that the underlying runtime has matching concurrency capacity.

Without an explicit boundary, a later implementation could mislabel an HAC limit as runtime capacity, expose it as remote availability, or grow it into scheduling and load balancing. Each would exceed HAC's authority established by Accepted RFC-0099 and compromise engine independence.

## Goals

This RFC should:

- define one finite positive process-local HAC execution concurrency limit over RFC-0101's existing active-interval cardinality;
- generalize the fixed zero/nonzero policy while preserving `limit = 1` as its exact first-proof meaning;
- require one coherent permission-and-interval-entry transition for concurrent requests;
- permit the same process-local semantic at the established originating-local and receiver-side pre-adapter boundaries;
- preserve the RFC-0103 and RFC-0104 permission-denial and safe-continuation contracts; and
- make unusually explicit that the limit is not runtime capacity.

## Non-goals

This RFC does not define:

- runtime capacity, runtime concurrency, GPU or model capacity, worker count, runtime queue depth, runtime slots, machine utilization, or runtime load;
- per-capability, per-model, per-adapter, per-runtime, per-node-class, weighted, or capability-specific limits;
- a scheduler, queue, waiting, fairness, round robin, least-loaded routing, load balancing, scoring, weights, priorities, reservations, leases, permit-token lifecycle, distributed semaphore, central coordinator, or background worker;
- polling, cache, heartbeat, distributed availability state, runtime-capacity discovery, dynamic topology, or speculative duplicate execution;
- a configuration key, CLI option, environment variable, retained-configuration rule, configuration migration, remote declaration field, or `hac config` syntax;
- status or health output, protocol disclosure, remote cardinality or limit advertisement, persistence, cross-process coordination, or a multi-process architecture; or
- a product commitment to any non-`1` operator-selected value.

## Proposal

### One HAC-owned bounded limit

Within the one ordinary composed HAC application process scoped by Accepted RFC-0100 and Accepted RFC-0101, the architecture should have one finite positive integer HAC execution concurrency limit.

It applies to the same process-wide cardinality of active HAC-owned execution intervals. It is not partitioned by capability, model, adapter, runtime, or node class.

Conceptually:

```text
active HAC execution intervals < HAC execution concurrency limit
    -> grant execution permission and coherently begin the interval

active HAC execution intervals >= HAC execution concurrency limit
    -> deny execution permission before adapter invocation
```

The limit domain is finite positive integers only. Zero does not mean temporarily busy, disabled, runtime unavailable, or no participation. Static participation and enabled/disabled meanings belong to their existing boundaries. This RFC introduces no unlimited or infinite sentinel.

### Coherent bounded transition

Permission evaluation and entry to the HAC execution interval must be one coherent transition. Concurrent requests must not observe the same remaining permission and collectively begin more intervals than the limit permits.

For example, when the limit is `2`, requests A and B may coherently enter from cardinality `0` to `1` and `1` to `2`; request C must then be denied before adapter invocation.

The architecture does not prescribe a lock, semaphore, atomic operation, reservation, or other synchronization primitive. Any synchronization is bounded to this state transition and must not be held across adapter or runtime execution.

This introduces no waiting, queue, or permit lifecycle.

### Relationship to the first fixed policy

The fixed threshold in Accepted RFC-0102 and Accepted RFC-0104 is exactly the special case `HAC execution concurrency limit = 1`:

```text
limit = 1, active = 0 -> permit
limit = 1, active = 1 -> deny
```

This proposal generalizes only that permission threshold. It does not rewrite RFC-0102 or RFC-0104, change their established local or receiver boundaries, or turn the first proof into a scheduling architecture.

### Default ordinary behavior remains limit 1

This RFC does not introduce an operator selection mechanism for a non-`1` value.

Until a separate accepted configuration decision says otherwise, ordinary composed HAC application construction continues to use an effective limit of `1`.

A bounded implementation proof may construct a non-`1` value internally for tests or proof composition. That does not make the value configurable product behavior and does not expose it remotely.

### Local and receiver application

The same process-local semantic may apply at either already-established HAC execution boundary:

1. an originating process considering local execution; and
2. a receiver handling `/internal/cluster/request` before adapter invocation.

At the originating local boundary, a denial occurs before local adapter invocation and retains RFC-0102's deterministic consideration of the next statically eligible candidate.

At a receiver boundary, a denial occurs before adapter invocation and retains RFC-0104's exact internal HTTP `409` plus `execution-permission-denied` contract.

The remote caller learns only the request-specific outcome: processing continues after a grant, or this request was denied before adapter invocation with that exact validated refusal.

The caller must not learn the receiver's limit, active cardinality, remaining concurrency, utilization, queue state, or runtime capacity.

### Failure and continuation behavior

When the limit denies permission, the adapter must not be invoked and the runtime must not be contacted for that request.

The authoritative semantic remains:

```text
execution-permission-denied
```

A greater threshold creates no new failure type.

RFC-0103 and RFC-0104 remain unchanged. Remote continuation still requires the exact affirmative receiver refusal defined by RFC-0104.

There is no pre-screening, polling, cached availability, heartbeat, remote cardinality advertisement, speculative retry, or change to deterministic static candidate order.

A bare `409`, malformed response, timeout, generic transport error, or other ambiguous post-transmission failure remains terminal and must not cause another execution attempt.

### Interval lifetime remains HAC-owned

Accepted RFC-0100 and RFC-0101 continue to define an interval's end: it ends when HAC no longer awaits adapter invocation.

That end does not prove that the underlying runtime has stopped executing. A timed-out HAC invocation can release an HAC interval while the runtime continues consuming resources; a later request may therefore be permitted by this HAC limit while more underlying runtime work exists than the HAC cardinality suggests.

This is intentional. The limit is HAC-owned interval policy, not runtime-work accounting. HAC must not compensate by consulting runtime load or capacity.

## Runtime-capacity boundary

The limit states only a self-imposed process-local HAC policy. It is not and must never be described as:

- a claim that a runtime can execute the limit's number of requests at once;
- a claim that the runtime will not queue or serialize those requests;
- runtime capacity, runtime concurrency, available runtime slots, queue depth, worker count, model capacity, GPU capacity, or machine utilization; or
- a guarantee that granted work starts promptly or succeeds.

The underlying runtime can serialize, queue, parallelize, reject, or continue work independently of this policy.

No Ollama-, llama-server-, vLLM-, GPU-, model-, or hardware-specific capacity logic belongs here. This preserves the HAC authority boundary from Accepted RFC-0099 and engine independence.

## Examples

### Limit 1

```text
limit = 1
active = 0
new request -> permitted

limit = 1
active = 1
new request -> permission denied
```

This is the accepted first policy.

### Limit 2 proof composition

```text
limit = 2
active = 0
request A -> permitted, active becomes 1

request B -> permitted, active becomes 2

request C -> permission denied before adapter invocation
```

This makes no runtime-capacity statement and does not make `2` operator-configurable.

### Remote receiver with a proof limit of 2

```text
Remote A: internal proof limit = 2, active = 2
Caller sends a new request to A
A denies before adapter invocation
A returns exact RFC-0104 execution-permission-denied response
Caller may consider the next static remote candidate
```

The caller does not learn `2/2`, `0 slots`, or any equivalent capacity state.

## Explainability and privacy

Accepted RFC-0032 and RFC-0034 remain authoritative for the current explicit actual-request explanation surface. This RFC does not add a multi-candidate request timeline or a new explanation schema.

No network observation or remote disclosure is introduced. HAC must not expose active request identities, prompt or response contents, interval cardinality, the limit, machine load, runtime queue state, or utilization metrics through this RFC.

## Alternatives considered

### Retain only the fixed limit of 1

Deferred as the sole future policy. `1` remains the smallest valid bounded limit and the ordinary default, but a finite positive internal generalization can remain equally honest when explicitly scoped to HAC-owned intervals.

### Treat the limit as runtime capacity

Rejected. HAC lacks that authority, and the claim would be runtime- and hardware-specific as well as false after HAC timeouts.

### Per-capability or per-runtime limits

Deferred. They require a materially broader scope and concrete evidence from heterogeneous runtimes; one process-wide limit is the boring first semantic.

### Queue, scheduler, or load-based candidate choice

Rejected. The limit answers only whether the current candidate may begin at its local HAC boundary. Static candidate order remains authoritative.

### Remote availability advertisement or distributed coordination

Rejected. Receiver-side exact refusal already supplies the bounded safe-continuation fact without freshness, state distribution, or a coordinator.

## Trade-offs

This proposal permits a bounded number of overlapping HAC-owned intervals in an explicit proof composition but does not make underlying runtime behavior predictable.

The single process-wide limit is deliberately coarse. It avoids premature partitioning, scheduler semantics, and hidden capacity claims, but may later prove insufficient after real-machine evidence.

Ordinary behavior remains conservative at limit `1` until a separate accepted operator-selection decision exists.

## Impact

This RFC changes no implementation by itself. It changes no operator configuration, status, protocol, routing order, scheduler, queue, polling, or runtime-capacity semantics merely by being accepted.

Its architectural prerequisites, RFC-0098 through RFC-0104, are Accepted.

Acceptance authorizes one bounded implementation proof of the finite-positive process-local permission threshold while preserving ordinary effective limit `1` by default. A non-`1` value may be used only in internal tests or explicit proof composition under this authorization.

Acceptance does not authorize an operator configuration surface, retained selection, remote declaration field, status disclosure, protocol advertisement, or ordinary non-`1` product behavior. Those require a separate accepted architectural decision.

## Open / follow-up questions

- How should an ordinary operator select a non-`1` limit?
- Should retained configuration eventually own the value?
- Is one process-wide limit sufficient after evidence from heterogeneous runtimes?
- Should the limit ever be observable in operator status without making status routing truth?
- Does a future multi-process HAC application need separate coordination semantics?
- What real-machine proof is required before configurable concurrency becomes product behavior?

## Decision

Accepted. Home AI Cluster defines one finite positive process-local HAC execution concurrency limit over the existing RFC-0101 active-interval cardinality. Permission and interval entry remain one coherent transition; `limit = 1` preserves the already accepted first policy; and the limit is strictly HAC-owned policy rather than runtime-capacity truth. Acceptance authorizes one bounded internal implementation proof of a non-`1` threshold while ordinary effective behavior remains `1`. Operator selection, retained configuration, remote declaration fields, status or protocol disclosure, and ordinary non-`1` product behavior remain outside this decision and require separate accepted architecture.
