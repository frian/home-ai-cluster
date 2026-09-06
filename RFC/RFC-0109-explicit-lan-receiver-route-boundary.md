# RFC-0109: Explicit LAN Receiver Route Boundary

Status: Accepted

Date: 2026-09-05

Author: frian

## Summary

Home AI Cluster defines an explicit route-ownership boundary for an ordinary HAC composition that is deliberately exposed beyond loopback in order to receive requests from another HAC machine.

The accepted remote-cluster surface should remain exactly:

```text
POST /internal/cluster/request
GET  /internal/cluster/status
```

A HAC network surface exposed for the remote-receiver role must not thereby expose unrelated local/native execution routes such as:

```text
POST /v1/chat
POST /v1/chat/sources
POST /v1/summarize
POST /v1/classify
POST /internal/chat/external-information-decision
```

It must also not expose framework-generated or browser-oriented routes merely because the receiver reuses ordinary application machinery.

This RFC defines route ownership and exposure only.

It does not define authentication, credentials, TLS, a new daemon, a new transport protocol, a new remote API, or a second cluster architecture.

It does not decide whether the implementation uses one listener, multiple listeners, one FastAPI application object, multiple FastAPI application objects, or another small process-local representation.

The purpose is to establish the smallest honest receiver surface before any later authentication decision.

## Problem

Home AI Cluster 1.0 has a deliberately simple static remote architecture.

A calling HAC process may route one normalized cluster request to an explicitly declared remote HAC application using:

```text
POST /internal/cluster/request
```

and may inspect its bounded local status through:

```text
GET /internal/cluster/status
```

The receiving machine uses the same HAC local composition and local node semantics as ordinary local execution.

Current implementation reuses one FastAPI application containing both:

- local/native request routes;
- caller-local internal routes;
- HAC-to-HAC internal routes.

When an operator deliberately binds that application beyond loopback so another HAC machine can reach the receiver, the entire mounted route set becomes reachable on that listener.

Conceptually:

```text
LAN peer
   |
   v
ordinary HAC application
   |
   +-- POST /internal/cluster/request
   +-- GET  /internal/cluster/status
   |
   +-- POST /v1/chat
   +-- POST /v1/chat/sources
   +-- POST /v1/summarize
   +-- POST /v1/classify
   |
   +-- POST /internal/chat/external-information-decision
   |
   +-- framework/application routes
```

The `/internal/` prefix is only route naming.

It is not an access-control or listener boundary.

Therefore a remote peer that can reach the exposed receiver does not need to use the cluster transport route in order to cause local model execution.

It may call an unrelated native execution route directly.

This makes a narrow future authentication rule on only `/internal/cluster/*` incomplete.

Before choosing credentials or authentication, Home AI Cluster needs to decide which routes belong to the remote-receiver authority at all.

## Existing Accepted Boundaries

This RFC preserves the existing accepted architecture.

### Static remote membership

Static remote declarations remain explicit caller-owned topology.

A declared remote means that the caller is authorized to consider and contact that target.

It does not make reachability into trust.

It does not establish cryptographic identity.

### Remote transport

The existing remote transport boundary carries normalized cluster requests and results.

The concrete first transport remains HTTP.

The cluster-owned remote request route remains:

```text
POST /internal/cluster/request
```

### Remote status

The cluster-owned remote status route remains:

```text
GET /internal/cluster/status
```

Status remains bounded observation.

It does not become a management, discovery, registration, or runtime-control API.

### Native request surfaces

The existing `/v1/*` request routes remain native HAC caller edges.

They were established for ordinary local/native access.

This RFC does not redefine them as remote-cluster APIs.

### Caller-local internal routes

Routes such as:

```text
POST /internal/chat/external-information-decision
```

remain caller-local implementation boundaries.

An `/internal/` path prefix alone does not make a route part of the HAC-to-HAC transport contract.

### Runtime ownership

Runtime processes remain operator-owned.

This RFC does not expose runtime endpoints or runtime-specific payloads to remote callers.

## Accepted Route-Ownership Decision

Home AI Cluster distinguishes between:

```text
ordinary local/native route ownership
```

and:

```text
remote HAC receiver route ownership
```

The remote HAC receiver surface is a closed route set containing exactly the existing cluster-owned routes:

```text
POST /internal/cluster/request
GET  /internal/cluster/status
```

No other existing route becomes remotely owned merely because the same process or application machinery is reachable beyond loopback.

## Receiver Route Set

The accepted remote receiver route set is closed.

It contains exactly two routes.

### Request execution

```text
POST /internal/cluster/request
```

This route accepts one normalized internal HAC request and executes it through the receiving machine's local HAC composition.

### Status observation

```text
GET /internal/cluster/status
```

This route returns the existing bounded receiver-local status representation.

The route set does not implicitly expand when:

- new native routes are added;
- new caller-local internal routes are added;
- browser routes are added;
- FastAPI or another framework provides generated documentation or schema routes;
- another local operator surface is added.

Any future route intended for remote HAC callers requires an explicit architectural decision.

## Routes Outside the Receiver Authority

Every route not explicitly listed in the closed receiver route set is outside remote HAC receiver authority.

### Native execution routes

```text
POST /v1/chat
POST /v1/chat/sources
POST /v1/summarize
POST /v1/classify
```

These remain native HAC caller edges.

They must not become supported LAN receiver APIs merely because another HAC route is exposed from the same process.

### Caller-local decision routes

```text
POST /internal/chat/external-information-decision
```

This remains a caller-local internal execution boundary.

Its path prefix does not make it remote-cluster traffic.

### Browser routes and assets

Browser routes, browser assets, and browser-oriented application surfaces remain outside remote receiver authority.

This RFC does not define remote browser access.

### Framework-generated routes

Framework-generated application routes remain outside remote receiver authority.

For the current FastAPI implementation, this includes surfaces such as:

```text
/docs
/redoc
/openapi.json
```

The receiver boundary must not acquire these routes merely because a default FastAPI application would normally expose them.

This RFC does not establish those exact framework paths as long-term architecture.

The architectural rule is:

> Framework defaults do not expand the closed receiver route set.

### Compatibility API

The separately accepted OpenAI-compatible listener remains outside this RFC.

This RFC does not add authentication or LAN exposure to it.

## Exposure Invariant

When HAC is intentionally made reachable beyond loopback for the remote-receiver role:

> A remote network peer must only be able to exercise routes that belong to the accepted closed remote receiver route set.

The implementation must not require operators to expose unrelated local/native execution surfaces merely to enable HAC-to-HAC communication.

This is a route-exposure and authority invariant.

It is not yet an authentication guarantee.

A reachable peer may still invoke the accepted receiver routes until a later authentication decision says otherwise.

Therefore:

```text
receiver route isolation
!=
request authentication
```

and:

```text
receiver route isolation
!=
authorization credential
```

and:

```text
receiver route isolation
!=
transport confidentiality
```

## One HAC Composition and Node Remain One

This RFC preserves:

```text
one HAC process-level composition
one cluster-visible local node
one local execution composition
```

It does not create a fake receiver node.

It does not create another cluster member.

It does not require a second local runtime composition.

It does not require another orchestrator.

Conceptually:

```text
one HAC process/composition
one local node
one local execution composition
        |
        +-- local/native authority
        |
        +-- bounded remote receiver authority
```

The distinction is route authority, not node identity.

The representation of those route authorities is deliberately not decided here.

In particular, this RFC does not require or forbid:

```text
one ASGI application object
multiple ASGI application objects

one listener
multiple listeners

one port
multiple ports
```

Those are implementation choices subject to the accepted exposure invariant.

A later implementation should choose the smallest boring representation that preserves one HAC composition and one node while keeping the receiver route set closed.

## No New Transport

The accepted remote transport remains HTTP.

This RFC does not replace it with:

- SSH;
- gRPC;
- WebSocket;
- raw TCP;
- a message broker;
- a VPN protocol.

The existing normalized remote request and result contracts remain unchanged.

## No New Receiver Protocol

The remote caller continues to use:

```text
POST /internal/cluster/request
GET  /internal/cluster/status
```

No request schema changes are authorized.

No result schema changes are authorized.

No new remote handshake is authorized.

No remote route discovery is authorized.

## Implementation Shape

This RFC defines semantics, not exact FastAPI, ASGI, listener, or socket construction.

A later implementation must preserve:

```text
same HAC local composition
same local node identity
same runtime adapter ownership
same normalized receiver contracts
```

while making remote receiver reachability equivalent to the closed receiver route set.

A possible implementation might compose route sets explicitly.

Another possible implementation might use separate process-local application or listener representations.

Neither is selected by this RFC.

The implementation must not introduce, merely to satisfy this decision:

- a new cluster node;
- a new runtime composition;
- a new orchestrator;
- a generic router registry;
- a route-policy framework;
- a general listener framework.

The implementation agent should prefer the smallest concrete mechanism supported by repository evidence.

## Listener and Port Scope

This RFC does not require a new port.

It does not require keeping the receiver on the same port as any local/native surface.

It does not require one listener.

It does not require multiple listeners.

Port and listener representation remain implementation decisions.

The first proof must demonstrate the architectural reachability property rather than assuming that a particular port layout provides it.

Creating a new daemon, independently managed service lifecycle, service-discovery mechanism, or general multi-listener configuration system is not authorized.

## Local Behavior Compatibility

Existing ordinary loopback local/native behavior remains supported.

The intended compatibility boundary is:

- native `/v1/*` caller behavior remains available through its accepted local/loopback authority;
- caller-local internal behavior remains available where its existing local contract requires it;
- existing browser behavior remains local according to its accepted boundary;
- existing local runtime composition remains unchanged;
- existing local node identity remains unchanged;
- existing local model execution semantics remain unchanged.

This RFC does not remove native routes.

It does not redefine their request or response schemas.

However, this RFC deliberately does **not** preserve accidental LAN reachability of native routes obtained by exposing an ordinary receiver listener beyond loopback.

Such LAN exposure is not treated as an accepted compatibility contract.

Therefore this RFC intentionally tightens remote network exposure while preserving accepted local/native behavior.

## Remote Behavior Compatibility

Existing HAC-to-HAC callers continue to use the same remote origin and fixed cluster-owned paths.

No remote declaration field changes.

No node model changes.

No capability model changes.

No remote request model changes.

No remote response model changes.

No routing changes.

No fallback changes.

No attribution changes.

A receiver remains the same cluster-visible local node even if the concrete server representation used to expose its receiver routes changes.

## Relationship to Authentication

This RFC is a prerequisite for, not an implementation of, receiver authentication.

Once the receiver route boundary is explicit, a later RFC may ask the much smaller question:

> Should access to the bounded receiver route set require receiver-owned authorization material?

That later work can reason about exactly:

```text
POST /internal/cluster/request
GET  /internal/cluster/status
```

without accidentally creating general authentication for every native HAC route.

This RFC therefore explicitly defers:

- shared secrets;
- bearer credentials;
- HMAC;
- TLS requirements;
- mutual TLS;
- credential files;
- secret persistence;
- credential rotation;
- credential generation;
- authentication failure contracts.

## Relationship to Trusted LAN

The current trusted-LAN assumption remains unchanged.

This RFC does not claim to make plain HTTP confidential.

It does not protect prompts or results from network observation.

It does not authenticate callers.

It does not authenticate receivers.

It only narrows remote network exposure and makes receiver authority explicit.

## Relationship to Future Secure Networks

Operators may continue to place HAC traffic inside an operator-owned authenticated or encrypted network boundary.

This RFC does not integrate with or depend on any VPN, overlay network, reverse proxy, firewall product, or certificate system.

Those remain outside HAC ownership.

## Relationship to Execution-Permission Admission

This RFC is independent of the accepted execution-availability and
execution-permission rail, including RFC-0098 through RFC-0106. Route
ownership decides neither execution availability nor execution permission.

For a request that reaches the receiver route, the existing conceptual order
remains:

```text
remote request
   -> receiver route
   -> future authentication/admission if later accepted
   -> HAC execution-permission admission
   -> local execution
```

Receiver route ownership remains outside and before those existing admission
boundaries. It creates no execution slot, capacity, scheduling, polling,
availability advertisement, load sharing, or per-route capacity semantics.

## Relationship to RFC-0108 and RFC-0110 Binding Ownership

RFC-0108 and RFC-0110 are accepted. Their binding ownership is
receiver/process-local execution truth; this RFC's receiver route ownership
decides which HAC routes may be reachable through remote receiver authority.
The two decisions remain independent.

The receiver still receives one normalized capability request through:

```text
POST /internal/cluster/request
```

and privately resolves that capability through its current local HAC
composition.

No local binding identity, runtime identity, model identity, or adapter identity becomes remotely visible.

## Relationship to the Accepted vLLM Adapter Boundary

This RFC is runtime-independent.

A receiver may use any accepted concrete runtime composition, including the
accepted vLLM adapter boundary, behind its local HAC boundary.

No vLLM-native or other runtime-specific route becomes remote HAC receiver
authority.

## Status Route

`GET /internal/cluster/status` remains part of the receiver route set because it is already the accepted cluster-owned remote observation surface.

Route membership does not mean every local composition has a successful status
representation. This RFC does not change the existing observation semantics.
In particular, RFC-0110 deliberately fails closed when a multi-adapter
composition reaches the unsupported internal status surface; RFC-0109 preserves
that boundary rather than aggregating or selecting an adapter.

This RFC does not broaden the status response.

It does not add:

- model inventory;
- runtime details beyond the accepted status shape;
- binding details;
- execution counts;
- authentication state;
- credentials.

A later authentication RFC may decide whether status and execution share one admission boundary.

## Failure Semantics

Route isolation must fail closed.

A route outside the receiver route set must not become executable remotely through accidental application composition.

The exact HTTP result for a remote attempt to reach a route outside the closed receiver surface is an implementation detail for the first proof, provided:

- the route cannot execute;
- it does not expose another HAC surface;
- the result does not leak private application details.

The implementation does not need to distinguish whether a non-receiver route exists on some local-only surface.

This RFC does not introduce a new cluster failure taxonomy.

It does not change RFC-0028 fallback behavior.

It does not add retry.

## Preflight

Preflight remains network-free.

This RFC does not authorize preflight to probe receiver routes.

A later implementation may statically validate a receiver route composition if necessary, but must not contact the network.

## Configuration

This RFC does not define new retained configuration.

It does not add:

- receiver profiles;
- route lists;
- configurable route allowlists;
- general listener configuration;
- stored authentication state.

The receiver route set is cluster-owned and fixed by architecture.

Operators do not configure which individual cluster routes belong to receiver authority.

This avoids turning route ownership into a policy framework.

## Exposure and Security Boundary

This RFC narrows remote network exposure and makes remote receiver authority explicit.

It establishes:

```text
remote receiver authority
=
closed cluster-owned receiver route set
```

It does not establish:

```text
authenticated peer
authorized cryptographic identity
confidential transport
integrity against network attackers
replay resistance
Internet-safe service
```

After this RFC alone, a network peer that can reach the receiver may still invoke:

```text
POST /internal/cluster/request
```

because authentication has not yet been decided.

Therefore documentation and later work must not describe this route boundary as secure HAC-to-HAC transport.

## First Implementation Proof

If accepted, this RFC should authorize one bounded implementation proof.

The proof should establish both local compatibility and remote receiver isolation.

### Local/native proof

Using the ordinary local/native application boundary, prove that accepted local routes remain available according to their existing loopback contract.

At minimum, ordinary native execution behavior must remain representable.

The proof does not need to exhaustively retest every feature already covered elsewhere.

### Receiver proof

Using the receiver route surface, prove that:

```text
POST /internal/cluster/request              available
GET  /internal/cluster/status               available

POST /v1/chat                               unavailable
POST /v1/chat/sources                       unavailable
POST /v1/summarize                          unavailable
POST /v1/classify                           unavailable
POST /internal/chat/external-information-decision
                                             unavailable

/docs                                       unavailable
/redoc                                      unavailable
/openapi.json                               unavailable
```

The proof should additionally demonstrate:

1. a valid remote internal cluster request still executes normally;
2. remote status still works normally for an already status-supported
   single-adapter composition;
3. the receiver uses the same local HAC composition intended for local execution;
4. the same cluster-visible local node identity is preserved;
5. no second runtime composition is introduced;
6. no second orchestrator is introduced;
7. no authentication is introduced;
8. no TLS decision is introduced;
9. remote request and status schemas remain unchanged;
10. caller-side remote transport remains unchanged;
11. adding or mounting another native route does not automatically expand the receiver route set.

The proof must not require successful multi-binding status or introduce adapter
aggregation, binding aggregation, adapter selection, binding status, or
multi-adapter status response fields.

The first proof may use in-process FastAPI/ASGI test construction.

It need not choose final operator CLI or service lifecycle.

A real two-machine proof is not required until the implementation boundary is clear.

## Alternatives Considered

### Authenticate only `/internal/cluster/request`

Rejected as the first step.

If unrelated execution-capable routes remain reachable on the same LAN surface, an unauthorized peer can bypass the protected cluster envelope.

Authentication should be applied only after the receiver authority itself is explicit.

### Authenticate every execution-capable route

Rejected from this RFC.

That would turn the problem into general native API authentication.

The current need is narrower: HAC-to-HAC receiver authority.

### Keep the current entire application exposed

Rejected as the intended receiver architecture.

It makes implementation reuse accidentally define network authority.

A route being present in the same FastAPI application does not mean it should become part of the remote HAC contract.

### Require one FastAPI application

Rejected as an architectural requirement.

Application-object composition is an implementation detail and may conflict with simultaneously preserving loopback-native access and a closed LAN receiver surface.

### Add a completely separate receiver daemon

Rejected from the first scope.

It adds lifecycle, startup, configuration, service management, and operational concepts before they are needed.

### Require a separate receiver port immediately

Not required.

Port separation may prove to be the smallest implementation, but this RFC does not decide that in advance.

### Require a single listener

Not required.

A single-listener design may or may not satisfy the accepted exposure and local-compatibility invariants cleanly.

### Add configurable route allowlists

Rejected.

The cluster receiver route set is project-owned and fixed.

Operators should not need to design an HTTP security policy.

### Rely only on firewall rules

Operator firewalls may provide additional protection, but they cannot define HAC route ownership.

HAC should not require an operator to expose a whole application and then reconstruct its intended route contract externally.

### Add authentication and route isolation together

Rejected.

These are separate decisions:

```text
what may a remote peer reach?
```

and:

```text
who may use what it can reach?
```

The first should be decided before the second.

## Trade-offs

Explicit route ownership introduces another application-composition distinction.

That adds a small amount of implementation complexity.

In return:

- remote HAC authority becomes explainable;
- native local APIs remain local by design;
- future authentication has a bounded target;
- exposure claims become more honest;
- no generic API authentication system is required;
- the cluster protocol remains unchanged.

The project may end up with more than one process-local HTTP/ASGI route composition built from common HAC execution components.

That is acceptable.

It does not mean multiple HAC nodes, multiple orchestrators, or multiple runtime compositions.

Some duplication is preferable to a generic route-policy abstraction unless implementation evidence proves a smaller shared representation.

## Non-goals

This RFC does not define or add:

- authentication;
- authorization credentials;
- API keys;
- bearer tokens;
- HMAC;
- TLS policy;
- certificate management;
- mutual TLS;
- public Internet support;
- secrets management;
- secret generation;
- secret persistence;
- user accounts;
- sessions;
- cookies;
- RBAC;
- ACLs;
- discovery;
- registration;
- dynamic membership;
- node identity changes;
- cryptographic node identity;
- new remote protocol;
- new remote request schema;
- new remote response schema;
- new remote status schema;
- runtime-specific remote APIs;
- runtime discovery;
- model discovery;
- scheduler;
- load balancing;
- queue;
- retries;
- fallback changes;
- new execution-availability semantics;
- new capability semantics;
- multiple local binding semantics;
- browser login;
- OpenAI-compatible API authentication;
- configurable route allowlists;
- generic middleware policy frameworks;
- generic listener frameworks;
- daemon management;
- service installation;
- database;
- dashboard;
- Docker;
- Kubernetes.

## Impact

Acceptance authorizes only the bounded receiver-route implementation proof.

It does not authorize authentication implementation.

It does not authorize new secrets or retained configuration.

It does not change released HAC 1.0 behavior until a separate implementation is reviewed and later released.

It does intentionally establish that accidental LAN availability of native routes through a LAN-bound receiver is not a compatibility contract that future implementations must preserve.


## Open Questions

No architectural question remains within the route-ownership boundary itself.

The following remain implementation decisions:

- one or multiple ASGI application objects;
- one or multiple listeners;
- one or multiple ports;
- router composition details.

Those choices must satisfy the accepted exposure invariant without introducing a second HAC node, runtime composition, or orchestrator.

Authentication, credential ownership, TLS, secret transport, failure contracts, and real two-machine security proof remain separate future architectural decisions.

## Decision

Accepted. A HAC composition deliberately exposed for remote HAC receiving may
make remotely reachable only the fixed cluster-owned routes:

```text
POST /internal/cluster/request
GET  /internal/cluster/status
```

Unrelated native, caller-local, browser, compatibility, framework-generated,
and runtime surfaces remain outside that remote authority.

One HAC composition remains one HAC composition.

One local node remains one local node.

The local runtime composition remains unchanged.

Protocol schemas and capability-centered routing remain unchanged.

Authentication and transport security remain separate future architectural
decisions. The concrete bounded ASGI/listener/port representation remains an
implementation choice subject to the exposure invariant.
