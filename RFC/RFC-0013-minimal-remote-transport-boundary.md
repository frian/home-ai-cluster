# RFC-0013: Minimal Remote Transport Boundary

Status: Draft

Date: 2026-07-05

Author: frian

## Summary

Home AI Cluster should define the minimal remote transport boundary before a
routed cluster request may cross from the orchestrator to a manually and
statically declared remote node.

RFC-0012 decides which remote nodes may be considered by the orchestrator. This
RFC decides only what boundary must exist before a routed request can cross to
such a node.

A remote transport boundary is the narrow boundary that may carry a normalized
cluster request from the orchestrator to a selected manually declared remote
node boundary and return either a normalized cluster result or a normalized
transport or runtime failure.

This RFC does not choose a concrete protocol.

It does not define an HTTP endpoint, node public API, authentication model,
daemon lifecycle, discovery, registration, dynamic configuration, retries,
fallback, health probing, runtime supervision, or remote execution
implementation.

## Problem

Home AI Cluster is moving toward the first meaningful proof:

```text
One endpoint. Two machines. One routed request.
```

Accepted RFCs already define the minimal system shape, minimal node model,
runtime availability boundary, Phase 2 node boundary, static local node
announcement boundary, static node availability boundary, minimal agent shape,
and static remote node declaration boundary.

Those decisions intentionally keep the current implementation:

- single-process;
- local;
- static;
- non-distributed.

RFC-0012 defines the next trust and membership boundary:

```text
Only manually and statically declared remote nodes may be considered.
```

However, RFC-0012 explicitly does not define how a selected remote node is
reached, how a cluster request crosses to it, how failures are represented, or
what transport shape exists between the orchestrator and the remote node
boundary.

Without a minimal transport boundary, future implementation could accidentally
decide too much in code. It could make reachability act as trust, let transport
metadata own node identity, leak runtime-specific request formats into the
core, introduce retries or fallback as incidental behavior, or imply discovery,
registration, daemon lifecycle, or dynamic configuration.

The project needs a boring boundary that says what may cross to a selected
declared remote node before deciding a concrete protocol or implementing remote
execution.

## Goals

This RFC should:

- define the minimal remote transport boundary;
- build directly on RFC-0012's static remote node declaration boundary;
- allow transport only after routing has selected a manually and statically
  declared remote node;
- ensure unknown or undeclared machines are never contacted;
- keep the request crossing the boundary cluster-facing and normalized;
- keep runtime-specific request formats behind runtime adapters;
- keep node identity and metadata outside transport ownership;
- prevent the transport boundary from discovering, registering, creating,
  mutating, probing, or supervising nodes;
- prevent reachability from becoming trust;
- require either a normalized cluster result or normalized failure to return;
- keep failure normalization separate from retry or fallback policy;
- preserve static node availability, descriptive node health, and
  adapter-call-time runtime availability;
- leave concrete transport choice for a later decision.

## Non-goals

This RFC does not define:

- concrete protocol choice;
- HTTP endpoint design;
- node public API;
- daemon or process lifecycle;
- discovery;
- registration;
- dynamic configuration or config file format;
- authentication or transport security design;
- runtime probing;
- runtime supervision or auto-start;
- health polling;
- fallback or retries;
- scheduling policy;
- load balancing;
- dashboard;
- Docker;
- database;
- OpenAI-compatible API;
- model inventory;
- model placement or download automation;
- prompt or response logging by default;
- remote execution implementation;
- runtime-specific request formats in core;
- treating node id as address, credential, or cryptographic identity.

Future work in any of those areas requires a separate RFC.

## Proposal

Home AI Cluster should define a remote transport boundary as:

> The narrow boundary that may carry a normalized cluster request from the
> orchestrator to a selected manually declared remote node boundary and return
> either a normalized cluster result or a normalized transport or runtime
> failure.

The boundary may be used only after routing has selected a remote node that was
manually and statically declared according to RFC-0012.

The transport boundary does not decide which remote nodes exist.

It does not decide whether a remote node is allowed.

It does not decide whether a remote node is eligible for routing.

It does not own node identity, display name, availability, health,
capabilities, or declared adapter names.

Those remain cluster-facing node declaration concerns.

### Minimal flow

The minimal conceptual flow is:

```text
user request
  -> orchestrator endpoint
  -> normalized cluster request
  -> routing decision
  -> selected manually declared remote node
  -> remote transport boundary
  -> remote node boundary
  -> normalized cluster result or normalized failure
  -> user response
```

This flow is conceptual only.

It does not imply that remote transport exists in production code today.

It does not define a concrete protocol, endpoint path, process, server, or
daemon.

### Relationship to RFC-0012

RFC-0012 answers this question:

```text
Which non-local nodes may the orchestrator consider at all?
```

This RFC answers only this narrower follow-up:

```text
What boundary must exist before a routed request may cross to a selected
declared remote node?
```

The orchestrator must not use the transport boundary to contact unknown or
undeclared machines.

Unknown or undeclared machines must never be contacted as part of routing,
transport, probing, reachability checks, or execution.

Manual static declaration remains the trust boundary for considering a remote
node. Reachability must not become trust.

### Request boundary

The request crossing the remote transport boundary must be cluster-facing and
normalized.

It may represent the same kind of normalized cluster request that the
orchestrator already uses internally, including requested capability and the
request content needed to execute the selected work.

It must not be a runtime-specific request format.

The core must not send Ollama-shaped, llama.cpp-shaped, vLLM-shaped, MLX-shaped,
or other runtime-specific requests across this boundary as core transport
semantics.

Runtime-specific request formats remain behind runtime adapters.

### Result and failure boundary

The remote transport boundary must return one of:

- a normalized cluster result;
- a normalized transport failure;
- a normalized runtime failure.

A normalized cluster result is the cluster-facing result of the routed request.

A normalized transport failure describes failure to carry the normalized request
or response across the remote transport boundary.

A normalized runtime failure describes a runtime-side failure after the request
has crossed the remote node boundary and reached runtime adapter behavior.

Failure normalization must not introduce retry or fallback policy.

If a selected remote node cannot be reached, cannot answer, or returns a
failure, this RFC does not allow the router or transport to silently try another
node, another adapter, or another transport.

Retries, fallback, timeout policy, and user-facing error mapping require later
decisions.

### Relationship to nodes

Node identity and metadata must not be owned by the transport.

The transport boundary may be associated with a selected declared remote node
only because routing has already selected that node.

The transport must not create, discover, register, mutate, or enrich node
descriptions.

It must not turn a hostname, URL, socket, token, process, or reachable service
into a node.

It must not treat node id as an address, credential, cryptographic identity, or
registration token.

The minimal node model remains:

- `id`;
- `name`;
- `availability`;
- `health`;
- `capabilities`;
- `adapters`.

Those fields remain cluster-facing declaration metadata, not transport-owned
state.

### Relationship to availability and health

Availability remains static routing eligibility only, as defined by RFC-0010.

For a declared remote node, availability still answers only:

```text
May this declared remote node be considered by routing?
```

It does not prove reachability.

It does not prove health.

It does not prove runtime availability.

It does not imply retry or fallback behavior.

Health remains descriptive only.

The transport boundary must not introduce health polling, health-based routing,
or transport-derived health state.

### Relationship to runtime adapters

Runtime availability remains adapter-call-time behavior, as defined by
RFC-0007.

Runtime-specific details remain behind adapters, including:

- runtime endpoint URLs;
- runtime request formats;
- runtime-specific failures;
- runtime availability at call time;
- runtime process state;
- model names needed to execute a request.

The remote transport boundary may carry a normalized cluster request to a remote
node boundary. It must not become a runtime adapter and must not make the core
aware of runtime-specific request or response shapes.

### Relationship to protocol choice

This RFC does not choose HTTP or any other concrete transport.

A boring manual HTTP transport may be a reasonable later candidate because it is
understandable, inspectable, and compatible with the project's preference for
simple manual mechanisms before dynamic ones.

However, this RFC only defines the boundary such a transport would need to
satisfy.

A later RFC should decide whether HTTP is the smallest acceptable concrete
transport, what endpoint shape exists if any, and what minimal trust or
authentication assumptions are required once bytes cross machines.

## Rationale

This proposal keeps the project moving toward:

```text
One endpoint. Two machines. One routed request.
```

without deciding too much at once.

RFC-0012 deliberately defines who may be considered before defining how a remote
node is reached. This RFC keeps that layering intact by defining the crossing
boundary without choosing the concrete protocol.

The boundary preserves explicit user control. The orchestrator may only use it
after routing has selected a manually declared remote node. Unknown or
undeclared machines remain outside the cluster and must not be contacted.

The boundary preserves engine independence. The request crossing it is a
normalized cluster request, not a runtime-specific request. Runtime adapters
continue to own runtime details.

The boundary preserves privacy-first defaults. It does not introduce prompt or
response logging by default, telemetry, discovery scans, model inventory, or
extra machine inspection.

The boundary also keeps failure behavior boring. Returning a normalized failure
is allowed. Retrying somewhere else or falling back is not smuggled in as a
transport behavior.

## Alternatives considered

### Choose HTTP now

The project could decide that the first remote transport is manually configured
HTTP.

That may be the right later decision, but choosing it here would combine two
questions:

- what boundary must exist before a request crosses to a remote node;
- which concrete protocol satisfies that boundary first.

This RFC keeps those decisions separate.

### Define a node public API now

A remote node may eventually expose an endpoint that accepts work.

Defining that endpoint now would decide protocol shape, request shape, response
shape, compatibility expectations, and probably authentication assumptions
before the minimal transport boundary is agreed.

### Treat remote transport as a runtime adapter

The project could model a remote node as another adapter.

That would blur transport, node, and runtime responsibilities. It could make the
core think in terms of transport or runtime mechanics rather than declared
capabilities and node boundaries.

### Let transport discover reachable nodes

The transport could scan, probe, or accept any reachable machine.

That would make reachability act as trust and would conflict with RFC-0012.
Discovery and registration remain separate future decisions.

### Define remote execution implementation now

The project could define both the transport boundary and the implementation
needed to execute work remotely.

That would decide process shape, endpoint behavior, failure mapping, security
assumptions, and possibly runtime adapter placement too early.

This RFC defines only the boundary that future implementation must respect.

## Trade-offs

This RFC adds another architectural boundary before remote execution exists.

That may feel cautious, but it prevents important transport, trust, failure,
and runtime decisions from becoming hidden implementation details.

The RFC does not make the system more capable by itself. That is acceptable
because the project is still preparing the smallest two-machine proof.

Keeping the concrete protocol undecided means one more RFC is likely needed
before implementation can begin. That cost is acceptable because protocol,
endpoint, authentication, and remote execution choices affect long-term
compatibility and user trust.

The proposal also means a later transport implementation must normalize
transport failures without adding retries or fallback. This keeps behavior
simple, but it postpones resilience features until the project is ready to
define them explicitly.

## Impact

This RFC affects future Phase 3 architecture and implementation review.

It does not require production code changes.

It does not require public API changes.

It does not imply that remote transport exists in code today.

It does not change current single-process behavior.

It does not change node health, static node availability, runtime availability,
or runtime adapter boundaries.

If accepted, future work that introduces remote transport or remote execution
must preserve this rule:

```text
Only a selected manually and statically declared remote node may be contacted
through the remote transport boundary.
```

Future work that introduces concrete protocol choice, HTTP endpoints, node
public APIs, authentication, transport security, daemon lifecycle, discovery,
registration, dynamic configuration, remote execution implementation, retries,
fallback, health polling, runtime probing, runtime supervision, model inventory,
or prompt and response logging must be proposed separately.

## Open questions

- What concrete transport should satisfy this boundary?
- Is boring manual HTTP the smallest acceptable first transport?
- What minimal authentication or local trust assumption is required once bytes
  cross machines?
- What endpoint shape, if any, should a remote node expose later?
- How should remote transport failures be mapped to user-facing API errors?
- What is the smallest implementation that proves one endpoint, two machines,
  one routed request?

## Decision

Pending.
