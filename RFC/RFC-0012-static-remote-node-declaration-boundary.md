# RFC-0012: Static Remote Node Declaration Boundary

Status: Draft

Date: 2026-07-05

Author: frian

## Summary

Home AI Cluster should define how the orchestrator may know about, trust, and
consider a second non-local node before any two-machine implementation begins.

For the next step toward the two-machine proof, a non-local node may be
considered by the orchestrator only if it is manually and statically declared as
an allowed cluster member.

That declaration is the trust boundary for considering the node.

It is not discovery, registration, reachability proof, health proof, runtime
probing, transport design, or configuration file design.

## Problem

Home AI Cluster is moving toward the first meaningful proof:

```text
One endpoint. Two machines. One routed request.
```

Accepted Phase 2 RFCs already define a minimal node model, an explicit node
boundary, a static local node announcement, static node availability, and a
minimal agent shape.

Those decisions intentionally keep the current system:

- single-process;
- local;
- static;
- non-distributed.

Before implementation work introduces a second machine, the project needs to
define one narrow boundary:

```text
Which non-local machines may the orchestrator consider at all?
```

Without that boundary, future work could accidentally treat remote nodes as:

- discovered machines;
- registered nodes;
- reachable network endpoints;
- trusted peers by default;
- runtime adapter metadata;
- runtime-probed inventory;
- entries in a user-facing configuration format.

Those are different architectural decisions.

The project needs a boring rule that preserves user control before adding
networking, transport, authentication, discovery, or remote execution.

## Goals

This RFC should:

- define static remote node declaration as the boundary for considering a
  non-local node;
- preserve user/operator intent as the source of trust;
- ensure unknown or undeclared machines are never considered;
- keep the existing minimal node model usable for declared remote nodes;
- keep model information outside the minimal node model;
- keep static availability as routing eligibility only;
- keep node health descriptive only;
- keep runtime availability as adapter-call-time behavior;
- prevent runtime adapters from owning node identity or remote node metadata;
- keep current routing behavior conceptually unchanged;
- prepare for later work where routing may consider more than one statically
  declared node.

## Non-goals

This RFC does not introduce:

- discovery;
- registration protocol;
- node HTTP API details;
- daemon or process lifecycle;
- config file format;
- runtime probing;
- runtime supervision or auto-start;
- health polling;
- fallback or retries;
- dashboard;
- Docker;
- database;
- OpenAI-compatible API;
- model inventory;
- model placement or download automation;
- prompt or response logging;
- scheduling policy beyond current deterministic minimal routing;
- remote execution implementation;
- transport security design.

Future work in any of those areas requires a separate RFC.

## Proposal

For the next step toward the two-machine proof, Home AI Cluster should allow the
orchestrator to consider a non-local node only when that node has been manually
and statically declared as an allowed cluster member.

A manually declared remote node is an allowed cluster member description.

It says:

```text
This non-local node is allowed to be considered by the cluster.
```

It does not say:

```text
This node was discovered.
This node registered itself.
This node is reachable right now.
This node is healthy right now.
This runtime is live right now.
This node can execute a request over a chosen transport.
This node metadata came from a final configuration format.
```

Unknown or undeclared machines must never be considered by the orchestrator or
router.

Static remote node declaration is user/operator intent. It is not automatic
discovery.

### Declared remote node shape

A statically declared remote node may use the existing minimal node model:

- `id`;
- `name`;
- `availability`;
- `health`;
- `capabilities`;
- `adapters`.

The declaration describes cluster-facing metadata only.

The node `id` is the stable identifier used by the cluster in the current
cluster context. It is not a cryptographic identity, discovery name,
registration token, network address, or authentication credential.

The node `name` is a human-readable display name.

The declared `capabilities` describe what the cluster is allowed to consider
the node for, such as `chat`.

The declared `adapters` identify adapter names the cluster is allowed to use
for that node once later implementation work defines how remote execution is
performed.

Model information remains outside the minimal node model.

A remote node declaration must not require model inventory, model placement,
model download state, model-specific routing metadata, or runtime-specific model
names.

### Availability

Availability remains static routing eligibility only.

For a declared remote node, availability answers only this question:

```text
May this declared remote node be considered by routing?
```

It does not answer:

```text
Is the node reachable?
Is the node healthy?
Is the runtime available?
Was the node discovered?
Should the system retry somewhere else?
```

The existing availability semantics remain:

- `available` means the declared node may be considered by routing;
- `unknown` means the declared node is not considered by routing;
- `unavailable` means the declared node is not considered by routing.

No runtime probing, network probing, health polling, or adapter preflight is
performed as part of interpreting availability.

### Health

Health remains descriptive only.

A remote node declaration may include descriptive health metadata because health
is part of the minimal node model.

That health value does not prove reachability.

It does not prove runtime availability.

It does not drive routing, fallback, retries, polling, supervision, or adapter
selection.

Future work may define dynamic remote health behavior, but this RFC does not.

### Runtime availability

Runtime availability remains adapter-call-time behavior.

Declaring a remote node does not prove that a runtime behind that node is
available.

If a later implementation selects a remote node and then calls a runtime
adapter, runtime-specific failures must still be handled and normalized at the
runtime adapter boundary.

This RFC does not define how a remote adapter call happens.

### Reachability and transport

Reachability and execution transport are not decided by this RFC.

A static remote node declaration does not define:

- hostnames;
- ports;
- URLs;
- protocols;
- authentication;
- encryption;
- request forwarding;
- remote execution APIs;
- connection retries;
- timeout policy.

Those are separate decisions.

The declaration only defines whether the orchestrator is allowed to consider the
node once later implementation provides a way to reach and execute work on it.

### Relationship to runtime adapters

Runtime adapters must not own node identity or remote node metadata.

An adapter may know how to speak to a concrete runtime.

An adapter may expose adapter-level behavior through the runtime adapter
boundary.

An adapter must not decide:

- which remote nodes exist;
- which remote nodes are allowed cluster members;
- what identity a remote node has;
- what cluster-facing metadata a remote node exposes;
- whether an undeclared machine should be considered.

The remote node declaration remains a cluster-facing trust and metadata
boundary. Runtime adapters remain runtime-facing execution boundaries.

### Routing behavior

This RFC keeps current routing behavior conceptually unchanged.

The router may continue using the current minimal deterministic behavior:

- match the requested capability;
- consider static node availability;
- use declared adapter names;
- select a matching registered adapter.

This RFC does not introduce scoring, scheduling, fallback, retries, load
balancing, health-based routing, runtime probing, or remote execution.

The conceptual change is only that future routing may consider more than one
statically declared node once later implementation work allows that.

Until that later implementation exists, this RFC does not require production
code changes.

## Rationale

Manual static declaration preserves explicit user/operator control.

That matches the project principle:

```text
The user defines boundaries.
The cluster chooses within them.
```

A remote node is a larger trust decision than a local static node. Even before
transport exists, the project should say that unknown machines are outside the
cluster unless the user or operator explicitly allows them.

This keeps the next step toward two machines small. The project can define who
may be considered before deciding how that node is reached, how requests move,
how failures are represented, or how trust is enforced over a transport.

The proposal also preserves engine independence. Remote node metadata remains
cluster-facing and runtime-neutral. Runtime adapters continue to hide concrete
runtime behavior instead of owning node identity or cluster membership.

Keeping model inventory out of the declaration protects capability-centered
routing and avoids making the first remote-node step model-centered.

## Alternatives considered

### Allow any reachable machine

The orchestrator could consider any machine it can reach.

That would make reachability act as trust. It would silently expand the
cluster's authority and conflict with explicit user/operator boundaries.

### Add discovery first

Automatic discovery may become useful later.

It is rejected here because discovery would introduce trust, filtering,
networking, identity, and user-control questions before the project has accepted
those boundaries.

### Add registration first

A registration protocol may become useful later.

It is rejected here because registration would introduce protocol, lifecycle,
authentication, and dynamic-state decisions before the project needs them for
this boundary.

### Let runtime adapters define remote nodes

Adapters could report remote runtime locations or construct node descriptions.

That would blur node identity with runtime execution details. It would make the
core more likely to inherit runtime-specific assumptions and would conflict with
the accepted node and agent boundaries.

### Define transport and configuration now

The project could define the remote node declaration together with URLs,
transport, authentication, and a file format.

That would decide too much at once.

This RFC only defines the membership boundary for consideration. Transport,
security, and representation can be designed later against that boundary.

## Trade-offs

This proposal makes remote node consideration explicit before the system can
execute remote work.

That may feel early, but it prevents hidden trust assumptions from appearing in
the first two-machine implementation.

Manual declaration is simple and reviewable. It is also less convenient than
discovery or registration. That trade-off is acceptable because the project is
still preparing the smallest two-machine proof, not building a dynamic cluster
manager.

Static declarations can become stale. A node declared as `available` may still
be unreachable or fail when execution is attempted. That is acceptable because
availability remains static routing eligibility, health remains descriptive, and
runtime availability remains adapter-call-time behavior.

The RFC postpones important decisions about transport, authentication,
configuration, and failure handling. That keeps this decision narrow, but later
RFCs must define those boundaries before remote execution is implemented.

## Impact

This RFC affects future Phase 3 architecture and implementation review.

It does not require production code changes.

It does not require public API changes.

It does not change current single-process behavior.

It does not change node health, static node availability, runtime availability,
or runtime adapter boundaries.

If accepted, future work that introduces a second node must preserve this rule:

```text
Only manually and statically declared remote nodes may be considered.
```

Future work that introduces discovery, registration, transport, authentication,
configuration files, remote execution, runtime probing, model inventory,
fallback, retries, or health polling must be proposed separately.

## Open questions

- How will a remote node be reached?
- What transport will be used?
- How will user/operator declarations be represented later?
- What trust or authentication model is needed once transport exists?
- How will remote runtime failures be normalized?
- What is the smallest later implementation that can prove one endpoint, two
  machines, one routed request?

## Decision

Pending.
