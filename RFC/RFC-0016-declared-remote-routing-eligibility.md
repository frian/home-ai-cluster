# RFC-0016: Declared Remote Routing Eligibility Boundary

Status: Draft

Date: 2026-07-08

Author: frian

## Summary

Home AI Cluster should define the routing eligibility boundary for explicitly
declared remote nodes before implementation work changes routing behavior.

For local nodes, routing eligibility remains adapter-backed: the selected node
must declare an adapter name that resolves to an available local runtime adapter
in the local `AdapterRegistry`.

For explicitly declared remote nodes, routing eligibility may become
declaration-backed: the node may be eligible when the caller provides a
`RemoteNodeDeclarationRegistry`, the node appears in that registry, the node
declares the requested capability, and the node is statically available
according to existing availability semantics.

This would not require the remote node's declared adapter name to resolve to a
locally executable runtime adapter.

This RFC decides nothing yet. It proposes the smallest boundary needed to keep
declared remote routing honest before any implementation changes are made.

## Problem

The current router selects nodes through node capabilities and adapter
availability.

For local nodes, this is natural:

- the node declares an adapter name;
- the adapter exists in the local `AdapterRegistry`;
- execution calls the selected local adapter.

For declared remote nodes, the same requirement is conceptually awkward:

- the remote node may declare capabilities and adapter names;
- the remote node may be explicitly present in the caller-owned
  `RemoteNodeDeclarationRegistry`;
- execution should go through `RemoteTransport`;
- the remote node's adapter should not need to exist as a locally executable
  adapter in the local `AdapterRegistry`.

Recent implementation work proved the opt-in declared remote HTTP path and a
statically declared remote node whose node id is distinct from the local node
id. That proof used a local test adapter only to make the current router
consider the remote node routable.

That was useful as a proof, but it reveals the next architectural boundary.

Declared remote nodes should not need fake, placeholder, or locally executable
adapters just to become eligible for routing. Requiring a local adapter for a
remote node makes the model misleading because it treats remote execution as if
it depended on a local runtime adapter.

The project needs a small explicit boundary that distinguishes:

- local routing eligibility, which remains adapter-backed;
- declared remote routing eligibility, which may become declaration-backed;
- execution, which still decides local versus remote through explicit execution
  seams.

Without this boundary, future implementation could accidentally blur local
runtime adapters, declared remote node metadata, and remote transport execution.

## Goals

This RFC should:

- define a minimal draft proposal for declared remote routing eligibility;
- keep local routing eligibility backed by local adapter availability;
- allow declared remote nodes to become eligible through explicit caller-owned
  declarations and declared capabilities;
- avoid requiring fake or locally executable adapters for declared remote nodes;
- preserve `RemoteTransport` as the remote execution boundary;
- keep active `/v1/chat` behavior unchanged;
- keep the active default orchestrator local-only unless a future RFC changes
  that boundary;
- preserve static availability semantics from RFC-0010;
- preserve runtime availability as adapter-call-time behavior from RFC-0007;
- preserve caller-owned in-memory remote declarations from RFC-0015;
- keep implementation work small and explicit if this RFC is later accepted.

## Non-goals

This RFC does not introduce:

- config files;
- config loading;
- environment-variable loading;
- discovery;
- registration;
- persistence;
- daemon-owned registry state;
- active `/v1/chat` remote execution;
- automatic remote execution;
- public node API;
- new external protocol;
- retries;
- fallback;
- health probing;
- daemon lifecycle;
- streaming;
- model inventory;
- model placement;
- database;
- dashboard;
- Docker;
- OpenAI-compatible API.

This RFC is only about the routing eligibility boundary for explicitly declared
remote nodes.

## Proposal

Home AI Cluster should distinguish local routing eligibility from declared
remote routing eligibility.

Local routing eligibility remains adapter-backed.

Declared remote routing eligibility becomes declaration-backed.

The router or a small opt-in routing helper may consider a declared remote node
eligible when all of the following are true:

1. the caller explicitly provides a `RemoteNodeDeclarationRegistry`;
2. the node appears in that registry;
3. the node description declares the requested capability;
4. the node is statically available according to existing availability
   semantics.

This should not require the node's adapter name to resolve to a local runtime
adapter.

Declared remote eligibility must be opt-in and caller-owned. A remote node must
not become eligible merely because a process, URL, hostname, adapter name, or
network endpoint exists.

Unknown or undeclared machines must not be considered.

### Local routing eligibility

Local nodes still require local adapter availability through the
`AdapterRegistry`.

A local node may be considered only when its declared capabilities match the
request, its static availability allows routing, and one of its declared adapter
names resolves to a local runtime adapter.

Local execution still calls a local runtime adapter.

Runtime-specific details remain behind runtime adapters.

This RFC does not change local adapter registration, local adapter selection,
runtime adapter interfaces, runtime error normalization, or local execution
behavior.

### Declared remote routing eligibility

A declared remote node may be considered by routing based on explicit
caller-owned declaration and declared cluster-facing metadata.

For a declared remote node, the remote declaration is the source that allows the
node to be considered. The local `AdapterRegistry` is not the source of remote
execution capability.

The declared node's capabilities describe what the caller allows the router to
consider the node for.

The declared node's static availability continues to answer only:

```text
May this declared node be considered by routing?
```

Availability does not prove reachability, live health, runtime availability,
transport availability, or successful execution.

This RFC leaves open whether declared remote nodes should continue to carry
adapter names as descriptive cluster-facing metadata, or whether routing
eligibility should depend only on capabilities for this path.

### Remote execution boundary

Remote execution, when explicitly used, goes through `RemoteTransport`.

The router may select a declared remote node, but execution decides local versus
remote through the declared remote execution seam.

No direct runtime call happens for remote nodes from the local orchestrator.

The local orchestrator must not call a remote node's runtime adapter directly.
It may only hand a normalized cluster request to the remote transport boundary
after an explicit opt-in path has selected a declared remote node.

Runtime-specific details remain behind the adapter boundary on the machine that
executes the request.

### Relationship to `/v1/chat`

The active default orchestrator remains local-only unless a future RFC
explicitly changes it.

`/v1/chat` must remain unchanged by this RFC.

This RFC does not activate remote routing in `/v1/chat`.

This RFC does not make remote execution automatic.

This RFC does not wire caller-owned remote declarations into API routes,
configuration loading, daemon state, or global process state.

### Implementation shape

If this RFC is later accepted, implementation should remain small and explicit.

One acceptable implementation shape may be a new opt-in routing helper for
declared remote orchestration rather than changing the default
`route_request()` behavior.

Another acceptable implementation shape may be a narrow internal helper used by
an explicit opt-in orchestration seam.

This RFC does not decide the implementation shape.

The important boundary is:

```text
local node eligibility
  -> adapter-backed

declared remote node eligibility
  -> declaration-backed
```

## Rationale

This proposal keeps execution boundaries honest.

Local execution uses local adapters.

Declared remote execution uses remote transport.

Requiring declared remote nodes to resolve adapter names through the local
`AdapterRegistry` makes a remote node look locally executable even when the
execution path should cross a transport boundary.

Declaration-backed remote eligibility better matches RFC-0012 and RFC-0015:
the caller explicitly chooses which remote nodes may be considered, and those
declarations remain caller-owned and in memory for the current step.

The proposal also preserves engine independence. The core should reason about
requests, capabilities, nodes, routing decisions, adapters, results, health,
and availability. It should not require a local fake adapter to represent a
runtime that lives behind a remote node boundary.

The proposal keeps privacy and user control visible. Unknown machines are not
considered. Remote nodes become eligible only through explicit declarations.
Active remote execution remains opt-in and behind `RemoteTransport`.

The active `/v1/chat` path remains local-only, so this RFC does not silently
expand the system's authority or send request contents across a remote boundary.

## Alternatives considered

### Keep requiring local adapter entries for remote nodes

The project could keep the current behavior and require every routable remote
node to have an adapter name that resolves in the local `AdapterRegistry`.

This is simple, but misleading. It treats remote execution as if it depended on
a locally executable runtime adapter.

It also encourages tests and future code to create local adapter entries only
to satisfy routing, even when execution should go through `RemoteTransport`.

### Add fake placeholder adapters for remote nodes

The project could add placeholder adapters whose only job is to make declared
remote nodes look routable.

This is rejected because fake adapters make the model harder to understand and
blur the adapter boundary.

A placeholder adapter is neither a real local runtime adapter nor a remote
transport. It would hide the distinction this RFC is trying to make explicit.

### Activate remote routing in `/v1/chat`

The project could change `/v1/chat` so the active API path considers declared
remote nodes.

This is rejected for this RFC because it is a separate architectural decision.

Activating remote routing in `/v1/chat` would affect runtime behavior, request
boundary expectations, privacy review, error behavior, and user-facing API
semantics.

### Introduce discovery or registration

The project could make remote nodes eligible through discovery, registration,
or a daemon-owned registry.

This is rejected because RFC-0015 deliberately kept declarations caller-owned
and in memory for the next step.

Discovery, registration, dynamic state, persistence, and daemon lifecycle all
require separate RFCs.

## Trade-offs

This makes the router model slightly more complex because local and declared
remote nodes have different eligibility sources.

That complexity may be acceptable because it keeps execution boundaries honest:

- local execution uses local adapters;
- declared remote execution uses remote transport.

The implementation must remain small and explicit.

The proposal may require routing explanations to distinguish local
adapter-backed eligibility from declared remote declaration-backed eligibility.

The proposal may also require tests that prove declared remote nodes can become
routing-eligible without local fake adapters.

This proposal does not make remote execution easier for users yet. It only
clarifies the next boundary so implementation can remain honest and reviewable.

## Impact

This RFC may affect future implementation of:

- routing helpers;
- router tests;
- declared remote orchestration seam;
- Phase 2 current-state documentation.

It must not require changes to:

- `/v1/chat`;
- config loading;
- discovery;
- registration;
- persistence;
- daemon lifecycle.

This RFC does not require production code changes by itself.

It does not require tests by itself.

It does not change current runtime behavior.

It does not mark any remote node as automatically executable.

## Open questions

- Should this be implemented as a new opt-in routing helper rather than
  changing the existing `route_request()` behavior?
- Should local and declared remote eligibility produce the same
  `RoutingDecision` shape?
- How should routing explanations distinguish local adapter-backed eligibility
  from declared remote declaration-backed eligibility?
- Should declared remote routing require adapter names at all, or only
  capabilities?
- Should this be implemented before or after a more explicit execution-target
  model?

## Decision

Pending.
