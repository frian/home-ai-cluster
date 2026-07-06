# Phase 2 Current State

Status: Draft

This document describes the current Phase 2 implementation state.

It is descriptive, not a new architectural decision. Accepted RFCs remain the
source of architectural decisions.

## Accepted RFC references

This current state should be read against:

- [RFC-0004: Minimal node model](../RFC/RFC-0004-minimal-node-model.md);
- [RFC-0006: Node Health Boundary](../RFC/RFC-0006-node-health-boundary.md);
- [RFC-0007: Runtime Availability Boundary](../RFC/RFC-0007-runtime-availability-boundary.md);
- [RFC-0008: Phase 2 Node Boundary](../RFC/RFC-0008-phase-2-node-boundary.md);
- [RFC-0009: Static Local Node Announcement Boundary](../RFC/RFC-0009-static-local-node-announcement-boundary.md);
- [RFC-0010: Static Node Availability Boundary](../RFC/RFC-0010-static-node-availability-boundary.md);
- [RFC-0011: Minimal Agent Shape](../RFC/RFC-0011-minimal-agent-shape.md);
- [RFC-0012: Static Remote Node Declaration Boundary](../RFC/RFC-0012-static-remote-node-declaration-boundary.md);
- [RFC-0013: Minimal Remote Transport Boundary](../RFC/RFC-0013-minimal-remote-transport-boundary.md);
- [RFC-0014: Minimal Concrete Transport Protocol](../RFC/RFC-0014-minimal-concrete-transport-protocol.md).

## Current shape

Phase 2 currently remains:

- single-process;
- local;
- static;
- non-distributed.

The current flow is:

```text
API request
  -> core orchestrator
  -> router
  -> routing decision
  -> execution helper
  -> local execution path
  -> runtime adapter
  -> normalized cluster result
```

There are no remote nodes, node transports, discovery mechanisms, registration
protocols, or independent node lifecycles in the current implementation.

Phase 2 now has an accepted static remote node declaration boundary, but the
current implementation still has no remote nodes, transport, discovery,
registration, config file, reachability proof, remote execution, or
trust/authentication mechanism.

Phase 2 now has an accepted minimal remote transport boundary, but the current
implementation still has no remote transport, concrete protocol, HTTP endpoint,
node public API, authentication model, daemon lifecycle, discovery,
registration, dynamic configuration, retries, fallback, health probing, runtime
supervision, or remote execution.

Phase 2 now has an accepted minimal concrete transport protocol. RFC-0014
chooses manual local-network HTTP as the first concrete transport/protocol
boundary, using the internal endpoint `POST /internal/cluster/request` to carry
normalized cluster requests and return normalized cluster results or normalized
failures. That endpoint may only be used for manually and statically declared
remote nodes. Unknown or undeclared machines must never be contacted. The
current implementation still has no remote transport or remote execution, and
RFC-0014 does not define discovery, registration, authentication, TLS, retries,
fallback, health probing, daemon lifecycle, streaming, or a public node API.

Phase 2 has an accepted minimal agent boundary, but the current implementation
does not include a separate `Agent` object, daemon, protocol endpoint, discovery
participant, runtime supervisor, configuration system, or runtime-derived
metadata source.

## Current remote-preparation seams

The current implementation has small remote-preparation seams that describe
boundaries without implementing remote behavior.

`RemoteTransport` exists only as a protocol boundary for carrying normalized
cluster objects. `RemoteTransportError` exists as a generic normalized transport
failure boundary.

`RemoteNodeDeclaration` represents a manually and statically declared remote
node. It keeps `transport_address` as transport metadata separate from
`NodeDescription`; the address is not node identity, proof of trust, discovery,
or registration. `RemoteNodeDeclarationRegistry` is a static in-memory holder
for those declarations.

`remote_declaration_for_routing_decision()` can resolve a declaration by the
selected `decision.node.id`.

None of these seams are wired into routing, orchestration, API routes, HTTP
transport, or remote execution.

## Current execution seam

`execute_routing_decision()` is the current post-routing execution entry point.
It currently delegates to `execute_local_routing_decision()`.

`execute_local_routing_decision()` calls the selected local adapter.

There is no remote execution branch yet.

## Current node boundary

The node boundary is explicit.

Static node boundary helpers exist and make the cluster-facing node description
visible in code.

The static local node announcement is explicit in wiring code. For now, the
announcement is manually declared. It describes cluster-facing metadata only,
including node identity, display name, availability, descriptive health,
declared capabilities, and declared adapter names.

The node announcement is not discovered dynamically, derived from live runtime
probing, owned by runtime adapters, or loaded from a file-based configuration
format.

## Current availability semantics

Node availability means static declared routing eligibility.

Availability is part of the static node announcement and is manually declared
for now.

Current routing behavior is:

- nodes with `availability == "available"` are considered by routing;
- nodes with `availability == "unknown"` are not considered by routing;
- nodes with `availability == "unavailable"` are not considered by routing.

Availability is not node health, adapter health, runtime availability, runtime
probing, discovery state, or dynamic node state.

## Current health and runtime boundaries

Node health is descriptive only.

Node health does not drive routing, fallback, retries, polling, supervision, or
adapter selection.

Adapter health is not preflighted during routing.

Runtime availability remains adapter-call-time behavior. If a selected runtime
adapter cannot reach or use its runtime, the adapter normalizes the
runtime-specific failure before it reaches the public API boundary.

Runtime-specific details remain behind adapters, including endpoint URLs,
request formats, model naming, runtime process state, and runtime-specific
errors.

## Current test coverage

Router tests cover static node availability as routing eligibility. They
document that an available static node with the requested capability can be
selected, an unavailable static node is ignored, and routing fails clearly when
no available node matches.

Router tests also cover the runtime adapter selection boundary. They document
that routing only considers adapters declared by the selected node, registry
adapters that are not declared by the selected node are not selected, missing
declared adapters fail clearly, declared adapters without the requested
capability fail clearly, and routing explanations remain runtime-neutral.

Route tests exercise the FastAPI app in-process through `httpx.AsyncClient`
with `ASGITransport`. They use test doubles for node lookup and runtime
adapters rather than calling a real runtime adapter.

Remote transport boundary tests cover the `RemoteTransport` protocol shape and
`RemoteTransportError` propagation.

Remote node tests cover remote node declarations and the static in-memory remote
node declaration registry.

Executor tests cover the explicit local execution path after routing.

Execution target helper tests cover resolving a remote node declaration from a
selected routing decision without calling adapters, transport, routing, or
execution behavior.

These tests document the current implementation state. They do not introduce
node or cluster networking, discovery, persistence, distributed behavior, or a
new public API.

## Still out of scope

Phase 2 currently does not include:

- remote nodes;
- node HTTP API;
- discovery;
- registration protocol;
- daemon or agent process;
- runtime probing;
- fallback;
- retries;
- health polling;
- runtime supervision;
- file-based config;
- database;
- dashboard;
- Docker;
- API compatibility layer;
- model inventory;
- model placement automation;
- public API changes.

Those remain outside the current implementation unless a future accepted RFC
defines their boundary.
