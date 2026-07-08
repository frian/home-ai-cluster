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
- [RFC-0014: Minimal Concrete Transport Protocol](../RFC/RFC-0014-minimal-concrete-transport-protocol.md);
- [RFC-0015: Static Remote Declaration Source Boundary](../RFC/RFC-0015-static-remote-declaration-source-boundary.md);
- [RFC-0016: Declared Remote Routing Eligibility Boundary](../RFC/RFC-0016-declared-remote-routing-eligibility.md).

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

There are no remote nodes, discovery mechanisms, registration protocols, or
independent node lifecycles in the current implementation.

Phase 2 now has an accepted static remote node declaration boundary, but the
current implementation still has no remote nodes, discovery, registration,
config file, reachability proof, active remote execution, or trust mechanism.

Phase 2 now has an accepted minimal remote transport boundary and a concrete
HTTP transport implementation. The implementation remains opt-in and un-wired:
there is no active remote execution, node public API, daemon lifecycle,
discovery, registration, dynamic configuration, retries, fallback, health
probing, runtime supervision, or active remote routing.

Phase 2 now has an accepted minimal concrete transport protocol. RFC-0014
chooses manual local-network HTTP as the first concrete transport/protocol
boundary, using the internal endpoint `POST /internal/cluster/request` to carry
normalized cluster requests and return normalized cluster results or normalized
failures. That endpoint may only be used for manually and statically declared
remote nodes. Unknown or undeclared machines must never be contacted. The
current implementation exposes that endpoint as a thin local handler and has an
opt-in `HttpRemoteTransport` client implementation, but it still has no active
remote execution. RFC-0014 does not define discovery, registration, retries,
fallback, health probing, daemon lifecycle, streaming, or a public node API.

Phase 2 has an accepted minimal agent boundary, but the current implementation
does not include a separate `Agent` object, daemon, protocol endpoint, discovery
participant, runtime supervisor, configuration system, or runtime-derived
metadata source.

## Current remote-preparation seams

The current implementation has small remote-preparation seams that describe
boundaries without activating remote behavior.

`RemoteTransport` exists as the protocol boundary for carrying normalized
cluster objects. `RemoteTransportError` exists as a generic normalized transport
failure boundary.

`HttpRemoteTransport` is the concrete RFC-0014 HTTP transport implementation. It
posts a normalized `ClusterRequest` to the declared node's
`POST /internal/cluster/request` endpoint and validates the response as a
normalized `ClusterResult`. HTTP failures and invalid result payloads are raised
as `RemoteTransportError`.

`HttpRemoteTransport` receives an existing `httpx.AsyncClient` from its caller.
It does not own client lifecycle, configuration loading, discovery, retries,
fallback, or health probing.

`RemoteNodeDeclaration` represents a manually and statically declared remote
node. It keeps `transport_address` as transport metadata separate from
`NodeDescription`; the address is not node identity, proof of trust, discovery,
or registration. `RemoteNodeDeclarationRegistry` is a static in-memory holder
for those declarations.

`build_remote_node_declaration_registry(...)` can assemble an in-memory
`RemoteNodeDeclarationRegistry` from explicit caller-owned
`RemoteNodeDeclaration` values. This supports the existing opt-in orchestration
seams without adding config loading, environment loading, discovery,
registration, persistence, daemon-owned registry state, API route changes, or
`/v1/chat` remote activation.

`declared_remote_declarations_for_request(...)` can identify declared remote
declarations eligible for a request from a caller-owned
`RemoteNodeDeclarationRegistry`. Eligibility is based on the declaration's node
supporting the requested capability and being statically available. It does not
use `AdapterRegistry`, require a local runtime adapter, call adapters, call
transports, perform network I/O, change `route_request()`, change
`RoutingDecision`, change execution behavior, or activate `/v1/chat` remote
execution.

`DeclaredRemoteRoutingCandidate` is a declared-remote-specific routing
candidate shape. It is separate from the existing local `RoutingDecision` and
carries the selected node, selected declaration, requested capability, and
reason.

`declared_remote_routing_candidate_for_request(...)` selects the first eligible
declared remote declaration for a request and returns `None` when no declared
remote declaration is eligible. It does not require `AdapterRegistry`, require a
local runtime adapter, call adapters, call transports, perform network I/O,
change `route_request()`, change `RoutingDecision`, change execution behavior,
wire orchestration, or activate `/v1/chat` remote execution.

`remote_declaration_for_routing_decision()` can resolve a declaration by the
selected `decision.node.id`.

`execute_declared_routing_decision()` is an explicit opt-in execution helper
for future remote wiring. It resolves a `RemoteNodeDeclaration` for the
selected routing decision node. When a matching declaration exists, it delegates
to `execute_remote_routing_decision()`. When no matching declaration exists, it
delegates to `execute_local_routing_decision()`.

`orchestrate_request_with_declared_remote()` is an explicit opt-in
orchestration helper for future remote wiring. It routes the request using the
existing `route_request()` flow, then executes the resulting `RoutingDecision`
through `execute_declared_routing_decision()`. When no matching
`RemoteNodeDeclaration` exists, it uses local execution. When a matching
declaration exists, it uses the provided `RemoteTransport`.

`orchestrate_request_with_declared_http_remote()` is an explicit opt-in
orchestration helper for future HTTP remote wiring. It receives an existing
`httpx.AsyncClient` from the caller, wraps it in `HttpRemoteTransport`, and then
uses `orchestrate_request_with_declared_remote()`.

These helpers are not wired into API routes or the active `/v1/chat` execution
path.

## Current execution seam

`execute_routing_decision()` is the current post-routing execution entry point.
It currently delegates only to `execute_local_routing_decision()`.

`execute_local_routing_decision()` calls the selected local adapter.

`execute_remote_routing_decision()` delegates to an explicit
`RemoteTransport.send(request, declaration)` call.

`execute_declared_routing_decision()` can choose between the explicit local and
remote execution helpers based on whether the selected routing decision node has
a matching remote declaration. This is a prepared seam for future explicit
remote wiring. It is not the active execution path.

The active `/v1/chat` behavior is unchanged and remains local-only through
`execute_routing_decision()`.

## Current orchestration seam

`orchestrate_request()` remains the active local-only orchestrator path. It
routes the request with `route_request()` and executes the selected routing
decision through `execute_routing_decision()`.

`orchestrate_request_with_declared_remote()` composes the existing routing flow
with the explicit declared execution helper. It requires a
`RemoteNodeDeclarationRegistry` and `RemoteTransport` from the caller. It is a
prepared seam for future explicit remote wiring, not active behavior.

`orchestrate_request_with_declared_http_remote()` composes the declared remote
orchestration helper with the concrete `HttpRemoteTransport`. It requires a
`RemoteNodeDeclarationRegistry` and an existing `httpx.AsyncClient` from the
caller. It does not own HTTP client lifecycle, configuration loading, discovery,
registration, retries, fallback, or health probing.

The active `/v1/chat` route does not call
`orchestrate_request_with_declared_remote()` or
`orchestrate_request_with_declared_http_remote()`.

## Current internal endpoint

`POST /internal/cluster/request` exists as the minimal RFC-0014 internal
transport endpoint shape.

For now, it is a thin local handler. It accepts a normalized `ClusterRequest`,
uses the same static local wiring as `/v1/chat`, calls the active local-only
`orchestrate_request()` path, and returns a normalized `ClusterResult`.

The internal endpoint does not activate remote execution. It does not call
`orchestrate_request_with_declared_remote()`. It does not perform remote node
lookup, discovery, registration, retry, fallback, health probing, daemon
lifecycle, streaming, or runtime supervision.

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
adapters rather than calling a real runtime adapter. They cover both the public
`/v1/chat` route and the internal `POST /internal/cluster/request` route.

Remote transport boundary tests cover the `RemoteTransport` protocol shape,
`RemoteTransportError` propagation, the `HttpRemoteTransport` request shape,
result validation, normalized HTTP transport failures, and an in-process
transport-to-endpoint proof through `httpx.ASGITransport`.

The in-process transport-to-endpoint proof verifies that `HttpRemoteTransport`
uses the declared `RemoteNodeDeclaration.transport_address`, posts to
`POST /internal/cluster/request`, exercises the FastAPI app without real network
I/O, and returns a normalized `ClusterResult`.

Remote node tests cover remote node declarations, the static in-memory remote
node declaration registry, and declared remote eligibility. Declared remote
eligibility tests cover an available matching declaration, missing capability,
`unknown` availability, `unavailable` availability, no local adapter
requirement, and declaration order preservation.

Remote node tests also cover declared remote routing candidate selection,
including first eligible declaration selection, returned node, declaration,
capability, and reason, no-match behavior, `unknown` and `unavailable`
filtering, no local adapter requirement, and declaration order preservation.

Executor tests cover the explicit local execution path after routing, the
current local-only `execute_routing_decision()` entry point, the explicit remote
transport execution helper, and the explicit declared execution helper's local
and remote branches.

Orchestrator tests cover the active local-only `orchestrate_request()` path, the
explicit declared remote orchestration helper's local and remote branches, and
the explicit declared HTTP remote orchestration helper's composition of
`HttpRemoteTransport` with a caller-provided `httpx.AsyncClient`.

Orchestrator tests also prove that the explicit opt-in declared remote
orchestration seam can target a statically declared remote node with an id
distinct from the local node id, using a caller-owned declaration registry and a
provided `RemoteTransport`.

Orchestrator tests also include an in-process proof for the full explicit HTTP
remote orchestration seam. That proof exercises
`orchestrate_request_with_declared_http_remote()` through `HttpRemoteTransport`
and the internal `POST /internal/cluster/request` endpoint using
`httpx.ASGITransport`, without real network I/O or active `/v1/chat` remote
wiring.

Execution target helper tests cover resolving a remote node declaration from a
selected routing decision without calling adapters, transport, routing, or
execution behavior.

These tests document the current implementation state. They do not introduce
active node or cluster networking, discovery, persistence, distributed behavior,
or a new public API.

## Still out of scope

Phase 2 currently does not include:

- remote nodes;
- remote execution active in `/v1/chat`;
- active remote execution through `POST /internal/cluster/request`;
- node HTTP API;
- public node API;
- discovery;
- registration protocol;
- remote node routing;
- daemon or agent process;
- runtime probing;
- fallback;
- retries;
- fallback or retry policy;
- health polling;
- runtime supervision;
- file-based config;
- config loading;
- streaming;
- database;
- dashboard;
- Docker;
- OpenAI-compatible API;
- API compatibility layer;
- model inventory;
- model placement automation;
- public API changes.

Those remain outside the current implementation unless a future accepted RFC
defines their boundary.
