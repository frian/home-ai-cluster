# RFC-0019: Phase 2 Closeout and Phase 3 Entry

Status: Accepted

Date: 2026-07-09

Author: frian

## Summary

Phase 2 has prepared the architecture for explicit opt-in selected candidate
execution, but it has not made Home AI Cluster distributed.

The current implementation has a coherent preparation chain:

```text
declared remote eligibility
  -> declared remote routing candidate discovery
  -> candidate composition beside local routing candidates
  -> explicit opt-in candidate selection
  -> explicit opt-in selected candidate orchestration
  -> existing execution boundaries
```

The active path remains unchanged:

```text
/v1/chat
  -> active orchestrate_request(...)
  -> route_request(...)
  -> local adapter execution
```

This RFC proposes a Phase 2 closeout checkpoint and Phase 3 entry boundary. It
does not implement anything. It does not activate remote routing, remote
execution, dynamic discovery, registration, config loading, persistence,
fallback, health probing, scoring, scheduling, or distributed behavior.

## Problem

Phase 2 now contains several explicit preparation seams for declared remote
nodes and selected routing candidates.

Those seams are useful because they make future two-machine behavior easier to
review and test. However, without a closeout checkpoint, the project could
accidentally treat prepared architecture as active distributed behavior.

That would blur important boundaries:

- remote declarations could be mistaken for dynamic discovery;
- remote eligibility could be mistaken for active remote routing;
- selected candidate orchestration could be mistaken for default remote
  execution;
- prepared execution boundaries could be mistaken for retries, fallback,
  scheduling, or health-aware routing;
- Phase 3 work could begin without a clear RFC boundary.

The project needs a boring checkpoint that records what Phase 2 has prepared,
what it has not activated, and what must be true before entering Phase 3.

## Goals

This RFC should:

- define the current Phase 2 state as prepared architecture, not active
  distributed behavior;
- summarize the opt-in preparation chain from declared remote eligibility to
  existing execution boundaries;
- clarify that `/v1/chat` remains local-only;
- clarify that active `orchestrate_request(...)`, `route_request(...)`,
  `RoutingDecision`, and active execution remain unchanged;
- identify what Phase 2 still has not activated;
- identify what is still missing from the roadmap definition of Phase 2;
- define what kinds of work should be considered Phase 3 work;
- require a separate accepted RFC before introducing real two-machine behavior,
  registration, dynamic discovery, active remote routing, or active remote
  execution;
- preserve local-first, privacy-first, explicit opt-in defaults.

## Non-goals

This RFC does not:

- implement code;
- change `/v1/chat`;
- change active `orchestrate_request(...)`;
- change `route_request(...)`;
- change `RoutingDecision`;
- change active execution;
- activate remote routing by default;
- activate remote execution by default;
- decide dynamic discovery;
- decide registration implementation;
- decide config loading;
- decide persistence;
- introduce daemon-owned registry state;
- decide retries;
- decide fallback after selected candidate failure;
- decide health probing;
- decide scoring or scheduling;
- introduce distributed behavior;
- introduce Docker or Kubernetes;
- introduce a dashboard;
- introduce a database;
- introduce an OpenAI-compatible API.

## Current Phase 2 State

Phase 2 remains:

- single-process;
- local;
- static;
- non-distributed;
- explicit opt-in for remote seams.

The active public request path remains:

```text
/v1/chat
  -> active orchestrate_request(...)
  -> route_request(...)
  -> execute_routing_decision(...)
  -> execute_local_routing_decision(...)
  -> local runtime adapter
```

Remote routing is not active by default. Remote execution is not active by
default. Request contents do not cross a remote transport boundary unless an
explicit caller uses an opt-in helper and provides the required remote seam.

Phase 2 has prepared:

- static node descriptions;
- static node availability semantics;
- descriptive node health;
- static in-memory local node and adapter registries;
- static remote node declarations;
- a remote transport boundary;
- a concrete opt-in HTTP remote transport;
- a declared remote eligibility boundary;
- declared remote routing candidate discovery;
- candidate composition beside local routing candidates;
- explicit opt-in candidate selection;
- explicit opt-in selected candidate orchestration;
- existing local and declared remote execution boundaries.

Phase 2 has not activated:

- dynamic discovery;
- registration;
- config loading;
- persistence;
- daemon-owned registry state;
- active remote routing;
- active remote execution;
- retries;
- fallback after selected candidate failure;
- health probing;
- scoring;
- scheduling;
- distributed behavior.

The roadmap definition of Phase 2 says that the project should define what a
node is, including cluster-facing node description, availability, supported
capabilities, declared adapter names, and basic health. The current
implementation has prepared those boundaries, but it still does not include a
separate agent process, node discovery, or registration protocol.

## Proposal

Home AI Cluster should treat the current Phase 2 state as a closeout checkpoint
for prepared architecture only.

Phase 2 should be considered to have prepared the shape needed for future
explicit two-machine work, but it should not be described as distributed.

The current opt-in chain is:

```text
declared remote eligibility
  -> declared remote routing candidate discovery
  -> candidate composition beside local routing candidates
  -> explicit opt-in candidate selection
  -> explicit opt-in selected candidate orchestration
  -> existing execution boundaries
```

This chain is not an active routing policy. It does not change `/v1/chat`.
It does not change active `orchestrate_request(...)`. It does not change
`route_request(...)`. It does not change `RoutingDecision`. It does not change
active execution.

Any move toward Phase 3 real two-machine behavior must be preceded by a
separate accepted RFC when it would introduce:

- real two-machine active behavior;
- active remote routing;
- active remote execution;
- registration;
- dynamic discovery;
- config loading;
- persistence;
- daemon-owned registry state;
- fallback after execution failure;
- health probing;
- scoring;
- scheduling.

Before real two-machine behavior exists, remote seams must remain explicit and
opt-in. Unknown or undeclared machines must not be contacted. Request contents
must not leave the local cluster unless an explicit caller provides the remote
execution boundary required by accepted RFCs.

Phase 3 work should begin only when the next RFC clearly states which part of
two-machine behavior it activates and which boundaries remain out of scope.

## Phase 2 Closeout Criteria

Phase 2 may be treated as architecturally prepared when:

- the active `/v1/chat` path remains local-only;
- active `orchestrate_request(...)` remains unchanged;
- `route_request(...)` remains unchanged;
- `RoutingDecision` remains unchanged;
- active execution remains unchanged;
- local execution remains adapter-backed;
- declared remote execution remains behind explicit `RemoteTransport`;
- declared remote declarations remain caller-owned and static;
- candidate discovery, composition, selection, orchestration, and execution
  remain separate;
- selected candidate orchestration consumes caller intent and does not create a
  routing policy;
- missing or invalid selected candidates fail explicitly;
- missing `RemoteTransport` for declared remote selected candidates fails
  explicitly;
- failure does not retry or fall back to another candidate.

These criteria describe a prepared boundary. They do not make remote behavior
active.

## Phase 3 Entry Criteria

Phase 3 should be treated as the first real two-machine proof.

Entering Phase 3 requires a separate accepted RFC before changing active
behavior. That RFC should define, at minimum:

- which two-machine behavior is being activated;
- whether `/v1/chat` changes or remains unchanged;
- how nodes are allowed to become visible to the orchestrator;
- whether declarations remain manual and static for the first proof;
- what remote transport is allowed to carry request contents;
- what failure shape is exposed when remote execution fails;
- whether fallback is still out of scope;
- what privacy boundary prevents accidental remote execution;
- what remains explicitly opt-in.

If the next step introduces discovery, registration, config loading,
persistence, daemon-owned registry state, active remote routing, active remote
execution, fallback, health probing, scoring, or scheduling, that decision
belongs in its own accepted RFC before implementation.

## Rationale

The current architecture is useful because it separates concerns:

- declared remote eligibility says which declared remote nodes may be
  considered by opt-in helpers;
- candidate discovery finds possible candidate families;
- candidate composition presents local and declared remote candidates side by
  side;
- candidate selection records explicit caller intent;
- selected candidate orchestration consumes that already selected intent;
- execution boundaries decide how local or declared remote execution is
  performed.

Keeping these steps separate makes future Phase 3 work easier to review. It
also protects privacy defaults. Remote execution should not become active just
because a transport, declaration, or helper exists.

Calling the current state distributed would make the architecture harder to
reason about. The system has prepared the seams needed for a future
two-machine proof, but the active behavior remains local-only.

## Alternatives Considered

### Treat Phase 2 as already distributed

This is rejected. Phase 2 has remote preparation seams, but the active path is
still local-only and static. Describing it as distributed would overstate the
implementation and weaken the meaning of Phase 3.

### Move directly into active remote routing

This is rejected for this RFC. Active remote routing changes privacy,
execution, error, and user-facing behavior. It needs a separate accepted RFC.

### Decide dynamic discovery now

This is rejected. Dynamic discovery is a major architectural decision and is
not required to record the Phase 2 closeout checkpoint.

### Decide registration or daemon-owned state now

This is rejected. Registration and daemon-owned registry state would change
ownership, lifecycle, trust, and persistence assumptions. They require a
separate RFC.

### Decide fallback, scoring, or scheduling now

This is rejected. Fallback, scoring, and scheduling are routing policy
decisions. They are outside the Phase 2 closeout checkpoint.

## Trade-offs

This RFC adds one more checkpoint document before Phase 3.

That adds a small amount of process, but it makes the boundary between
prepared architecture and active distributed behavior explicit. It helps keep
future Phase 3 work from smuggling in discovery, registration, persistence,
fallback, health probing, scoring, scheduling, or default remote execution.

The trade-off is that Phase 3 may need more than one RFC before the first
two-machine proof is active. That is acceptable because the project values
small, reviewable steps and explicit privacy boundaries.

## Impact

If accepted, this RFC would affect project planning and review expectations.

It would not require code changes by itself.

It would not change `/v1/chat`, active `orchestrate_request(...)`,
`route_request(...)`, `RoutingDecision`, active execution, remote routing, or
remote execution.

It would clarify that future Phase 3 implementation work needs separate
accepted RFC coverage before activating real two-machine behavior or adding
discovery, registration, config loading, persistence, daemon-owned registry
state, fallback, health probing, scoring, or scheduling.

## Open Questions

- What is the smallest Phase 3 RFC that can prove one endpoint, two machines,
  one routed request without introducing unnecessary infrastructure?
- Should the first Phase 3 proof keep manual static remote declarations, or
  should declaration loading be decided first?
- What user-visible error shape should active remote execution use when a
  declared remote node cannot execute the request?
- Should `/v1/chat` remain local-only for the first Phase 3 proof, with a
  separate explicit endpoint or helper exercising two-machine behavior?

## Decision

Accepted.

Phase 2 is considered a prepared architecture checkpoint, not active
distributed behavior.

The prepared opt-in chain is:

```text
declared remote eligibility
  -> declared remote routing candidate discovery
  -> candidate composition beside local routing candidates
  -> explicit opt-in candidate selection
  -> explicit opt-in selected candidate orchestration
  -> existing execution boundaries
```

The active path remains unchanged:

```text
/v1/chat
  -> active orchestrate_request(...)
  -> route_request(...)
  -> local adapter execution
```

Remote routing is not enabled by default. Remote execution is not enabled by
default.

Phase 3 work requires a separate accepted RFC before introducing real
two-machine active behavior, active remote routing, active remote execution,
dynamic discovery, registration, config loading, persistence, daemon-owned
registry state, fallback, health probing, scoring, or scheduling.
