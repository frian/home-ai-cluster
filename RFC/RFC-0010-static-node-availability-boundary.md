# RFC-0010: Static Node Availability Boundary

Status: Draft

Date: 2026-07-04

Author: frian

## Summary

This RFC defines Phase 2 node availability as static declared routing
eligibility.

Availability is part of the static node announcement. It is manually declared
for now. It is not a live runtime check, node health, adapter health, runtime
availability, discovery, or dynamic node state.

This RFC documents and constrains the current behavior. It does not introduce
new routing behavior.

## Problem

Home AI Cluster now has an explicit node boundary and an explicit static local
node announcement.

The minimal node model includes both availability and health. Runtime adapters
also have their own availability and health concepts. Without a clear boundary,
future changes could blur several different questions:

- should this declared node be eligible for routing?
- does the node describe itself as healthy?
- is a runtime adapter reachable right now?
- did a runtime call fail at execution time?
- was a node discovered or registered dynamically?

Those questions are related, but they are not the same architectural decision.

The current implementation already treats node availability as a static routing
eligibility flag. Only nodes whose availability is `available` are considered
for routing. Nodes whose availability is `unknown` or `unavailable` are not
considered.

This RFC records that behavior before later work turns availability into
runtime probing, health-based routing, discovery state, or dynamic node state.

## Goals

This RFC should:

- define Phase 2 node availability as static declared routing eligibility;
- keep availability part of the node announcement;
- keep availability manually declared for now;
- distinguish node availability from node health;
- distinguish node availability from adapter health;
- distinguish node availability from runtime availability;
- document the current routing behavior;
- preserve the existing static, local, single-process implementation shape;
- keep runtime-specific details behind adapters;
- avoid introducing new routing behavior.

## Non-goals

This RFC does not introduce:

- remote nodes;
- a node HTTP API;
- discovery;
- a registration protocol;
- a daemon or agent process;
- health polling;
- runtime probing;
- runtime supervision;
- health-based routing;
- fallback;
- retries;
- file-based config;
- model inventory;
- model placement automation;
- public API changes;
- routing policy changes beyond documenting existing static eligibility
  semantics.

Future dynamic availability, runtime-derived availability, health-based routing,
or discovery-based availability require separate RFCs.

## Proposal

For Phase 2, node availability means:

> This statically declared node is eligible, or not eligible, to be considered
> by routing.

Availability is part of the static node announcement defined by RFC-0009.

It is manually declared for now.

It is not discovered dynamically.

It is not derived from live runtime probing.

It is not owned by runtime adapters.

It is not node health.

It is not adapter health.

It is not runtime availability.

It is not dynamic node state.

The current allowed availability values remain:

- `available`;
- `unknown`;
- `unavailable`.

The current routing behavior is:

- only nodes whose availability is `available` are considered by routing;
- nodes whose availability is `unknown` are not considered by routing;
- nodes whose availability is `unavailable` are not considered by routing.

No runtime probing is performed when filtering nodes by availability.

No adapter health preflight is performed when filtering nodes by availability.

Node health remains descriptive and does not affect routing.

Runtime availability remains an adapter concern at runtime adapter call time, as
defined by RFC-0007.

This RFC does not change routing behavior. It records the existing static
eligibility semantics so future changes have a clear boundary to reference.

## Rationale

Static declared availability keeps the Phase 2 node model simple and honest.

It lets the router answer one narrow question:

```text
May this declared node be considered for this request?
```

It does not ask:

```text
Is the runtime reachable right now?
Is the node healthy?
Was the node discovered?
Should another node be tried?
Should the system poll or supervise anything?
```

Keeping availability static avoids turning the node boundary into monitoring,
discovery, runtime probing, fallback, or supervision.

Keeping availability separate from health preserves RFC-0006. Node health can
describe the node, but it does not drive routing.

Keeping availability separate from runtime availability preserves RFC-0007.
Runtime failures are detected and normalized by runtime adapters at call time,
not by the router before selection.

Keeping availability part of the node announcement preserves RFC-0009. The
local node declaration remains the source of truth for cluster-facing metadata
until a later RFC defines another source.

## Alternatives considered

### Treat availability as node health

The system could use node health to decide whether a node is available.

That would introduce health-based routing, which RFC-0006 and RFC-0008
explicitly leave out of scope for now.

### Treat availability as adapter health

The system could check adapter health before routing and use that result as
node availability.

That would introduce adapter health preflight and blur the boundary between a
node declaration and runtime adapter behavior.

### Treat availability as runtime availability

The system could derive node availability from whether a runtime can answer a
request right now.

That would introduce runtime probing before routing and would conflict with
RFC-0007, which keeps runtime availability at adapter call time.

### Treat availability as discovery state

The system could treat availability as whether a node has been discovered,
registered, or recently seen.

That would introduce discovery, registration, or dynamic node state before the
project has accepted those boundaries.

### Remove availability from routing

The router could ignore node availability entirely and route only by capability
and adapter name.

That would make the availability field less meaningful and would undo the
current static eligibility behavior. Keeping availability as declared routing
eligibility is clearer.

## Trade-offs

This proposal makes the current behavior explicit and easy to review.

It keeps routing simple and static.

It also means a node declared as `available` may still fail when its selected
runtime adapter is called. That is acceptable because runtime availability is
handled at adapter call time.

It means `unknown` is conservative: an unknown node is not considered for
routing in Phase 2. That avoids pretending to know how to handle dynamic node
state before discovery or registration exists.

It postpones useful future behavior such as dynamic availability, health-based
routing, discovery-derived state, and runtime-derived availability. Those
features require separate RFCs because they change routing semantics and user
expectations.

## Impact

This RFC affects node and routing semantics.

It does not require a public API change.

It does not require a code change by itself.

It does not introduce new routing behavior.

It documents the existing static availability behavior:

- `available` nodes are considered for routing;
- `unknown` nodes are not considered for routing;
- `unavailable` nodes are not considered for routing;
- node health does not affect routing;
- runtime probing is not performed;
- adapter health preflight is not performed.

Future work that changes availability into dynamic state, derives availability
from runtime checks, uses health for routing, or ties availability to discovery
must reference this RFC and define a new boundary.

## Open questions

- When should the project introduce dynamic availability?
- Should future discovered nodes begin as `unknown` or `unavailable`?
- Should future file-based configuration allow users to declare availability?
- How should future user-visible node status distinguish availability, health,
  and runtime errors?
- What is the smallest useful availability behavior before the first
  two-machine proof?

## Decision

Pending.
